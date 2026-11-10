import random
import unittest
from itertools import product

from mathsteps import discrete


def rel(elements, pairs):
    return discrete.parse_relation(elements, pairs)


class RelationTests(unittest.TestCase):
    def test_equality_is_equivalence(self):
        e, r = rel("1 2 3", "(1,1) (2,2) (3,3)")
        res = discrete.analyze_relation(e, r)
        self.assertEqual(res.value["classes"], [["1"], ["2"], ["3"]])
        self.assertIn("эквивалент", res.answer)

    def test_same_parity_classes(self):
        pairs = " ".join(f"({a},{b})" for a, b in product("1234", repeat=2)
                         if int(a) % 2 == int(b) % 2)
        e, r = rel("1 2 3 4", pairs)
        res = discrete.analyze_relation(e, r)
        self.assertEqual(res.value["classes"], [["1", "3"], ["2", "4"]])

    def test_less_or_equal_is_partial_order_with_hasse(self):
        pairs = " ".join(f"({a},{b})" for a, b in product("123", repeat=2) if a <= b)
        e, r = rel("1 2 3", pairs)
        res = discrete.analyze_relation(e, r)
        self.assertEqual(res.answer, "частичный порядок")
        self.assertEqual(res.value["hasse"], [("1", "2"), ("2", "3")])

    def test_divisibility_hasse(self):
        elems = ["1", "2", "3", "6"]
        pairs = " ".join(f"({a},{b})" for a, b in product(elems, repeat=2) if int(b) % int(a) == 0)
        e, r = rel(" ".join(elems), pairs)
        self.assertEqual(discrete.hasse_edges(e, r),
                         [("1", "2"), ("1", "3"), ("2", "6"), ("3", "6")])

    def test_transitivity_witness(self):
        e, r = rel("1 2 3", "(1,1) (2,2) (3,3) (1,2) (2,3)")
        ok, w = discrete.is_transitive(e, r)
        self.assertFalse(ok)
        self.assertEqual(w, (("1", "2"), ("2", "3")))

    def test_reflexive_symmetric_antisymmetric_witnesses(self):
        e, r = rel("1 2", "(1,2) (2,1)")
        self.assertEqual(discrete.is_reflexive(e, r), (False, ("1", "1")))
        self.assertTrue(discrete.is_symmetric(e, r)[0])
        self.assertEqual(discrete.is_antisymmetric(e, r), (False, ("1", "2")))
        e, r = rel("1 2", "(1,2)")
        self.assertEqual(discrete.is_symmetric(e, r), (False, ("1", "2")))

    def test_neither(self):
        e, r = rel("1 2", "(1,2)")
        self.assertIn("ни отношением эквивалентности", discrete.analyze_relation(e, r).answer)

    def test_parse_errors(self):
        with self.assertRaises(ValueError):
            rel("1 2", "(1,3)")
        with self.assertRaises(ValueError):
            rel("", "(1,2)")

    def test_numeric_ordering_not_lexicographic(self):
        e, _ = rel("10 9 2", "")
        self.assertEqual(e, ["2", "9", "10"])


def brute_force_bipartite(g):
    verts = sorted(g)
    for colors in product((0, 1), repeat=len(verts)):
        c = dict(zip(verts, colors))
        if all(c[u] != c[v] for u in g for v in g[u]):
            return True
    return False


def union_find_components(g):
    parent = {v: v for v in g}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for u in g:
        for v in g[u]:
            parent[find(u)] = find(v)
    return len({find(v) for v in g})


def brute_force_euler(g):
    """Независимая проверка перебором: (есть ли эйлеров путь, есть ли эйлеров цикл)."""
    edges = {frozenset((u, v)) for u in g for v in g[u]}
    total = len(edges)
    if total == 0:
        return False, False
    found = {"trail": False, "circuit": False}

    def walk(v, start, used):
        if len(used) == total:
            found["trail"] = True
            if v == start:
                found["circuit"] = True
            return
        for w in g[v]:
            e = frozenset((v, w))
            if e not in used:
                walk(w, start, used | {e})

    for s in g:
        walk(s, s, frozenset())
    return found["trail"], found["circuit"]


class GraphTests(unittest.TestCase):
    def test_path_graph(self):
        g = discrete.parse_graph("1-2 2-3 3-4")
        v = discrete.analyze_graph(g).value
        self.assertTrue(v["tree"] and v["bipartite"] and v["connected"])
        self.assertIn("эйлеров путь между 1 и 4", v["euler"])

    def test_triangle(self):
        v = discrete.analyze_graph(discrete.parse_graph("1-2 2-3 3-1")).value
        self.assertFalse(v["bipartite"])
        self.assertFalse(v["tree"])
        self.assertIn("эйлеров цикл", v["euler"])

    def test_k4_has_no_euler_walk(self):
        g = discrete.parse_graph("1-2 1-3 1-4 2-3 2-4 3-4")
        # именно префикс: в положительном ответе тоже встречается слово «нет» («цикла нет»)
        self.assertTrue(discrete.analyze_graph(g).value["euler"].startswith("нет:"))

    def test_euler_path_message_is_not_negative(self):
        g = discrete.parse_graph("1-2 2-3")
        euler = discrete.analyze_graph(g).value["euler"]
        self.assertTrue(euler.startswith("есть эйлеров путь"))

    def test_edges_in_two_components_no_euler(self):
        g = discrete.parse_graph("1-2 3-4")
        euler = discrete.analyze_graph(g).value["euler"]
        self.assertTrue(euler.startswith("нет:"))
        self.assertIn("разных компонентах", euler)

    def test_isolated_vertices_do_not_break_euler(self):
        g = discrete.parse_graph("1-2 2-3 3-1 9")
        v = discrete.analyze_graph(g).value
        self.assertFalse(v["connected"])
        self.assertIn("эйлеров цикл", v["euler"])

    def test_shortest_path(self):
        g = discrete.parse_graph("1-2 2-3 3-4 4-1 5")
        self.assertEqual(len(discrete.shortest_path(g, "1", "3")), 3)
        self.assertIsNone(discrete.shortest_path(g, "1", "5"))
        self.assertEqual(discrete.shortest_path(g, "2", "2"), ["2"])
        with self.assertRaises(ValueError):
            discrete.shortest_path(g, "1", "99")

    def test_parse_errors(self):
        for bad in ("", "1-1", "1-2-3", "-2"):
            with self.assertRaises(ValueError, msg=bad):
                discrete.parse_graph(bad)

    def test_random_graphs_against_independent_implementations(self):
        rng = random.Random(7)
        for _ in range(300):
            n = rng.randint(1, 8)
            g = {str(i): set() for i in range(n)}
            for i in range(n):
                for j in range(i + 1, n):
                    if rng.random() < 0.3:
                        g[str(i)].add(str(j))
                        g[str(j)].add(str(i))
            ok, _ = discrete.bipartition(g)
            self.assertEqual(ok, brute_force_bipartite(g), g)
            self.assertEqual(len(discrete.components(g)), union_find_components(g), g)
            edges = sum(len(s) for s in g.values()) // 2
            self.assertEqual(discrete.analyze_graph(g).value["edges"], edges)

    def test_euler_classification_against_brute_force(self):
        rng = random.Random(10)
        seen = {"цикл": 0, "путь": 0, "нет": 0}
        for _ in range(400):
            n = rng.randint(2, 6)
            g = {str(i): set() for i in range(n)}
            for i in range(n):
                for j in range(i + 1, n):
                    if rng.random() < 0.45:
                        g[str(i)].add(str(j))
                        g[str(j)].add(str(i))
            if sum(len(s) for s in g.values()) // 2 > 9:
                continue  # перебор обходов ограничиваем по размеру
            trail, circuit = brute_force_euler(g)
            euler = discrete.analyze_graph(g).value["euler"]
            if euler == "рёбер нет":
                self.assertFalse(trail, g)
            elif euler.startswith("есть эйлеров цикл"):
                self.assertTrue(circuit, g)
                seen["цикл"] += 1
            elif euler.startswith("есть эйлеров путь"):
                self.assertTrue(trail and not circuit, g)
                seen["путь"] += 1
            else:
                self.assertTrue(euler.startswith("нет:"), euler)
                self.assertFalse(trail, g)
                seen["нет"] += 1
        # тест должен реально встречать все три вида исходов
        for kind, count in seen.items():
            self.assertGreater(count, 10, f"мало случаев «{kind}»: {seen}")


if __name__ == "__main__":
    unittest.main()
