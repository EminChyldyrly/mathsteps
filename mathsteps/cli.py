"""Командная строка mathsteps."""
from __future__ import annotations

import argparse
import sys

from . import combinatorics, discrete, geometry, linalg
from .core import Solution, parse_matrix, parse_vector


def _show(sol: Solution, args: argparse.Namespace) -> int:
    print(sol.render(with_steps=not args.short))
    return 0


def _cmd_solve(args):
    a, b, names = linalg.parse_system(args.system)
    return _show(linalg.solve_system(a, b, names), args)


def _cmd_det(args):
    return _show(linalg.determinant(parse_matrix(args.matrix)), args)


def _cmd_inv(args):
    return _show(linalg.inverse(parse_matrix(args.matrix)), args)


def _cmd_rank(args):
    return _show(linalg.rank(parse_matrix(args.matrix)), args)


def _cmd_relation(args):
    elems, rel = discrete.parse_relation(args.elements, args.pairs)
    return _show(discrete.analyze_relation(elems, rel), args)


def _cmd_graph(args):
    g = discrete.parse_graph(args.graph)
    sol = discrete.analyze_graph(g)
    if args.path:
        s, t = args.path
        path = discrete.shortest_path(g, s, t)
        sol.steps.append(f"Кратчайший путь {s} → {t}: "
                         + (" → ".join(path) + f" (длина {len(path) - 1})" if path
                            else "пути нет, вершины в разных компонентах."))
    return _show(sol, args)


def _cmd_comb(args):
    n, k = args.n, args.k
    kind = args.kind
    if kind == "perm":
        sol = combinatorics.permutations(n)
    elif kind == "arr":
        sol = combinatorics.arrangements(n, k)
    elif kind == "comb":
        sol = combinatorics.combinations(n, k)
    elif kind == "arr-rep":
        sol = combinatorics.arrangements_with_repetition(n, k)
    else:
        sol = combinatorics.combinations_with_repetition(n, k)
    return _show(sol, args)


def _cmd_multiset(args):
    return _show(combinatorics.multiset_permutations(args.counts), args)


def _cmd_line(args):
    return _show(geometry.line_through(parse_vector(args.p), parse_vector(args.q)), args)


def _cmd_dist(args):
    a, b, c = parse_vector(args.line)
    return _show(geometry.point_line_distance(parse_vector(args.point), a, b, c), args)


def _cmd_angle(args):
    return _show(geometry.angle_between(parse_vector(args.u), parse_vector(args.v)), args)


def _cmd_area(args):
    return _show(geometry.triangle_area(
        parse_vector(args.p), parse_vector(args.q), parse_vector(args.r)), args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mathsteps",
        description="Решает задачи по линейной алгебре, дискретной математике и "
                    "аналитической геометрии с пошаговым выводом (точная арифметика).",
        epilog="Аргументы с пробелами заключайте в кавычки. Числа: 3, -1/2, 0.25.")
    parser.add_argument("--short", action="store_true", help="показать только ответ, без шагов")
    sub = parser.add_subparsers(dest="command", required=True)

    def add(name, func, help_, *arguments):
        p = sub.add_parser(name, help=help_)
        for arg_name, kwargs in arguments:
            p.add_argument(arg_name, **kwargs)
        p.set_defaults(func=func)
        return p

    add("solve", _cmd_solve, "решить СЛАУ: '2x + y = 5; x - y = 1'",
        ("system", {"help": "уравнения через ';'"}))
    add("det", _cmd_det, "определитель: '1 2; 3 4'", ("matrix", {}))
    add("inv", _cmd_inv, "обратная матрица", ("matrix", {}))
    add("rank", _cmd_rank, "ранг матрицы", ("matrix", {}))
    add("relation", _cmd_relation, "свойства бинарного отношения",
        ("elements", {"help": "например '1 2 3'"}),
        ("pairs", {"help": "например '(1,1) (2,2) (1,2)'"}))
    p = add("graph", _cmd_graph, "анализ графа: '1-2 2-3 3-1 4'",
            ("graph", {"help": "рёбра 'a-b' и изолированные вершины через пробел"}))
    p.add_argument("--path", nargs=2, metavar=("ОТ", "ДО"), help="найти кратчайший путь")
    p = add("comb", _cmd_comb, "комбинаторные числа",
            ("kind", {"choices": ["perm", "arr", "comb", "arr-rep", "comb-rep"],
                      "help": "perm — n!, arr — размещения, comb — сочетания, "
                              "arr-rep / comb-rep — с повторениями"}),
            ("n", {"type": int}))
    p.add_argument("k", type=int, nargs="?", default=0)
    add("multiset", _cmd_multiset, "перестановки с повторениями: n!/(k1!·k2!·…)",
        ("counts", {"type": int, "nargs": "+", "help": "количества одинаковых элементов"}))
    add("line", _cmd_line, "прямая через две точки: '1 2' '3 5'",
        ("p", {}), ("q", {}))
    add("dist", _cmd_dist, "расстояние от точки до прямой: '0 0' '3 4 -5'",
        ("point", {}), ("line", {"help": "коэффициенты 'a b c' для ax + by + c = 0"}))
    add("angle", _cmd_angle, "угол между векторами: '1 0 0' '1 1 0'",
        ("u", {}), ("v", {}))
    add("area", _cmd_area, "площадь треугольника по трём точкам",
        ("p", {}), ("q", {}), ("r", {}))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except ValueError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
