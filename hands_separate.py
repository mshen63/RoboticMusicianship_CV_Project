# TODO
from cgitb import handler
from urllib import robotparser

# TODO:
# universal speed, 5 combos of rhythmns for # arms on 
# make it more sensitive 

import cv2
import mediapipe as mp
from pythonosc import udp_client
from handGestureRecognition import *
from movements import Move, Movement
from screenDisplayHelpers import *

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_hands = mp.solutions.hands
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

    MOVEMENT_CHANGE_MARGIN = 2
    VOLUME_CHANGE_SPEED = 10
    DEFAULT_VOLUME = 50
    NUM_ARMS = 6
    VOLUME_INTERVAL_CHANGE = 10
    # flag for volume being controlled together or separately
    VOLUME_ALL_TOGETHER = True
    NUM_TOTAL_JOINTS_EACH_HAND = 21
    # 75% of screen between two detections
    REQUIRED_SPEED_GESTURE_RECOGNITION = .75
    # which sections are on
    onBoxes = [False]*6
    # volume of each section
    volumes = [DEFAULT_VOLUME]*5

    lastRegisteredMovement = Movement()
    lastMovement = Movement()

    def sendCommand(section, volumeChange):
        global volumes
        global onBoxes
        volume = min(100, volumes[section]+volumeChange)
        volume = max(0, volume)
        if not VOLUME_ALL_TOGETHER:
            volumes[section] = volume
            if section < 5:
                client.send_message("/" + str(section), (onBoxes[section], volumes[section]))
        else:
            volumes = [volume] * NUM_ARMS
            for i, boxOn in enumerate(onBoxes):
                if i<5 and boxOn:
                    client.send_message("/" + str(i), (boxOn, volumes[i]))

        

    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("Ignoring empty camera frame.")
            # If loading a video, use 'break' instead of 'continue'.
            continue

        image.flags.writeable = False
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        drawGuidelines(image, onBoxes)
        results = hands.process(image)

        # Draw the hand annotations on the image.
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        if results.multi_hand_landmarks:
            section = -1
            move = Move.POINT
            movePos = (0, 0)
            for i, hand_landmarks in enumerate(results.multi_hand_landmarks):
                image_rows, image_cols, _ = image.shape

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
                    movePos = (moveX / NUM_TOTAL_JOINTS_EACH_HAND, moveY / NUM_TOTAL_JOINTS_EACH_HAND)


                # "Left" hand (right hand) does the pointing
                else:
                    # section = findPalmCenterSection(image, hand_landmarks)
                    section = findPointerSection(image, hand_landmarks)

                # draw guideboxes
                drawGuidelines(image, onBoxes)

            if section != -1:

                # is same registered movement and movement not done yet (or is continuous)
                if lastRegisteredMovement.isSameMove(section, move) and not lastRegisteredMovement.movementDone:
                    match move:
                        case Move.VOLUME_UP:
                            lastRegisteredMovement.times += 1
                            if onBoxes[section] and section < 5:
                                sendCommand(section, 1)
                        case Move.VOLUME_DOWN:
                            lastRegisteredMovement.times += 1
                            if onBoxes[section] and section < 5:
                                sendCommand(section, -1)

                    lastRegisteredMovement.X = movePos[0]
                    lastRegisteredMovement.Y = movePos[1]


                # is same as last movement (but not registered)
                elif lastMovement.isSameMove(section, move):
                    # keep checking gestures until registered as done 
                    
                    match move:
                        case [Move.PALM_UP, Move.PALM_DOWN]:

                            changeX, changeY = lastMovement.calculatePositionChange(movePos)
                            if abs(changeY) > 0.1:
                                lastMovement.times += 1

                        case _:
                            lastMovement.times += 1

                    lastMovement.X = movePos[0]
                    lastMovement.Y = movePos[1]

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
                                    if section < 5:
                                        print("sending message to " + str(section))
                                        client.send_message("/" + str(section), (onBoxes[section], volumes[section]))
                            
                            case Move.STOP:
                                if onBoxes[section]:
                                    onBoxes[section] = False
                                    if section < 5:
                                        client.send_message("/" + str(section), (onBoxes[section], volumes[section]))

                            case Move.PALM_UP:
                                sendCommand(section, VOLUME_INTERVAL_CHANGE)
                                lastMovement.movementDone = True
                                    
                            case Move.PALM_DOWN:

                                sendCommand(section, -VOLUME_INTERVAL_CHANGE)
                                lastMovement.movementDone = True

                            case Move.VOLUME_UP_INTERVAL:
                                if onBoxes[section] and section < 5:
                                    sendCommand(section, VOLUME_INTERVAL_CHANGE)

                            case Move.VOLUME_DOWN_INTERVAL:
                                if onBoxes[section] and section < 5:
                                    sendCommand(section, -VOLUME_INTERVAL_CHANGE)

                        lastMovement.movementDone = True

                # is completely new movement
                else:

                    lastMovement.section = section
                    lastMovement.move = move
                    lastMovement.times = 1
                    if movePos:
                        lastMovement.X = movePos[0]
                        lastMovement.Y = movePos[1]
                    

        flipped = cv2.flip(image, 1)
        writeVolume(flipped, volumes, onBoxes)

        cv2.imshow('MediaPipe Hands', flipped)
        if cv2.waitKey(5) & 0xFF == 27:
            break
cap.release()
