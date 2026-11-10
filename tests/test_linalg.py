import random
import unittest
from fractions import Fraction

from mathsteps import linalg
from mathsteps.core import identity, matmul, parse_matrix, to_fraction


def laplace_det(m):
    """Независимая реализация: разложение по первой строке."""
    n = len(m)
    if n == 1:
        return m[0][0]
    return sum((-1) ** j * m[0][j] * laplace_det([row[:j] + row[j + 1:] for row in m[1:]])
               for j in range(n))


def random_matrix(rng, rows, cols, lo=-5, hi=5):
    return [[Fraction(rng.randint(lo, hi)) for _ in range(cols)] for _ in range(rows)]


def mat_vec(a, x):
    return [sum(aij * xj for aij, xj in zip(row, x)) for row in a]


class ParsingTests(unittest.TestCase):
    def test_matrix(self):
        self.assertEqual(parse_matrix("1 2; 3/2 -4"),
                         [[1, 2], [Fraction(3, 2), -4]])
        self.assertEqual(parse_matrix("1,2\n3,4"), [[1, 2], [3, 4]])

    def test_matrix_errors(self):
        for bad in ("", "1 2; 3", "1 a; 2 3"):
            with self.assertRaises(ValueError):
                parse_matrix(bad)

    def test_decimal_point_is_supported_but_decimal_comma_is_not(self):
        self.assertEqual(to_fraction("0.5"), Fraction(1, 2))
        self.assertEqual(to_fraction("-3/4"), Fraction(-3, 4))
        with self.assertRaises(ValueError):
            to_fraction("0,5")          # запятая в матрицах и векторах — разделитель
        self.assertEqual(parse_matrix("1,5"), [[1, 5]])   # два элемента, а не 1.5

    def test_system_basic(self):
        a, b, names = linalg.parse_system("2x + 3y = 7; x - y = -1")
        self.assertEqual(names, ["x", "y"])
        self.assertEqual(a, [[2, 3], [1, -1]])
        self.assertEqual(b, [7, -1])

    def test_system_variables_on_both_sides_and_constants(self):
        a, b, names = linalg.parse_system("x = 2y + 1; 3 + z = x")
        self.assertEqual(names, ["x", "y", "z"])
        self.assertEqual(a, [[1, -2, 0], [-1, 0, 1]])
        self.assertEqual(b, [1, -3])

    def test_system_fraction_and_implicit_coefficients(self):
        a, b, _ = linalg.parse_system("1/2x - y = 0.5")
        self.assertEqual(a, [[Fraction(1, 2), -1]])
        self.assertEqual(b, [Fraction(1, 2)])

    def test_system_errors(self):
        # Каждый из этих вводов раньше мог быть молча принят как другое уравнение.
        for bad in ("x + y", "x = y = 2", "", "2 + = 3", "x + * y = 1",
                    "x ++ y = 1", "x - - y = 1", "x + = 1",          # лишние/висящие знаки
                    "2* = 3", "*x = 1", "1/x = 2",                    # неверные слагаемые
                    "2 3 = 1", "x 2 = 1", "x + 2 3 = 1",              # «2 3» не должно стать 23
                    "x y = 1", "xy = 1", "2 x y = 1",                 # возможное произведение
                    "5 = 3"):                                         # нет неизвестных
            with self.assertRaises(ValueError, msg=bad):
                linalg.parse_system(bad)

    def test_system_accepted_spellings(self):
        cases = {
            "2 x + 3 y = 7": ([[2, 3]], [7]),
            "2*x - 3*y = 0": ([[2, -3]], [0]),
            "x_1 + 2 x_2 = 3": ([[1, 2]], [3]),
            "1/2 x = 1": ([[Fraction(1, 2)]], [1]),
            "x + 2x = 3": ([[3]], [3]),          # одинаковые переменные складываются
            "x − y = 1": ([[1, -1]], [1]),       # юникодный минус
            "5 = 2x + 1": ([[-2]], [-4]),
        }
        for text, (exp_a, exp_b) in cases.items():
            a, b, _ = linalg.parse_system(text)
            self.assertEqual(a, [[Fraction(v) for v in r] for r in exp_a], text)
            self.assertEqual(b, [Fraction(v) for v in exp_b], text)

    def test_variable_order_is_first_appearance(self):
        self.assertEqual(linalg.parse_system("y + x = 1; z = 2")[2], ["y", "x", "z"])

    def test_equation_without_unknowns_inside_system_is_inconsistent(self):
        a, b, names = linalg.parse_system("x + y = 1; 0 = 5")
        self.assertEqual(linalg.solve_system(a, b, names).value.status, "none")


class SolveSystemTests(unittest.TestCase):
    def test_unique(self):
        a, b, names = linalg.parse_system("2x + y = 5; x - y = 1")
        res = linalg.solve_system(a, b, names).value
        self.assertEqual(res.status, "unique")
        self.assertEqual(res.evaluate(), [2, 1])

    def test_inconsistent(self):
        a, b, names = linalg.parse_system("x + y = 1; x + y = 2")
        self.assertEqual(linalg.solve_system(a, b, names).value.status, "none")

    def test_infinite_parametric(self):
        a, b, names = linalg.parse_system("x + y + z = 3; 2x + 2y + 2z = 6")
        sol = linalg.solve_system(a, b, names)
        self.assertEqual(sol.value.status, "infinite")
        self.assertEqual(len(sol.value.free), 2)
        self.assertIn("свободные", sol.answer)

    def test_random_square_systems_against_known_solution(self):
        rng = random.Random(1)
        checked = 0
        for _ in range(300):
            n = rng.randint(1, 5)
            a = random_matrix(rng, n, n)
            x0 = [Fraction(rng.randint(-6, 6)) for _ in range(n)]
            b = mat_vec(a, x0)
            res = linalg.solve_system(a, b).value
            if laplace_det(a) != 0:
                self.assertEqual(res.status, "unique")
                self.assertEqual(res.evaluate(), x0)
                checked += 1
            else:
                # система совместна по построению, решений бесконечно много
                self.assertEqual(res.status, "infinite")
                params = {j: Fraction(rng.randint(-9, 9), rng.randint(1, 4)) for j in res.free}
                self.assertEqual(mat_vec(a, res.evaluate(params)), b)
        self.assertGreater(checked, 100)  # тест действительно проверил много невырожденных случаев

    def test_random_rectangular_systems_parametric_solution_satisfies_all_equations(self):
        rng = random.Random(2)
        for _ in range(300):
            rows, cols = rng.randint(1, 5), rng.randint(1, 5)
            a = random_matrix(rng, rows, cols)
            x0 = [Fraction(rng.randint(-4, 4)) for _ in range(cols)]
            b = mat_vec(a, x0)  # совместна по построению
            res = linalg.solve_system(a, b).value
            self.assertNotEqual(res.status, "none")
            params = {j: Fraction(rng.randint(-5, 5)) for j in res.free}
            self.assertEqual(mat_vec(a, res.evaluate(params)), b)

    def test_inconsistent_by_construction(self):
        rng = random.Random(3)
        for _ in range(100):
            n = rng.randint(2, 4)
            a = random_matrix(rng, n, n)
            b = mat_vec(a, [Fraction(rng.randint(-3, 3)) for _ in range(n)])
            a.append(a[0][:])            # дубль первого уравнения
            b.append(b[0] + 1)           # с другой правой частью
            self.assertEqual(linalg.solve_system(a, b).value.status, "none")


class DeterminantTests(unittest.TestCase):
    def test_known(self):
        self.assertEqual(linalg.determinant(parse_matrix("2 1 3; 0 -1 4; 1 2 5")).value, -19)
        self.assertEqual(linalg.determinant(parse_matrix("5")).value, 5)
        self.assertEqual(linalg.determinant(parse_matrix("0 1; 1 0")).value, -1)  # нужна перестановка

    def test_singular(self):
        self.assertEqual(linalg.determinant(parse_matrix("1 2; 2 4")).value, 0)

    def test_matches_laplace_on_random_matrices(self):
        rng = random.Random(4)
        for _ in range(300):
            n = rng.randint(1, 5)
            m = random_matrix(rng, n, n)
            if rng.random() < 0.2 and n > 1:
                m[-1] = m[0][:]  # заведомо вырожденная
            self.assertEqual(linalg.determinant(m).value, laplace_det(m), m)

    def test_fraction_entries(self):
        m = parse_matrix("1/2 1/3; 1/4 1/5")
        self.assertEqual(linalg.determinant(m).value, laplace_det(m))

    def test_non_square_rejected(self):
        with self.assertRaises(ValueError):
            linalg.determinant(parse_matrix("1 2 3; 4 5 6"))


class InverseAndRankTests(unittest.TestCase):
    def test_known_inverse(self):
        inv = linalg.inverse(parse_matrix("2 1; 5 3")).value
        self.assertEqual(inv, [[3, -1], [-5, 2]])

    def test_singular_has_no_inverse(self):
        self.assertIsNone(linalg.inverse(parse_matrix("1 2; 2 4")).value)

    def test_random_inverse_roundtrip(self):
        rng = random.Random(5)
        invertible = 0
        for _ in range(300):
            n = rng.randint(1, 5)
            m = random_matrix(rng, n, n)
            inv = linalg.inverse(m).value
            if laplace_det(m) == 0:
                self.assertIsNone(inv)
            else:
                invertible += 1
                self.assertEqual(matmul(m, inv), identity(n))
                self.assertEqual(matmul(inv, m), identity(n))
        self.assertGreater(invertible, 100)

    def test_rank_known(self):
        self.assertEqual(linalg.rank(parse_matrix("1 2 3; 2 4 6; 1 0 1")).value, 2)
        self.assertEqual(linalg.rank(parse_matrix("0 0; 0 0")).value, 0)

    def test_rank_equals_rank_of_transpose_and_matches_det(self):
        rng = random.Random(6)
        for _ in range(300):
            r, c = rng.randint(1, 5), rng.randint(1, 5)
            m = random_matrix(rng, r, c)
            t = [list(col) for col in zip(*m)]
            self.assertEqual(linalg.rank(m).value, linalg.rank(t).value)
            if r == c:
                full = linalg.rank(m).value == r
                self.assertEqual(full, laplace_det(m) != 0)


if __name__ == "__main__":
    unittest.main()
