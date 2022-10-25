from enum import Enum
class Move(Enum):
  POINT = "Point"
  STOP = "Stop"
  VOLUME_UP = "Volume Up"
  VOLUME_DOWN = "Volume Down"
  VOLUME_UP_INTERVAL = "Volume Up Interval"
  VOLUME_DOWN_INTERVAL = "Volume Down Interval"

class Movement:
  def __init__(self, section = -1, move = Move.POINT, times = 0):
    self.section = section
    self.move = move
    self.times = times
  
  def isSameMove(self, section, move):
    return self.section == section and self.move == move