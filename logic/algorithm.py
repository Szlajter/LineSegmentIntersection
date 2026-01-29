from .primitives import Point, Event
from .math_utils import det, on_segment, get_intersection_math

def run_sweep_line_algorithm(segments):
    """Implementacja algorytmu Bentley-Ottmann (uproszczona)."""
    events = []
    for i, (start, end) in enumerate(segments):
        p1 = Point(start[0], start[1])
        p2 = Point(end[0], end[1])
        if p1.x > p2.x: p1, p2 = p2, p1
        events.append(Event(p1.x, p1, Event.LEFT, i))
        events.append(Event(p2.x, p2, Event.RIGHT, i))
    events.sort()

    active_segments = []
    for event in events:
        seg_idx = event.segment_id
        if event.type == Event.LEFT:
            active_segments.append(seg_idx)
            for other_idx in active_segments:
                if other_idx == seg_idx: continue
                s1 = segments[seg_idx]
                s2 = segments[other_idx]
                pt = get_intersection_math(s1[0], s1[1], s2[0], s2[1])
                if pt:
                    if (on_segment(pt, s1[0], s1[1]) and on_segment(pt, s2[0], s2[1])):
                        return "POINT", pt
        elif event.type == Event.RIGHT:
            if seg_idx in active_segments:
                active_segments.remove(seg_idx)
    return "NONE", None

def find_intersection(P1, P2, P3, P4, infinite=False):
    """Główna funkcja wyznaczająca przecięcie."""
    # Pre-check równoległości
    vec1 = (P2[0]-P1[0], P2[1]-P1[1])
    vec2 = (P4[0]-P3[0], P4[1]-P3[1])
    cross_prod = vec1[0]*vec2[1] - vec1[1]*vec2[0]

    if abs(cross_prod) < 1e-9:
        if infinite: return "NONE", None
        d1 = det(P3, P4, P1)
        if abs(d1) < 1e-9:
            overlap = []
            if on_segment(P1, P3, P4): overlap.append(P1)
            if on_segment(P2, P3, P4): overlap.append(P2)
            if on_segment(P3, P1, P2): overlap.append(P3)
            if on_segment(P4, P1, P2): overlap.append(P4)
            overlap = sorted(list(set(overlap)))
            if len(overlap) >= 2: return "SEGMENT", (overlap[0], overlap[-1])
            elif len(overlap) == 1: return "POINT", overlap[0]
        return "NONE", None

    if infinite:
        pt = get_intersection_math(P1, P2, P3, P4)
        if pt: return "POINT", pt
        return "NONE", None

    return run_sweep_line_algorithm([ (P1, P2), (P3, P4) ])