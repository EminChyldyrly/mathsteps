"""Аналитическая геометрия на плоскости и в пространстве: прямая, расстояние, угол, площадь."""
from __future__ import annotations

from fractions import Fraction
from math import acos, degrees, gcd, isqrt, sqrt

from .core import Solution, fmt

Point = list[Fraction]


def _lcm(a: int, b: int) -> int:
    return a // gcd(a, b) * b


def _int_coeffs(a: Fraction, b: Fraction, c: Fraction) -> tuple[int, int, int]:
    """Приводит (a, b, c) к взаимно простым целым, первый ненулевой коэффициент > 0."""
    d = _lcm(_lcm(a.denominator, b.denominator), c.denominator)
    ia, ib, ic = int(a * d), int(b * d), int(c * d)
    g = gcd(gcd(abs(ia), abs(ib)), abs(ic))
    ia, ib, ic = ia // g, ib // g, ic // g
    lead = ia if ia != 0 else ib
    if lead < 0:
        ia, ib, ic = -ia, -ib, -ic
    return ia, ib, ic


def fmt_line(a: int, b: int, c: int) -> str:
    parts = []
    for coef, var in ((a, "x"), (b, "y")):
        if coef == 0:
            continue
        mag = abs(coef)
        body = var if mag == 1 else f"{mag}{var}"
        parts.append(body if (not parts and coef > 0) else (f"−{body}" if not parts else
                     f"{'+' if coef > 0 else '−'} {body}"))
    if c != 0:
        parts.append(f"{'+' if c > 0 else '−'} {abs(c)}")
    return " ".join(parts) + " = 0"


def _v(x: Fraction) -> str:
    """Число для подстановки в формулу: отрицательные берём в скобки."""
    return f"({fmt(x)})" if x < 0 else fmt(x)


def _pt(p: Point) -> str:
    return "(" + ", ".join(fmt(x) for x in p) + ")"


def line_through(p: Point, q: Point) -> Solution:
    if len(p) != 2 or len(q) != 2:
        raise ValueError("прямая задаётся двумя точками на плоскости")
    if p == q:
        raise ValueError("точки совпадают, прямая не определена")
    (x1, y1), (x2, y2) = p, q
    a, b = y2 - y1, x1 - x2
    c = -(a * x1 + b * y1)
    steps = [f"Направляющий вектор: {_pt(q)} − {_pt(p)} = ({fmt(x2 - x1)}, {fmt(y2 - y1)})",
             "Нормаль (a, b) = (y₂ − y₁, x₁ − x₂), затем c = −(a·x₁ + b·y₁)",
             f"a = {fmt(a)}, b = {fmt(b)}, c = {fmt(c)}"]
    ia, ib, ic = _int_coeffs(a, b, c)
    steps.append("Приводим к целым взаимно простым коэффициентам.")
    return Solution((ia, ib, ic), fmt_line(ia, ib, ic), steps)


def point_line_distance(p: Point, a: Fraction, b: Fraction, c: Fraction) -> Solution:
    if len(p) != 2:
        raise ValueError("точка должна быть на плоскости")
    if a == 0 and b == 0:
        raise ValueError("a и b не могут быть нулями одновременно")
    ia, ib, ic = _int_coeffs(a, b, c)
    num = abs(ia * p[0] + ib * p[1] + ic)
    den2 = ia * ia + ib * ib
    root = isqrt(den2)
    steps = [f"Прямая: {fmt_line(ia, ib, ic)}",
             "Расстояние от точки до прямой: d = |a·x₀ + b·y₀ + c| / √(a² + b²)",
             f"числитель: |{ia}·{_v(p[0])} {'+' if ib >= 0 else '−'} {abs(ib)}·{_v(p[1])} "
             f"{'+' if ic >= 0 else '−'} {abs(ic)}| = {fmt(num)}",
             f"знаменатель: √({ia}² + {ib}²) = √{den2}" + (f" = {root}" if root * root == den2 else "")]
    if root * root == den2:
        exact = Fraction(num) / root
        value = float(exact)
        answer = f"d = {fmt(exact)}"
    else:
        value = float(num) / sqrt(den2)
        answer = f"d = {fmt(num)}/√{den2} ≈ {value:.4f}"
    return Solution(value, answer, steps)


def angle_between(u: Point, v: Point) -> Solution:
    if len(u) != len(v):
        raise ValueError("векторы должны быть одной размерности")
    nu = sum(x * x for x in u)
    nv = sum(x * x for x in v)
    if nu == 0 or nv == 0:
        raise ValueError("угол с нулевым вектором не определён")
    dot = sum(x * y for x, y in zip(u, v))
    steps = [f"u = {_pt(u)}, v = {_pt(v)}",
             f"Скалярное произведение: u·v = {fmt(dot)}",
             f"|u|² = {fmt(nu)}, |v|² = {fmt(nv)}",
             "cos φ = u·v / (|u|·|v|)"]
    if dot == 0:
        return Solution(90.0, "φ = 90° (векторы перпендикулярны)", steps)
    cos = float(dot) / sqrt(float(nu) * float(nv))
    cos = max(-1.0, min(1.0, cos))  # защита от погрешности около ±1
    phi = degrees(acos(cos))
    steps.append(f"cos φ = {fmt(dot)} / √({fmt(nu * nv)}) ≈ {cos:.4f}")
    return Solution(phi, f"φ ≈ {phi:.2f}°", steps)


def triangle_area(p: Point, q: Point, r: Point) -> Solution:
    if not (len(p) == len(q) == len(r) == 2):
        raise ValueError("площадь считается для точек на плоскости")
    cross = (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    area = abs(cross) / 2
    steps = [f"Векторы из первой вершины: ({fmt(q[0] - p[0])}, {fmt(q[1] - p[1])}) и "
             f"({fmt(r[0] - p[0])}, {fmt(r[1] - p[1])})",
             f"Псевдоскалярное произведение: {fmt(cross)}",
             "S = |определитель| / 2"]
    note = " (точки лежат на одной прямой)" if area == 0 else ""
    return Solution(area, f"S = {fmt(area)}{note}", steps)
