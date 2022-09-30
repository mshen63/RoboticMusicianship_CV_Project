# top right: (0,0)
# bottom left: (1, 1)

import cv2
import mediapipe as mp
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_hands = mp.solutions.hands
cap = cv2.VideoCapture(0)

def drawGuidelines(image, thickness):
  image_rows, image_cols, _ = image.shape
  ON_THICKNESS = 10
  OFF_THICKNESS = 2
  ### from left to right
  for i in range(5):
    # middle
    cv2.line(image, (image_cols//5*(5-i), image_rows//3*2), (image_cols//5*(5-i-1), image_rows//3*2), (0, 0, 0), ON_THICKNESS if thickness[i] else OFF_THICKNESS)
    # left
    cv2.line(image, (image_cols//5*(5-i), image_rows//3*2), (image_cols//5*(5-i), 0), (0, 0, 0), ON_THICKNESS if thickness[i] else OFF_THICKNESS)  
    # right
    cv2.line(image, (image_cols//5*(5-i-1), image_rows//3*2), (image_cols//5*(5-i-1), 0), (0, 0, 0), ON_THICKNESS if thickness[i] else OFF_THICKNESS)

def findPointerSection(image, hand_landmarks):
  pointerX = hand_landmarks.landmark[8].x
  pointerY = hand_landmarks.landmark[8].y
  handPos = tuple([int(pointerX*image_cols), int(pointerY*image_rows)])
  cv2.circle(image, handPos, radius=10, color=(0, 0, 0), thickness=10)

  if pointerY > (2/3):
    # neutral bottom section
    return 5
  else:
    section = int(abs(pointerX//(1/5)-4))
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

with mp_hands.Hands(
    model_complexity=0,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5) as hands:
  
  # which sections are on
  onBoxes = [False]*6
  # which section was last visited
  handLast = -1

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
      for i, hand_landmarks in enumerate(results.multi_hand_landmarks):

        image_rows, image_cols, _ = image.shape
        section = findPalmCenterSection(image, hand_landmarks)
        # section = findPointerSection(image, hand_landmarks)

        if len(onBoxes)>section and section!=handLast:
          onBoxes[section] = (not onBoxes[section])
          # TODO: send call to turn on or off playing 
          if section!=4:
            print(section)
          handLast = section

        # draw hands
        mp_drawing.draw_landmarks(
            image,
            hand_landmarks,
            mp_hands.HAND_CONNECTIONS,
            mp_drawing_styles.get_default_hand_landmarks_style(),
            mp_drawing_styles.get_default_hand_connections_style())
        # draw guideboxes
        drawGuidelines(image, onBoxes)

    cv2.imshow('MediaPipe Hands', cv2.flip(image, 1))
    if cv2.waitKey(5) & 0xFF == 27:
      break
cap.release()
