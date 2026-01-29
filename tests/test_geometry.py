import unittest
import sys
import os

# Dodajemy katalog nadrzędny do ścieżki, aby Python widział pakiet 'logic'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logic.algorithm import find_intersection
from logic.math_utils import on_segment, distance_point_to_segment

class TestGeometryLogic(unittest.TestCase):

    def assertPointEqual(self, p1, p2):
        """Pomocnicza funkcja do porównywania punktów z tolerancją float."""
        self.assertAlmostEqual(p1[0], p2[0], places=7)
        self.assertAlmostEqual(p1[1], p2[1], places=7)

    def test_intersection_cross(self):
        """Test 1: Klasyczne przecięcie w kształcie X."""
        # Odcinek 1: (-2, -2) -> (2, 2)
        # Odcinek 2: (-2, 2) -> (2, -2)
        # Przecięcie: (0, 0)
        res_type, res_data = find_intersection((-2, -2), (2, 2), (-2, 2), (2, -2))
        self.assertEqual(res_type, "POINT")
        self.assertPointEqual(res_data, (0, 0))

    def test_no_intersection_parallel(self):
        """Test 2: Równoległe odcinki (brak przecięcia)."""
        # Pionowe równoległe: x=0 i x=2
        res_type, res_data = find_intersection((0, 0), (0, 5), (2, 0), (2, 5))
        self.assertEqual(res_type, "NONE")
        self.assertIsNone(res_data)

    def test_overlapping_segments(self):
        """Test 3: Odcinki leżące na jednej prostej i nakładające się."""
        # L1: (0,0) -> (4,0)
        # L2: (2,0) -> (6,0)
        # Część wspólna: (2,0) -> (4,0)
        res_type, res_data = find_intersection((0, 0), (4, 0), (2, 0), (6, 0))
        self.assertEqual(res_type, "SEGMENT")
        # res_data to krotka (start, end)
        self.assertPointEqual(res_data[0], (2, 0))
        self.assertPointEqual(res_data[1], (4, 0))

    def test_endpoint_touch(self):
        """Test 4: Odcinki stykające się końcami (kształt V)."""
        # L1: (0,0) -> (2,2)
        # L2: (2,2) -> (4,0)
        # Styk: (2,2)
        res_type, res_data = find_intersection((0, 0), (2, 2), (2, 2), (4, 0))
        self.assertEqual(res_type, "POINT")
        self.assertPointEqual(res_data, (2, 2))

    def test_infinite_lines(self):
        """Test 5: Odcinki się nie stykają, ale proste nieskończone tak."""
        # L1: (0,0) -> (1,1) (leży na y=x)
        # L2: (0,2) -> (1,2) (leży na y=2)
        # Jako odcinki: BRAK. Jako proste: przecięcie w (2,2)
        
        # A. Tryb domyślny (Finite)
        res_type, _ = find_intersection((0, 0), (1, 1), (0, 2), (1, 2), infinite=False)
        self.assertEqual(res_type, "NONE")

        # B. Tryb nieskończony (Infinite)
        res_type, res_data = find_intersection((0, 0), (1, 1), (0, 2), (1, 2), infinite=True)
        self.assertEqual(res_type, "POINT")
        self.assertPointEqual(res_data, (2, 2))

    def test_vertical_and_horizontal(self):
        """Test 6: Przecięcie linii pionowej i poziomej."""
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

    # --- TESTY MATH UTILS ---

    def test_on_segment(self):
        # Punkt środkowy
        self.assertTrue(on_segment((1, 1), (0, 0), (2, 2)))
        # Punkt końcowy
        self.assertTrue(on_segment((0, 0), (0, 0), (2, 2)))
        # Punkt poza odcinkiem (współliniowy)
        self.assertFalse(on_segment((3, 3), (0, 0), (2, 2)))

    def test_distance_point_segment(self):
        # Punkt (0, 1) odległy od odcinka na osi X ((0,0)->(2,0)) o 1.0
        dist = distance_point_to_segment((1, 1), (0, 0), (2, 0))
        self.assertAlmostEqual(dist, 1.0)

if __name__ == '__main__':
    unittest.main()