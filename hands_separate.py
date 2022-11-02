# this IP 
# top right: (0,0)
# bottom left: (1, 1)

# state machine states:

# two hands/gesture recognition
# playing after socket done

# TODO:
# slow down volume change
# big gesture


# TODO
from cgitb import handler
from urllib import robotparser


# faster and louder different features
# one hand doing raise after selecting 
# not play string, move robots with hand (on two robots)
# drum robot
# big gestures
# sound goes to left and right (or arm) following arm
# one hand controls sound one hand controls arms 
# change speed on all of them not just one 
# change pattern/rhythm not the speed
# fingers 1, 2, 3
# multi user
# 



from curses.ascii import isascii
from enum import Enum
import cv2
import mediapipe as mp
import time
from pythonosc import udp_client
from handGestureRecognition import detectGesture
from movements import Move, Movement

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


def drawGuidelines(image, thickness):
    image_rows, image_cols, _ = image.shape
    ON_THICKNESS = 10
    OFF_THICKNESS = 2
    # from L -> R bottom row
    for i in range(2):
        # middle
        cv2.line(image, (image_cols//2*(2-i), image_rows//2), (image_cols//2*(2-i-1),
                image_rows//2), (0, 0, 0), ON_THICKNESS if thickness[i] else OFF_THICKNESS)
        # left
        cv2.line(image, (image_cols//2*(2-i), image_rows//2), (image_cols//2 *
                (2-i), image_rows), (0, 0, 0), ON_THICKNESS if thickness[i] else OFF_THICKNESS)
        # right
        cv2.line(image, (image_cols//2*(2-i-1), image_rows//2), (image_cols//2 *
                (2-i-1), image_rows), (0, 0, 0), ON_THICKNESS if thickness[i] else OFF_THICKNESS)
    # from left to right top row
    for i in range(3):
        # middle
        cv2.line(image, (image_cols//3*(3-i), image_rows//2), (image_cols//3*(3-i-1),
                image_rows//2), (0, 0, 0), ON_THICKNESS if thickness[i+2] else OFF_THICKNESS)
        # left
        cv2.line(image, (image_cols//3*(3-i), image_rows//2), (image_cols//3 *
                (3-i), 0), (0, 0, 0), ON_THICKNESS if thickness[i+2] else OFF_THICKNESS)
        # right
        cv2.line(image, (image_cols//3*(3-i-1), image_rows//2), (image_cols//3 *
                (3-i-1), 0), (0, 0, 0), ON_THICKNESS if thickness[i+2] else OFF_THICKNESS)

def writeVolume(image, volumes, onBoxes):
  image_rows, image_cols, _ = image.shape

  # top row
  for i, vol in enumerate(volumes[:2]):
    if onBoxes[i]:
      org = ((image_cols//2*i+(image_cols//2*(i+1)))//2, image_rows-20)
      font = cv2.FONT_HERSHEY_SIMPLEX
      fontScale = 1
      color = (256, 0, 0)
      thickness = 2
      image = cv2.putText(image, str(vol), org, font, 
                      fontScale, color, thickness, cv2.LINE_AA)
  # top row
  for i, vol in enumerate(volumes[2:]):
    if onBoxes[i+2]:
      org = ((image_cols//3*i+(image_cols//3*(i+1)))//2, image_rows//2-20)
      font = cv2.FONT_HERSHEY_SIMPLEX
      fontScale = 1
      color = (256, 0, 0)
      thickness = 2
      image = cv2.putText(image, str(vol), org, font, 
                      fontScale, color, thickness, cv2.LINE_AA)

def findPointerSection(image, hand_landmarks):
    pointerX = hand_landmarks.landmark[8].x
    pointerY = hand_landmarks.landmark[8].y
    handPos = tuple([int(pointerX*image_cols), int(pointerY*image_rows)])
    cv2.circle(image, handPos, radius=10, color=(0, 0, 0), thickness=10)

    if pointerY > (1/2):
        # robot 0 or 1
        if pointerX > 1/2:
            section = 0
        else:
            section = 1

    else:
        # robot 2, 3, or 4
        section = int(abs(pointerX//(1/3)-2))+2
    
    return section

def findPalmCenterSection(image, hand_landmarks):
    palmSumX = 0
    palmSumY = 0
    palmConnections = (0, 1, 5, 9, 13, 17)
    for i in palmConnections:
        palmSumX += hand_landmarks.landmark[i].x
        palmSumY += hand_landmarks.landmark[i].y
    palmAvgX = palmSumX/6
    palmAvgY = palmSumY/6
    handPos = tuple([int(palmAvgX*image_cols), int(palmAvgY*image_rows)])
    cv2.circle(image, handPos, radius=5, color=(0, 0, 0), thickness=10)
    if palmAvgY > (2/3):
        # neutral bottom section
        return 5
    else:
        section = int(abs(palmAvgX//(1/5)-4))
        return section

def detectStopGesture(hand_landmarks):

    thumbDown = hand_landmarks.landmark[4].x >= hand_landmarks.landmark[5].x
    if thumbDown:
        return False

    secondFinger = [8, 7, 6, 5]
    thirdFinger = [12, 11, 10, 9]
    fourthFinger = [16, 15, 14, 13]
    pinkie = [20, 19, 18, 17]

    fingerJoints = [
        secondFinger,
        thirdFinger,
        fourthFinger,
        pinkie
    ]

    for finger in fingerJoints:
        for i in range(len(finger)-1):
            jointNum = finger[i]
            nextJointNum = finger[i+1]
            if hand_landmarks.landmark[jointNum].y >= hand_landmarks.landmark[nextJointNum].y:
                return False
    return True


with mp_hands.Hands(
        model_complexity=0,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5) as hands:

    MOVEMENT_CHANGE_MARGIN = 4
    VOLUME_CHANGE_SPEED = 10
    DEFAULT_VOLUME = 50
    VOLUME_INTERVAL_CHANGE = 10
    # which sections are on
    onBoxes = [False]*6
    # volume of each section
    volumes = [DEFAULT_VOLUME]*5

    lastRegisteredMovement = Movement()
    lastMovement = Movement()

    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("Ignoring empty camera frame.")
            # If loading a video, use 'break' instead of 'continue'.
            continue

        # To improve performance, optionally mark the image as not writeable to
        # pass by reference.
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
            for i, hand_landmarks in enumerate(results.multi_hand_landmarks):
                image_rows, image_cols, _ = image.shape

                mp_drawing.draw_landmarks(
                    image,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing_styles.get_default_hand_landmarks_style(),
                    mp_drawing_styles.get_default_hand_connections_style())
                # draw hands
                # NOTE: Right is actually left hand

                if results.multi_handedness[i].classification[0].label == "Right":

                    newMove = detectGesture(hand_landmarks)
                    if newMove:
                      move = newMove

                # "Left" hand (right hand) does the pointing
                else:
                    # section = findPalmCenterSection(image, hand_landmarks)
                    section = findPointerSection(image, hand_landmarks)

                # draw guideboxes
                drawGuidelines(image, onBoxes)

            # print((section, move))
            if section != -1:
                # is same registered movement
                if lastRegisteredMovement.isSameMove(section, move):
                  lastRegisteredMovement.times += 1
                  match move:
                    case Move.VOLUME_UP:
                      if onBoxes[section] and section < 5:
                        volumes[section] = min(100, volumes[section] + 1)
                        print((section, volumes[section]))
                        client.send_message("/" + str(section), (onBoxes[section], volumes[section]))
                    case Move.VOLUME_DOWN:
                      if onBoxes[section] and section < 5:
                        volumes[section] = max(0, volumes[section] - 1)
                        print((section, volumes[section]))
                        client.send_message("/" + str(section), (onBoxes[section], volumes[section]))

                # is same as last movement (not registered)
                elif lastMovement.isSameMove(section, move):
                    lastMovement.times += 1
                    if lastMovement.times >= MOVEMENT_CHANGE_MARGIN:
                        lastRegisteredMovement.section = section
                        lastRegisteredMovement.move = move
                        lastRegisteredMovement.times = lastMovement.times
                        match move:
                          case Move.POINT:
                            print("start "+str(section))
                            onBoxes[section] = True
                            if section < 5:
                                client.send_message("/" + str(section), (onBoxes[section], volumes[section]))
                          case Move.STOP:
                            print("stop "+str(section))
                            onBoxes[section] = False
                            if section < 5:
                                client.send_message("/" + str(section), (onBoxes[section], volumes[section]))
                            
                          case Move.VOLUME_UP:
                            if onBoxes[section] and section < 5:
                                volumes[section] += 1
                                print((section, volumes[section]))
                                client.send_message("/" + str(section), (onBoxes[section], volumes[section]))
                          case Move.VOLUME_DOWN:
                            if onBoxes[section] and section < 5:
                                volumes[section] -= 1
                                print((section, volumes[section]))
                                client.send_message("/" + str(section), (onBoxes[section], volumes[section]))
                          case Move.VOLUME_UP_INTERVAL:
                            if onBoxes[section] and section < 5:
                                volumes[section] = min(100, volumes[section] + VOLUME_INTERVAL_CHANGE)
                                print((section, volumes[section]))
                                client.send_message("/" + str(section), (onBoxes[section], volumes[section]))
                          case Move.VOLUME_DOWN_INTERVAL:
                            if onBoxes[section] and section < 5:
                                volumes[section] = max(0, volumes[section] - VOLUME_INTERVAL_CHANGE)
                                print((section, volumes[section]))
                                client.send_message("/" + str(section), (onBoxes[section], volumes[section]))

                # is completely new movement
                else:
                    lastMovement.section = section
                    lastMovement.move = move
                    lastMovement.times = 1

        flipped = cv2.flip(image, 1)
        writeVolume(flipped, volumes, onBoxes)

        cv2.imshow('MediaPipe Hands', flipped)
        if cv2.waitKey(5) & 0xFF == 27:
            break
cap.release()
