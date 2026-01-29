import math

def det(a, b, c):
    """Oblicza iloczyn wektorowy."""
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

def on_segment(p, a, b):
    """Sprawdza czy punkt p leży na odcinku ab."""
    return (min(a[0], b[0]) - 1e-9 <= p[0] <= max(a[0], b[0]) + 1e-9 and
            min(a[1], b[1]) - 1e-9 <= p[1] <= max(a[1], b[1]) + 1e-9)

def get_intersection_math(P1, P2, P3, P4):
    """Analityczne wyznaczenie przecięcia prostych."""
    x1, y1 = P1
    x2, y2 = P2
    x3, y3 = P3
    x4, y4 = P4

    denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
    if abs(denom) < 1e-9: return None 

    ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denom
    x = x1 + ua * (x2 - x1)
    y = y1 + ua * (y2 - y1)
    return (x, y)

def get_line_equation(p1, p2):
    """Formatowanie równania prostej."""
    x1, y1 = p1
    x2, y2 = p2
    if abs(x2 - x1) < 1e-9:
        return f"x = {x1:.2f}"
    m = (y2 - y1) / (x2 - x1)
    b = y1 - m * x1
    sign = "+" if b >= 0 else "-"
    return f"y = {m:.2f}x {sign} {abs(b):.2f}"

def distance_point_to_segment(p, a, b):
    """Odległość punktu od odcinka."""
    px, py = p
    x1, y1 = a
    x2, y2 = b
    dx = x2 - x1
    dy = y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(px - x1, py - y1)
    t = ((px - x1) * dx + (py - y1) * dy) / (dx*dx + dy*dy)
    t = max(0, min(1, t))
    closest_x = x1 + t * dx
    closest_y = y1 + t * dy
    return math.hypot(px - closest_x, py - closest_y)