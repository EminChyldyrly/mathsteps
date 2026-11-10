import contextlib
import io
import itertools
import random
import unittest
from fractions import Fraction
from math import sqrt

from mathsteps import cli, combinatorics, geometry


class CombinatoricsTests(unittest.TestCase):
    def test_against_itertools(self):
        for n in range(0, 7):
            self.assertEqual(combinatorics.permutations(n).value,
                             len(list(itertools.permutations(range(n)))))
            for k in range(0, n + 1):
                self.assertEqual(combinatorics.arrangements(n, k).value,
                                 len(list(itertools.permutations(range(n), k))))
                self.assertEqual(combinatorics.combinations(n, k).value,
                                 len(list(itertools.combinations(range(n), k))))
        for n in range(1, 5):
            for k in range(0, 5):
                self.assertEqual(combinatorics.arrangements_with_repetition(n, k).value,
                                 len(list(itertools.product(range(n), repeat=k))))
                self.assertEqual(combinatorics.combinations_with_repetition(n, k).value,
                                 len(list(itertools.combinations_with_replacement(range(n), k))))

    def test_multiset_permutations(self):
        self.assertEqual(combinatorics.multiset_permutations([2, 2, 1]).value,
                         len(set(itertools.permutations("aabbc"))))
        self.assertEqual(combinatorics.multiset_permutations([2, 1, 1, 1]).value, 60)

    def test_validation(self):
        with self.assertRaises(ValueError):
            combinatorics.combinations(3, 5)
        with self.assertRaises(ValueError):
            combinatorics.arrangements(-1, 0)
        with self.assertRaises(ValueError):
            combinatorics.multiset_permutations([2, 0])
        with self.assertRaises(ValueError):
            combinatorics.combinations_with_repetition(0, 2)

    def test_explanation_shows_formula(self):
        text = combinatorics.combinations(10, 3).render()
        self.assertIn("10!", text)
        self.assertIn("120", text)


def P(*xs):
    return [Fraction(x) for x in xs]


class GeometryTests(unittest.TestCase):
    def test_line_through_points(self):
        self.assertEqual(geometry.line_through(P(1, 2), P(3, 5)).value, (3, -2, 1))
        self.assertEqual(geometry.line_through(P(0, 0), P(0, 4)).value, (1, 0, 0))   # x = 0
        self.assertEqual(geometry.line_through(P(0, 3), P(5, 3)).value, (0, 1, -3))  # y = 3

    def test_line_random_points_lie_on_line_and_coefficients_are_normalized(self):
        rng = random.Random(8)
        from math import gcd
        for _ in range(300):
            p = P(rng.randint(-9, 9), rng.randint(-9, 9))
            q = P(rng.randint(-9, 9), rng.randint(-9, 9))
            if p == q:
                continue
            a, b, c = geometry.line_through(p, q).value
            for x, y in (p, q):
                self.assertEqual(a * x + b * y + c, 0)
            self.assertEqual(gcd(gcd(abs(a), abs(b)), abs(c)), 1)
            self.assertGreater(a if a != 0 else b, 0)

    def test_line_errors(self):
        with self.assertRaises(ValueError):
            geometry.line_through(P(1, 1), P(1, 1))
        with self.assertRaises(ValueError):
            geometry.line_through(P(1, 1, 1), P(2, 2, 2))

    def test_distance_known(self):
        self.assertAlmostEqual(geometry.point_line_distance(P(0, 0), *P(3, 4, -5)).value, 1.0)
        self.assertEqual(geometry.point_line_distance(P(0, 0), *P(3, 4, -5)).answer, "d = 1")
        self.assertIn("√2", geometry.point_line_distance(P(0, 0), *P(1, 1, -1)).answer)

    def test_distance_matches_projection_method(self):
        rng = random.Random(9)
        for _ in range(300):
            a, b, c = (Fraction(rng.randint(-6, 6)) for _ in range(3))
            if a == 0 and b == 0:
                continue
            p = P(rng.randint(-9, 9), rng.randint(-9, 9))
            t = (a * p[0] + b * p[1] + c) / (a * a + b * b)
            foot = (p[0] - t * a, p[1] - t * b)           # основание перпендикуляра
            self.assertEqual(a * foot[0] + b * foot[1] + c, 0)
            expected = sqrt(float((p[0] - foot[0]) ** 2 + (p[1] - foot[1]) ** 2))
            self.assertAlmostEqual(geometry.point_line_distance(p, a, b, c).value, expected, places=9)

    def test_angle(self):
        self.assertAlmostEqual(geometry.angle_between(P(1, 0), P(1, 1)).value, 45.0)
        self.assertAlmostEqual(geometry.angle_between(P(1, 0), P(-1, 0)).value, 180.0)
        self.assertAlmostEqual(geometry.angle_between(P(2, 0, 0), P(5, 0, 0)).value, 0.0, places=5)
        self.assertEqual(geometry.angle_between(P(1, 0, 0), P(0, 3, 0)).value, 90.0)
        self.assertAlmostEqual(geometry.angle_between(P(1, 1, 0), P(0, 1, 1)).value, 60.0)

    def test_angle_errors(self):
        with self.assertRaises(ValueError):
            geometry.angle_between(P(0, 0), P(1, 1))
        with self.assertRaises(ValueError):
            geometry.angle_between(P(1, 2), P(1, 2, 3))

    def test_triangle_area(self):
        self.assertEqual(geometry.triangle_area(P(0, 0), P(4, 0), P(0, 3)).value, 6)
        self.assertEqual(geometry.triangle_area(P(0, 0), P(1, 1), P(2, 2)).value, 0)
        self.assertIn("одной прямой", geometry.triangle_area(P(0, 0), P(1, 1), P(2, 2)).answer)
        self.assertEqual(geometry.triangle_area(P(0, 0), P(1, 0), P(0, 1)).value, Fraction(1, 2))


def run_cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.main(list(argv))
    return code, out.getvalue(), err.getvalue()


class CliTests(unittest.TestCase):
    def test_solve(self):
        code, out, _ = run_cli("solve", "2x + y = 5; x - y = 1")
        self.assertEqual(code, 0)
        self.assertIn("Ответ: x = 2, y = 1", out)
        self.assertIn("R1", out)

    def test_short_hides_steps(self):
        _, out, _ = run_cli("--short", "det", "1 2; 3 4")
        self.assertEqual(out.strip(), "Ответ: det = -2")

    def test_negative_number_arguments(self):
        _, out, _ = run_cli("--short", "dist", "0 0", "3 4 -5")
        self.assertEqual(out.strip(), "Ответ: d = 1")

    def test_graph_with_path(self):
        code, out, _ = run_cli("graph", "1-2 2-3 4", "--path", "1", "3")
        self.assertEqual(code, 0)
        self.assertIn("1 → 2 → 3 (длина 2)", out)

    def test_error_exit_code_and_message(self):
        code, out, err = run_cli("det", "1 2; 3")
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("Ошибка", err)

    def test_comb(self):
        _, out, _ = run_cli("--short", "comb", "comb", "10", "3")
        self.assertIn("120", out)
        code, _, err = run_cli("comb", "comb", "3", "5")
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
