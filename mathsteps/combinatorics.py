"""Комбинаторика: перестановки, размещения, сочетания (в том числе с повторениями)."""
from __future__ import annotations

from math import comb, factorial, perm, prod

from .core import Solution


def _check(n: int, k: int | None = None, *, k_le_n: bool = True) -> None:
    if n < 0 or (k is not None and k < 0):
        raise ValueError("n и k должны быть неотрицательными")
    if k is not None and k_le_n and k > n:
        raise ValueError("k не может быть больше n")


def permutations(n: int) -> Solution:
    _check(n)
    v = factorial(n)
    return Solution(v, f"P({n}) = {n}! = {v}",
                    [f"Перестановки n различных элементов: P(n) = n!"])


def arrangements(n: int, k: int) -> Solution:
    _check(n, k)
    v = perm(n, k)
    steps = ["Размещения без повторений (порядок важен): A(n, k) = n! / (n − k)!",
             f"A({n}, {k}) = {n}! / {n - k}! = {factorial(n)} / {factorial(n - k)} = {v}"]
    return Solution(v, f"A({n}, {k}) = {v}", steps)


def combinations(n: int, k: int) -> Solution:
    _check(n, k)
    v = comb(n, k)
    steps = ["Сочетания без повторений (порядок не важен): C(n, k) = n! / (k!·(n − k)!)",
             f"C({n}, {k}) = {n}! / ({k}!·{n - k}!) = {factorial(n)} / ({factorial(k)}·{factorial(n - k)}) = {v}"]
    if k > n - k:
        steps.append(f"Можно было считать через симметрию: C({n}, {k}) = C({n}, {n - k}).")
    return Solution(v, f"C({n}, {k}) = {v}", steps)


def arrangements_with_repetition(n: int, k: int) -> Solution:
    _check(n, k, k_le_n=False)
    v = n ** k
    steps = ["Размещения с повторениями: каждую из k позиций можно заполнить n способами, Ā(n, k) = n^k",
             f"Ā({n}, {k}) = {n}^{k} = {v}"]
    return Solution(v, f"Ā({n}, {k}) = {v}", steps)


def combinations_with_repetition(n: int, k: int) -> Solution:
    _check(n, k, k_le_n=False)
    if n == 0 and k > 0:
        raise ValueError("при n = 0 выбрать k > 0 элементов нельзя")
    v = comb(n + k - 1, k)
    steps = ["Сочетания с повторениями: C̄(n, k) = C(n + k − 1, k)",
             f"C̄({n}, {k}) = C({n + k - 1}, {k}) = {v}"]
    return Solution(v, f"C̄({n}, {k}) = {v}", steps)


def multiset_permutations(counts: list[int]) -> Solution:
    """Перестановки с повторениями: n! / (k1!·k2!·…)."""
    if not counts or any(c <= 0 for c in counts):
        raise ValueError("нужны положительные количества одинаковых элементов")
    n = sum(counts)
    v = factorial(n) // prod(factorial(c) for c in counts)
    denom = "·".join(f"{c}!" for c in counts)
    steps = ["Перестановки с повторениями: P(k1, …, km) = n! / (k1!·…·km!)",
             f"n = {' + '.join(map(str, counts))} = {n}",
             f"P = {n}! / ({denom}) = {v}"]
    return Solution(v, f"P({', '.join(map(str, counts))}) = {v}", steps)
