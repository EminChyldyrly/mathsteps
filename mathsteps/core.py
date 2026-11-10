"""Общие типы и форматирование: результат решения, дроби, матрицы, разбор ввода."""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction

Matrix = list[list[Fraction]]


@dataclass
class Solution:
    """Результат задачи: значение для программного использования,
    текстовый ответ и шаги решения для чтения человеком."""

    value: object
    answer: str
    steps: list[str] = field(default_factory=list)

    def render(self, with_steps: bool = True) -> str:
        parts = list(self.steps) if with_steps else []
        parts.append(f"Ответ: {self.answer}")
        return "\n\n".join(parts)


def to_fraction(text: str | int | Fraction) -> Fraction:
    """'3', '-1/2', '0.25' -> Fraction. Бросает ValueError при неверном вводе.

    Десятичная запятая не поддерживается: в матрицах и векторах запятая — разделитель.
    """
    if isinstance(text, (int, Fraction)):
        return Fraction(text)
    try:
        return Fraction(text.strip())
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError(f"не удалось разобрать число: {text!r}") from exc


def fmt(x: Fraction) -> str:
    x = Fraction(x)
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


def fmt_matrix(m: Matrix, augmented: int = 0) -> str:
    """Текстовая матрица; последние `augmented` столбцов отделяются чертой."""
    if not m:
        return "[ ]"
    cells = [[fmt(x) for x in row] for row in m]
    width = [max(len(row[j]) for row in cells) for j in range(len(cells[0]))]
    split = len(cells[0]) - augmented
    lines = []
    for row in cells:
        items = [c.rjust(w) for c, w in zip(row, width)]
        if augmented:
            left, right = "  ".join(items[:split]), "  ".join(items[split:])
            body = f"{left} | {right}"
        else:
            body = "  ".join(items)
        lines.append(f"[ {body} ]")
    return "\n".join(lines)


def parse_matrix(text: str) -> Matrix:
    """'1 2; 3 4' или многострочный ввод -> матрица. Элементы: целые, дроби, десятичные."""
    rows = [r for r in text.replace("\n", ";").split(";") if r.strip()]
    if not rows:
        raise ValueError("пустая матрица")
    m = [[to_fraction(x) for x in r.replace(",", " ").split()] for r in rows]
    if any(len(r) != len(m[0]) for r in m):
        raise ValueError("строки матрицы разной длины")
    return m


def parse_vector(text: str) -> list[Fraction]:
    items = text.replace(",", " ").split()
    if not items:
        raise ValueError("пустой вектор")
    return [to_fraction(x) for x in items]


def matmul(a: Matrix, b: Matrix) -> Matrix:
    if len(a[0]) != len(b):
        raise ValueError("размеры матриц не согласованы для умножения")
    return [[sum(a[i][k] * b[k][j] for k in range(len(b))) for j in range(len(b[0]))]
            for i in range(len(a))]


def identity(n: int) -> Matrix:
    return [[Fraction(int(i == j)) for j in range(n)] for i in range(n)]
