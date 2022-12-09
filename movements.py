from enum import Enum
class Move(Enum):
  POINT = "Point"
  STOP = "Stop"
  SPEED_UP = "Speed Up"
  SPEED_DOWN = "Speed Down"
  SPEED_UP_INTERVAL = "Speed Up Interval"
  SPEED_DOWN_INTERVAL = "Speed Down Interval"
  PALM_UP = "Palm Up"
  PALM_DOWN = "Palm Down"


class Movement:
  def __init__(self, section = -1, move = Move.POINT, times = 0, x=None, y=None):
    self.section = section
    self.move = move
    self.times = times
    self.movementDone = False
    self.X = x
    self.Y = y
  
  def isSameMove(self, section, move):
    return self.section == section and self.move == move
  
  # moving down -> -
  # moving up -> +
  def calculatePositionChange(self, newPosition):
    return self.X - newPosition[0], self.Y - newPosition[1]
