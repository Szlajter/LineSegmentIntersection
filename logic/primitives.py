# logic/primitives.py

class Point:
    """Reprezentuje punkt na płaszczyźnie (x, y)."""
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"({self.x:.2f}, {self.y:.2f})"
    
    def __eq__(self, other):
        return abs(self.x - other.x) < 1e-9 and abs(self.y - other.y) < 1e-9

    def __lt__(self, other):
        if abs(self.x - other.x) > 1e-9:
            return self.x < other.x
        return self.y < other.y

    def to_tuple(self):
        return (self.x, self.y)

class Segment:
    """
    Reprezentuje odcinek. 
    Ważne: Punkt 'start' to zawsze ten z mniejszym X.
    Dzięki temu algorytm zamiatania zawsze "wchodzi" w odcinek od lewej strony.
    """
    def __init__(self, p1, p2, segment_id):
        if p1 < p2:
            self.start = p1
            self.end = p2
        else:
            self.start = p2
            self.end = p1
        self.id = segment_id

    def __repr__(self):
        return f"S{self.id}"
    
    def __eq__(self, other):
        return self.id == other.id

class Event:
    """
    Zdarzenie w kolejce priorytetowej algorytmu.
    """
    INTERSECTION = 0  # Przecięcie (najwyższy priorytet przy tym samym X)
    END = 1           # Koniec odcinka
    START = 2         # Początek odcinka

    def __init__(self, x, point, type, segments):
        self.x = x
        self.point = point
        self.type = type
        # Lista segmentów, których dotyczy zdarzenie.
        # Dla START/END to jeden segment. Dla INTERSECTION to dwa przecinające się segmenty.
        self.segments = segments 

    def __lt__(self, other):
        """
        Kolejność przetwarzania zdarzeń:
        1. X: Mniejsze X wcześniej (miotła idzie w prawo).
        2. Typ: Przy tym samym X:
           - Najpierw obsługujemy PRZECIĘCIA (aby zamienić kolejność odcinków).
           - Potem KOŃCE (aby usunąć stare).
           - Na końcu POCZĄTKI (aby dodać nowe).
        3. Y: Od dołu do góry.
        """
        if abs(self.x - other.x) > 1e-9:
            return self.x < other.x
        
        if self.type != other.type:
            return self.type < other.type
        
        return self.point.y < other.point.y