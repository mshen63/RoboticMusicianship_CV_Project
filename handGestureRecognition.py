from movements import Move
thumbJoints = [4, 3, 2]
secondFinger = [8, 7, 6, 5]
thirdFinger = [12, 11, 10, 9]
fourthFinger = [16, 15, 14, 13]
pinkie = [20, 19, 18, 17]

# all straight fingers
allStraightFingers = [secondFinger, thirdFinger, fourthFinger, pinkie]
allFingers = [thumbJoints, secondFinger, thirdFinger, fourthFinger, pinkie]


def detectGesture(hand_landmarks):
    fingersPointingUp = [True]*4
    fingersPointingDown = [True]*4
    thumbDown = hand_landmarks.landmark[4].x >= hand_landmarks.landmark[5].x

    # turns all down fingers into True in fingerState, only completely up fingers are False
    for fingerNum, finger in enumerate(allStraightFingers):
        for i in range(len(finger)-1):
            jointNum = finger[i]
            nextJointNum = finger[i+1]
            if hand_landmarks.landmark[jointNum].y >= hand_landmarks.landmark[nextJointNum].y:
                fingersPointingUp[fingerNum] = False

    for fingerNum, finger in enumerate(allStraightFingers):
        for i in range(len(finger)-1):
            jointNum = finger[i]
            nextJointNum = finger[i+1]
            if hand_landmarks.landmark[jointNum].y <= hand_landmarks.landmark[nextJointNum].y:
                fingersPointingDown[fingerNum] = False

    if fingersPointingUp[0] and all([fingersPointingUp[i] == False for i in range(1, 4)]):
        return Move.VOLUME_UP
    elif fingersPointingUp[0] and fingersPointingUp[1] and all([fingersPointingUp[i] == False for i in range(2, 4)]):
        return Move.VOLUME_UP_INTERVAL
    elif fingersPointingDown[0] and all([fingersPointingDown[i] == False for i in range(1, 4)]):
        return Move.VOLUME_DOWN
    elif fingersPointingDown[0] and fingersPointingDown[1] and all([fingersPointingDown[i] == False for i in range(2, 4)]):
        return Move.VOLUME_DOWN_INTERVAL
    elif all(fingersPointingUp) and not thumbDown:
        return Move.STOP
