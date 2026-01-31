import heapq
import bisect
from .primitives import Point, Segment, Event
from .math_utils import det, on_segment, get_intersection_math, y_at_x

# --- STRUKTURA STATUSU (SWEEP LINE STATUS) ---

class SweepLineStatus:  
    """
    Reprezentuje stan miotły (linii zamiatającej).
    Przechowuje aktywne odcinki posortowane według współrzędnej Y
    w aktualnym punkcie X miotły.
    
    W podręcznikowej wersji jest to Zbalansowane Drzewo BST.
    W Pythonie symulujemy to listą posortowaną + bisect (dla prostoty implementacji).
    """
    def __init__(self):
        self.active_segments = [] 
        self.current_x = 0 

    def _key(self, seg):
        """Klucz sortowania: Y odcinka w aktualnym X."""
        return y_at_x(seg, self.current_x)

    def insert(self, segment, x):
        """Wstawia odcinek zachowując porządek Y."""
        self.current_x = x
        keys = [self._key(s) for s in self.active_segments]
        idx = bisect.bisect_right(keys, self._key(segment))
        self.active_segments.insert(idx, segment)
        return idx

    def remove(self, segment, x):
        """Usuwa odcinek ze struktury."""
        self.current_x = x
        for i, s in enumerate(self.active_segments):
            if s.id == segment.id:
                self.active_segments.pop(i)
                return i
        return -1

    def swap_segments(self, s1, s2):
        """
        Zamienia miejscami dwa sąsiednie odcinki w strukturze statusu.
        Jest to kluczowe dla algorytmu Bentley-Ottmanna:
        Po przecięciu, odcinek który był "wyżej", teraz jest "niżej" (i vice versa).
        """
        try:
            i1 = self.active_segments.index(s1)
            i2 = self.active_segments.index(s2)
            # Zamiana w liście
            self.active_segments[i1], self.active_segments[i2] = self.active_segments[i2], self.active_segments[i1]
        except ValueError:
            pass # Odcinki mogły zostać usunięte w międzyczasie

    def get_neighbors_by_segment(self, segment):
        """Znajduje sąsiadów dla podanego obiektu odcinka."""
        try:
            idx = self.active_segments.index(segment)
            return self.get_neighbors_at_index(idx)
        except ValueError:
            return None, None

    def get_neighbors_at_index(self, idx):
        """Zwraca sąsiada powyżej i poniżej podanego indeksu."""
        prev_seg = self.active_segments[idx - 1] if idx > 0 else None
        next_seg = self.active_segments[idx + 1] if idx < len(self.active_segments) - 1 else None
        return prev_seg, next_seg

# --- LOGIKA BENTLEY-OTTMANNA ---

def check_future_intersection(s1, s2, current_x):
    """
    Sprawdza, czy dwa odcinki (s1, s2) przetną się w PRZYSZŁOŚCI (x > current_x).
    Algorytm zamiatania interesuje się tylko tym, co jest przed miotłą.
    """
    p1, p2 = s1.start.to_tuple(), s1.end.to_tuple()
    p3, p4 = s2.start.to_tuple(), s2.end.to_tuple()
    
    pt = get_intersection_math(p1, p2, p3, p4)
    
    if pt:
        # Sprawdź czy punkt leży fizycznie na odcinkach
        if on_segment(pt, p1, p2) and on_segment(pt, p3, p4):
            # Akceptujemy tylko zdarzenia na prawo od miotły (z małym marginesem błędu)
            if pt[0] >= current_x - 1e-9:
                return Point(pt[0], pt[1])
    return None

def run_sweep_line_algorithm(raw_segments):
    """
    Pełna implementacja algorytmu Bentley-Ottmanna dla N odcinków.
    Zwraca listę wszystkich znalezionych punktów przecięcia.
    """
    event_queue = []
    status = SweepLineStatus()
    found_intersections = set() # Zapobiega duplikatom
    found_points_list = []      # Wynikowa lista punktów
    
    # 1. INICJALIZACJA
    # Dodaj punkty początkowe i końcowe wszystkich odcinków do kolejki
    for i, (start, end) in enumerate(raw_segments):
        s = Segment(Point(*start), Point(*end), i)
        heapq.heappush(event_queue, Event(s.start.x, s.start, Event.START, [s]))
        heapq.heappush(event_queue, Event(s.end.x, s.end, Event.END, [s]))

    # 2. PĘTLA GŁÓWNA (SWEEP)
    while event_queue:
        event = heapq.heappop(event_queue)
        sweep_x = event.x
        
        # --- ZDARZENIE: START (Początek odcinka) ---
        if event.type == Event.START:
            segment = event.segments[0]
            
            # Wstaw do statusu i pobierz pozycję
            idx = status.insert(segment, sweep_x)
            
            # Sprawdź przecięcia z nowymi sąsiadami (góra/dół)
            pred, succ = status.get_neighbors_at_index(idx)
            
            if pred:
                pt = check_future_intersection(segment, pred, sweep_x)
                if pt and pt.to_tuple() not in found_intersections:
                    found_intersections.add(pt.to_tuple())
                    # Dodaj zdarzenie przecięcia do kolejki!
                    # Przecięcie dotyczy tych dwóch konkretnych segmentów
                    heapq.heappush(event_queue, Event(pt.x, pt, Event.INTERSECTION, [segment, pred]))
            
            if succ:
                pt = check_future_intersection(segment, succ, sweep_x)
                if pt and pt.to_tuple() not in found_intersections:
                    found_intersections.add(pt.to_tuple())
                    heapq.heappush(event_queue, Event(pt.x, pt, Event.INTERSECTION, [segment, succ]))

        # --- ZDARZENIE: END (Koniec odcinka) ---
        elif event.type == Event.END:
            segment = event.segments[0]
            
            # Pobierz sąsiadów zanim usuniemy odcinek
            idx = status.remove(segment, sweep_x)
            
            # Po usunięciu, dawni sąsiedzi (góra i dół) stają się bezpośrednimi sąsiadami.
            # Musimy sprawdzić, czy ONI się nie przetną w przyszłości.
            if idx != -1:
                # Uwaga na indeksy: po remove, element [idx] to dawny następnik, a [idx-1] to dawny poprzednik
                pred, succ = status.get_neighbors_at_index(idx)
                
                if pred and succ:
                    pt = check_future_intersection(pred, succ, sweep_x)
                    if pt and pt.to_tuple() not in found_intersections:
                        found_intersections.add(pt.to_tuple())
                        heapq.heappush(event_queue, Event(pt.x, pt, Event.INTERSECTION, [pred, succ]))

        # --- ZDARZENIE: INTERSECTION (Przecięcie dwóch odcinków) ---
        elif event.type == Event.INTERSECTION:
            # To jest serce pełnego algorytmu Bentley-Ottmanna.
            # Zapisujemy znaleziony punkt
            found_points_list.append(event.point.to_tuple())
            
            # Pobieramy dwa odcinki, które się przecięły
            s1 = event.segments[0]
            s2 = event.segments[1]
            
            # Zamieniamy je miejscami w strukturze statusu.
            # Ponieważ się przecięły, ich relacja góra/dół się odwraca.
            status.swap_segments(s1, s2)
            
            # Po zamianie s1 i s2 mają nowych sąsiadów z "zewnątrz".
            # Trzeba sprawdzić nowe potencjalne przecięcia:
            # - Górny zamieniony vs Jego górny sąsiad
            # - Dolny zamieniony vs Jego dolny sąsiad
            
            for seg in [s1, s2]:
                pred, succ = status.get_neighbors_by_segment(seg)
                if pred:
                    pt = check_future_intersection(seg, pred, sweep_x)
                    if pt and pt.to_tuple() not in found_intersections:
                        found_intersections.add(pt.to_tuple())
                        heapq.heappush(event_queue, Event(pt.x, pt, Event.INTERSECTION, [seg, pred]))
                if succ:
                    pt = check_future_intersection(seg, succ, sweep_x)
                    if pt and pt.to_tuple() not in found_intersections:
                        found_intersections.add(pt.to_tuple())
                        heapq.heappush(event_queue, Event(pt.x, pt, Event.INTERSECTION, [seg, succ]))

    return found_points_list

# --- FASADA (WRAPPER) ---

def find_intersection(P1, P2, P3, P4, infinite=False):
    """
    Wrapper dostosowujący ogólny algorytm (dla N odcinków) 
    do interfejsu GUI (oczekującego wyniku dla 2 odcinków).
    """
    
    # 1. Obsługa przypadków zdegenerowanych (Równoległość/Overlap)
    vec1 = (P2[0]-P1[0], P2[1]-P1[1])
    vec2 = (P4[0]-P3[0], P4[1]-P3[1])
    cross_prod = vec1[0]*vec2[1] - vec1[1]*vec2[0]

    if abs(cross_prod) < 1e-9:  
        if infinite: return "NONE", None
        
        # Sprawdzamy współliniowość
        d1 = det(P3, P4, P1)
        if abs(d1) < 1e-9:
            # Overlap logic
            overlap = []
            if on_segment(P1, P3, P4): overlap.append(P1)
            if on_segment(P2, P3, P4): overlap.append(P2)
            if on_segment(P3, P1, P2): overlap.append(P3)
            if on_segment(P4, P1, P2): overlap.append(P4)
            overlap = sorted(list(set(overlap)))
            if len(overlap) >= 2:
                return "SEGMENT", (overlap[0], overlap[-1])
            elif len(overlap) == 1:
                return "POINT", overlap[0]
        return "NONE", None

    # 2. Tryb Nieskończony
    if infinite:
        pt = get_intersection_math(P1, P2, P3, P4)
        if pt: return "POINT", pt
        return "NONE", None

    # 3. Uruchomienie Bentley-Ottmanna
    results = run_sweep_line_algorithm([ (P1, P2), (P3, P4) ])
    
    if results:
        # GUI obsługuje na razie wyświetlanie jednego punktu, zwracamy pierwszy znaleziony
        return "POINT", results[0]
    
    return "NONE", None