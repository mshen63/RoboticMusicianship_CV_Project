import time
import cv2
import mediapipe as mp
from pythonosc import udp_client
from handGestureRecognition import *
from movements import Move, Movement
from screenDisplayHelpers import *

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_hands = mp.solutions.hands
# when webcam attached, 0 is webcam and 1 is computer camera
cap = cv2.VideoCapture(0)

PORT_TO_MAX = 5002
# should point to IP from MAX's ethernet port
# put ur own IP to something different but on same network (ie: "192.168.2.3")
# on server, IP should be 0.0.0.0
IP = "192.168.2.2"

global client
client = udp_client.SimpleUDPClient(IP, PORT_TO_MAX)


with mp_hands.Hands(
        model_complexity=0,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5) as hands:

    # how many detections before a pose is recognized
    MOVEMENT_CHANGE_MARGIN = 2
    DEFAULT_SPEED = 50
    NUM_ARMS = 5
    # how much speed changes by on a gesture
    SPEED_INTERVAL_CHANGE = 10
    # flag for speed being controlled together or separately
    PLAY_ALL_TOGETHER = True
    # mediapipe based constant: how many joints detected on each hand
    NUM_TOTAL_JOINTS_EACH_HAND = 21
    # distance required to be moved over course of single mediapip detection to be registered as a gesture over a pose
    REQUIRED_GESTURE_SPEED = 0.1

    # which sections are on
    onBoxes = [False] * NUM_ARMS
    # speed of each section
    speeds = [DEFAULT_SPEED] * NUM_ARMS

    # last movement that was registered (using movement change margin)
    lastRegisteredMovement = Movement()
    # last movement (may not be registered)
    lastMovement = Movement()

    # handles speed change commands
    def handleSpeedCommand(section, speedChange):
        global speeds
        global onBoxes
        num_arms_playing = sum(onBoxes)
        # puts speed between 0 and 100
        speed = min(100, speeds[section] + speedChange)
        speed = max(0, speed)
        if not PLAY_ALL_TOGETHER:
            speeds[section] = speed
            time_between_strums = 1-(speeds[section]/100)
            
            time_to_wait = time_between_strums * num_arms_playing
            if section < 5:
                client.send_message("/" + str(section), (onBoxes[section], time_to_wait))
        else:
            speeds = [speed] * NUM_ARMS
            for i, boxOn in enumerate(onBoxes):
                if i<5 and boxOn:
                    time_between_strums = 1-(speeds[i]/100)
                    
                    time_to_wait = time_between_strums * num_arms_playing
                    client.send_message("/" + str(i), (boxOn, time_to_wait))

    # handles commands for starting or stopping an arm
    def handleStartStopCommands(section, isStop):
        global speeds
        global onBoxes

        num_arms_playing = sum(onBoxes)

        # turn all on boxes off to handle timing 
        for i, boxOn in enumerate(onBoxes):
            if i < 5 and ((i!=section and boxOn) or (i==section and isStop)):
                client.send_message("/" + str(i), (False, -1))

        # turn arms on in certain order so they play arpeggiated 
        for i, boxOn in enumerate(onBoxes):
            if i < 5 and boxOn:
                # dependent on speed
                time_between_strums = 1-(speeds[i]/100)
                time_to_wait = time_between_strums * num_arms_playing
                time.sleep(time_between_strums)
                client.send_message("/" + str(i), (True, time_to_wait))
    
        
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("Ignoring empty camera frame.")
            continue

        image.flags.writeable = False
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        drawGuidelines(image, onBoxes)
        results = hands.process(image)

        # Draw the hand annotations on the image.
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        if results.multi_hand_landmarks:
            # defaults
            section = -1
            move = Move.POINT
            movePos = (0, 0)

            for i, hand_landmarks in enumerate(results.multi_hand_landmarks):
                image_rows, image_cols, _ = image.shape

                # draws mediapipe detected hand joints
                mp_drawing.draw_landmarks(
                    image,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing_styles.get_default_hand_landmarks_style(),
                    mp_drawing_styles.get_default_hand_connections_style())

                # NOTE: "Right" is actually left hand because camera is flipped
                if results.multi_handedness[i].classification[0].label == "Right":
                    newMove = detectGesture(hand_landmarks)
                    if newMove:
                      move = newMove
                    moveX = 0
                    moveY = 0
                    for lm in hand_landmarks.landmark:
                        moveX += lm.x
                        moveY += lm.y
                    # average center point of hand
                    movePos = (moveX / NUM_TOTAL_JOINTS_EACH_HAND, moveY / NUM_TOTAL_JOINTS_EACH_HAND)


                # "Left" hand (right hand) does the pointing
                else:
                    ## can decide between using palm center or point finger for point detection
                    # section = findPalmCenterSection(image, hand_landmarks)
                    section = findPointerSection(image, hand_landmarks)

                # draw guideboxes
                drawGuidelines(image, onBoxes)

            if section != -1:

                # is same registered movement and movement not done yet (or is continuous)
                if lastRegisteredMovement.isSameMove(section, move) and not lastRegisteredMovement.movementDone:
                    match move:
                        case Move.SPEED_UP:
                            lastRegisteredMovement.times += 1
                            if onBoxes[section] and section < 5:
                                handleSpeedCommand(section, 1)
                        case Move.SPEED_DOWN:
                            lastRegisteredMovement.times += 1
                            if onBoxes[section] and section < 5:
                                handleSpeedCommand(section, -1)

                    lastRegisteredMovement.X = movePos[0]
                    lastRegisteredMovement.Y = movePos[1]


                # is same as last movement (but not registered)
                elif lastMovement.isSameMove(section, move):
                    
                    match move:
                        # for gestures (not poses), check if the speed is enough to keep registering it as a gesture
                        case [Move.PALM_UP, Move.PALM_DOWN]:

                            changeX, changeY = lastMovement.calculatePositionChange(movePos)
                            # hyperparameter REQUIRED_GESTURE_SPEED needs to be adjusted based on camera location
                            if abs(changeY) > REQUIRED_GESTURE_SPEED:
                                lastMovement.times += 1

                        case _:
                            lastMovement.times += 1

                    lastMovement.X = movePos[0]
                    lastMovement.Y = movePos[1]

                    # register the movement as not just a random swipe, but a gesture/pose intended by the user
                    if lastMovement.times >= MOVEMENT_CHANGE_MARGIN:
                        lastRegisteredMovement.section = section
                        lastRegisteredMovement.move = move
                        lastRegisteredMovement.times = lastMovement.times
                        lastRegisteredMovement.X = lastMovement.X
                        lastRegisteredMovement.Y = lastMovement.Y
                        match move:
                            case Move.POINT:  
                                if not onBoxes[section]:
                                    onBoxes[section] = True
                                    handleStartStopCommands(section, isStop=False)
                            case Move.STOP:
                                if onBoxes[section]:
                                    onBoxes[section] = False
                                    handleStartStopCommands(section, isStop=True)

                            case Move.PALM_UP:
                                handleSpeedCommand(section, SPEED_INTERVAL_CHANGE)
                                lastMovement.movementDone = True
                                    
                            case Move.PALM_DOWN:

                                handleSpeedCommand(section, -SPEED_INTERVAL_CHANGE)
                                lastMovement.movementDone = True

                            case Move.SPEED_UP_INTERVAL:
                                if onBoxes[section] and section < 5:
                                    handleSpeedCommand(section, SPEED_INTERVAL_CHANGE)

                            case Move.SPEED_DOWN_INTERVAL:
                                if onBoxes[section] and section < 5:
                                    handleSpeedCommand(section, -SPEED_INTERVAL_CHANGE)

                        lastMovement.movementDone = True

                # is completely new movement
                else:

                    lastMovement.section = section
                    lastMovement.move = move
                    lastMovement.times = 1
                    if movePos:
                        lastMovement.X = movePos[0]
                        lastMovement.Y = movePos[1]
                    

        # looks a lot trippier when it's not flipped
        flipped = cv2.flip(image, 1)
        # draws the speed labels
        writeSpeed(flipped, speeds, onBoxes)

        cv2.imshow('MediaPipe Hands', flipped)
        if cv2.waitKey(5) & 0xFF == 27:
            break
cap.release()
