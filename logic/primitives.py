class Point:
    """Reprezentuje punkt na płaszczyźnie."""
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __lt__(self, other):
        if abs(self.x - other.x) > 1e-9:
            return self.x < other.x
        return self.y < other.y
    
    def __eq__(self, other):
        return abs(self.x - other.x) < 1e-9 and abs(self.y - other.y) < 1e-9

    def to_tuple(self):
        return (self.x, self.y)

class Event:
    """Zdarzenie dla algorytmu zamiatania."""
    LEFT = 0  
    RIGHT = 1 

    def __init__(self, x, point, type, segment_id):
        self.x = x
        self.point = point
        self.type = type
        self.segment_id = segment_id

    def __lt__(self, other):
        if abs(self.x - other.x) > 1e-9:
            return self.x < other.x
        if self.type != other.type:
            return self.type < other.type
        return self.point.y < other.point.y