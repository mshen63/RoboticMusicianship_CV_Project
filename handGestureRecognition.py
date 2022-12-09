from movements import Move
import numpy as np
import cv2

thumbJoints = [4, 3, 2]
secondFinger = [8, 7, 6, 5]
thirdFinger = [12, 11, 10, 9]
fourthFinger = [16, 15, 14, 13]
pinkie = [20, 19, 18, 17]
palm = [0, 1, 5, 9, 13, 17]

allFingers = [thumbJoints, secondFinger, thirdFinger, fourthFinger, pinkie]
# exclude thumb
allStraightFingers = allFingers[1:]

def detectFlatHand(hand_landmarks):
    palmYLow = 2
    palmYHigh = -1
    for i in palm:
        palmY = hand_landmarks.landmark[i].y
        palmYHigh = max(palmYHigh, palmY)
        palmYLow = min(palmYLow, palmY)
    
    # check which sides thumb/second finger and fourth/fifth singer are on to determine palm up or palm down
    thumbSecond = 0
    fourthFifth = 0
    for lm in hand_landmarks.landmark[1:9]:
        thumbSecond += lm.x
    for lm in hand_landmarks.landmark[13:]:
        fourthFifth += lm.x
    
    thumbSecondAvg =  thumbSecond / 8
    fourthFifthAvg = fourthFifth / 8
    

    isFlatHand = (palmYHigh - palmYLow) < 0.10
    palmUp = thumbSecondAvg > fourthFifthAvg
    return isFlatHand, palmUp

    
        
def detectGesture(hand_landmarks):
    isFlatHand, palmUp = detectFlatHand(hand_landmarks)
    if isFlatHand:
        if palmUp:
            return Move.PALM_UP
        return Move.PALM_DOWN
    fingersPointingUp = [True]*4
    fingersPointingDown = [True]*4
    thumbDown = hand_landmarks.landmark[4].x >= hand_landmarks.landmark[5].x

    # turns all up fingers into True in fingerState, only completely up fingers are False
    for fingerNum, finger in enumerate(allStraightFingers):
        for i in range(len(finger)-1):
            jointNum = finger[i]
            nextJointNum = finger[i+1]
            if hand_landmarks.landmark[jointNum].y >= hand_landmarks.landmark[nextJointNum].y:
                fingersPointingUp[fingerNum] = False

    # turns all down fingers into True in fingerState, only completely up fingers are False
    for fingerNum, finger in enumerate(allStraightFingers):
        for i in range(len(finger)-1):
            jointNum = finger[i]
            nextJointNum = finger[i+1]
            if hand_landmarks.landmark[jointNum].y <= hand_landmarks.landmark[nextJointNum].y:
                fingersPointingDown[fingerNum] = False

    # pointer finger up and rest of fingers down -> speed up (+1 speed)
    if fingersPointingUp[0] and all([fingersPointingUp[i] == False for i in range(1, 4)]):
        return Move.SPEED_UP
    # pointer and third finger up together and rest of fingers down -> speed up at an interval (ie: +10 speed)
    elif fingersPointingUp[0] and fingersPointingUp[1] and all([fingersPointingUp[i] == False for i in range(2, 4)]):
        return Move.SPEED_UP_INTERVAL

    # same as finger up movements but facing downwards
    elif fingersPointingDown[0] and all([fingersPointingDown[i] == False for i in range(1, 4)]):
        return Move.SPEED_DOWN
    elif fingersPointingDown[0] and fingersPointingDown[1] and all([fingersPointingDown[i] == False for i in range(2, 4)]):
        return Move.SPEED_DOWN_INTERVAL
    
    # NOTE: be careful if tilting hand when doing up and down gestures, might lead to detection as STOP
    elif all(fingersPointingUp) and not thumbDown:
        return Move.STOP


# determine corresponding section pointer is pointing to
def findPointerSection(image, hand_landmarks):
    image_rows, image_cols, _ = image.shape
    # [8] is the top joint of the pointer finger
    pointerX = hand_landmarks.landmark[8].x
    pointerY = hand_landmarks.landmark[8].y
    handPos = tuple([int(pointerX*image_cols), int(pointerY*image_rows)])
    # draws a black circle over the point being used for detection
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

# determine section middle of palm corresponds to
def findPalmCenterSection(image, hand_landmarks):
    palmSumX = 0
    palmSumY = 0
    image_rows, image_cols, _ = image.shape
    # finds the middle point of the palm
    for i in palm:
        palmSumX += hand_landmarks.landmark[i].x
        palmSumY += hand_landmarks.landmark[i].y
    palmAvgX = palmSumX/6
    palmAvgY = palmSumY/6
    handPos = tuple([int(palmAvgX*image_cols), int(palmAvgY*image_rows)])
    # draws a black circle over the point being used for detection
    cv2.circle(image, handPos, radius=5, color=(0, 0, 0), thickness=10)
    if palmAvgY > (2/3):
        return 5
    else:
        section = int(abs(palmAvgX//(1/5)-4))
        return section