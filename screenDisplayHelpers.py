import cv2

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

def writeSpeed(image, speeds, onBoxes):
  image_rows, image_cols, _ = image.shape

  # top row
  for i, vol in enumerate(speeds[:2]):
    if onBoxes[i]:
      org = ((image_cols//2*i+(image_cols//2*(i+1)))//2, image_rows-20)
      font = cv2.FONT_HERSHEY_SIMPLEX
      fontScale = 1
      color = (255, 255, 255)
      thickness = 2
      image = cv2.putText(image, str(vol), org, font, 
                      fontScale, color, thickness, cv2.LINE_AA)
  # top row
  for i, vol in enumerate(speeds[2:]):
    if onBoxes[i+2]:
      org = ((image_cols//3*i+(image_cols//3*(i+1)))//2, image_rows//2-20)
      font = cv2.FONT_HERSHEY_SIMPLEX
      fontScale = 1
      color = (255, 255, 255)
      thickness = 2
      image = cv2.putText(image, str(vol), org, font, 
                      fontScale, color, thickness, cv2.LINE_AA)