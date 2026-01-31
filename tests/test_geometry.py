import unittest
import sys
import os

# --- KONFIGURACJA ŚCIEŻKI ---
# Dodajemy katalog nadrzędny ('IntersectionApp') do ścieżki systemowej,
# aby testy widziały pakiet 'logic'.
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(parent_dir)

# --- IMPORTY Z MODUŁÓW APLIKACJI ---
from logic.algorithm import find_intersection
from logic.math_utils import on_segment, distance_point_to_segment

class TestGeometryLogic(unittest.TestCase):

    def assertPointEqual(self, p1, p2):
        """
        Pomocnicza funkcja do porównywania punktów z tolerancją float.
        Sprawdza czy krotki (x, y) są wystarczająco blisko siebie.
        """
        if p1 is None or p2 is None:
            self.fail(f"Oczekiwano punktu, otrzymano None (p1={p1}, p2={p2})")
        
        self.assertAlmostEqual(p1[0], p2[0], places=7, msg=f"X się różni: {p1} != {p2}")
        self.assertAlmostEqual(p1[1], p2[1], places=7, msg=f"Y się różni: {p1} != {p2}")

    # --- TESTY GŁÓWNEGO ALGORYTMU (Bentley-Ottmann Wrapper) ---

    def test_intersection_cross(self):
        """Test 1: Klasyczne przecięcie w kształcie X (Symetryczne)."""
        # L1: (-2, -2) -> (2, 2)
        # L2: (-2, 2) -> (2, -2)
        # Oczekiwane: Punkt (0, 0)
        res_type, res_data = find_intersection((-2, -2), (2, 2), (-2, 2), (2, -2))
        
        self.assertEqual(res_type, "POINT")
        self.assertPointEqual(res_data, (0, 0))

    def test_intersection_asymmetric(self):
        """Test 1b: Przecięcie niesymetryczne."""
        # L1: (0, 0) -> (4, 4)
        # L2: (0, 4) -> (2, 0)
        # Równania: y=x oraz y=-2x+4 -> x= -2x+4 -> 3x=4 -> x=4/3, y=4/3
        res_type, res_data = find_intersection((0, 0), (4, 4), (0, 4), (2, 0))
        
        self.assertEqual(res_type, "POINT")
        self.assertPointEqual(res_data, (1.3333333, 1.3333333))

    def test_no_intersection_parallel(self):
        """Test 2: Równoległe odcinki (brak przecięcia)."""
        # Pionowe równoległe: x=0 i x=2
        res_type, res_data = find_intersection((0, 0), (0, 5), (2, 0), (2, 5))
        
        self.assertEqual(res_type, "NONE")
        self.assertIsNone(res_data)

    def test_overlapping_segments(self):
        """Test 3: Odcinki leżące na jednej prostej i nakładające się."""
        # Ten przypadek jest obsługiwany przez Pre-Check w find_intersection (nie przez Sweep Line)
        # L1: (0,0) -> (4,0)
        # L2: (2,0) -> (6,0)
        # Część wspólna: (2,0) -> (4,0)
        res_type, res_data = find_intersection((0, 0), (4, 0), (2, 0), (6, 0))
        
        self.assertEqual(res_type, "SEGMENT")
        # res_data to krotka (start, end)
        self.assertPointEqual(res_data[0], (2, 0))
        self.assertPointEqual(res_data[1], (4, 0))

    def test_infinite_lines(self):
        """Test 5: Tryb 'Infinite' - odcinki się nie stykają, ale proste tak."""
        # L1: (0,0) -> (1,1) (leży na y=x)
        # L2: (0,2) -> (1,2) (leży na y=2)
        # Jako odcinki: BRAK. Jako proste: przecięcie w (2,2)
        
        # A. Tryb domyślny (Finite) -> Bentley-Ottmann
        res_type, _ = find_intersection((0, 0), (1, 1), (0, 2), (1, 2), infinite=False)
        self.assertEqual(res_type, "NONE")

        # B. Tryb nieskończony (Infinite) -> Math Helper
        res_type, res_data = find_intersection((0, 0), (1, 1), (0, 2), (1, 2), infinite=True)
        self.assertEqual(res_type, "POINT")
        self.assertPointEqual(res_data, (2, 2))

    def test_vertical_and_horizontal(self):
        """Test 6: Przecięcie linii pionowej i poziomej."""
        # Testuje czy funkcja y_at_x radzi sobie z pionowymi liniami
        # Pionowa: (2, 0) -> (2, 10)
        # Pozioma: (0, 5) -> (5, 5)
        # Przecięcie: (2, 5)
        res_type, res_data = find_intersection((2, 0), (2, 10), (0, 5), (5, 5))
        
        self.assertEqual(res_type, "POINT")
        self.assertPointEqual(res_data, (2, 5))

    def test_collinear_disjoint(self):
        """Test 7: Współliniowe, ale rozłączne."""
        # L1: (0,0) -> (1,1)
        # L2: (2,2) -> (3,3)
        res_type, res_data = find_intersection((0, 0), (1, 1), (2, 2), (3, 3))
        self.assertEqual(res_type, "NONE")

    # --- TESTY MATH UTILS (Funkcje pomocnicze) ---

    def test_on_segment(self):
        # Punkt środkowy
        self.assertTrue(on_segment((1, 1), (0, 0), (2, 2)))
        # Punkt końcowy
        self.assertTrue(on_segment((0, 0), (0, 0), (2, 2)))
        # Punkt poza odcinkiem (współliniowy)
        self.assertFalse(on_segment((3, 3), (0, 0), (2, 2)))
        # Punkt obok
        self.assertFalse(on_segment((1, 2), (0, 0), (2, 2)))

    def test_distance_point_segment(self):
        # Punkt (0, 1) rzutowany na odcinek na osi X ((0,0)->(2,0))
        # Odległość powinna wynosić 1.0
        dist = distance_point_to_segment((1, 1), (0, 0), (2, 0))
        self.assertAlmostEqual(dist, 1.0)

if __name__ == '__main__':
    unittest.main()