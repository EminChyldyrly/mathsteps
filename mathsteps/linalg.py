"""Линейная алгебра: метод Гаусса, СЛАУ, определитель, обратная матрица, ранг.

Все вычисления точные (Fraction). Каждая функция возвращает Solution с шагами.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from fractions import Fraction

from .core import Matrix, Solution, fmt, fmt_matrix, identity


# ---------------------------------------------------------------- Гаусс–Жордан

def _row_op(target: int, f: Fraction, source: int) -> str:
    sign, mag = ("−", f) if f > 0 else ("+", -f)
    coef = "" if mag == 1 else f"{fmt(mag)}·"
    return f"R{target + 1} ← R{target + 1} {sign} {coef}R{source + 1}"


def gauss_jordan(m: Matrix, coeff_cols: int, steps: list[str], augmented: int = 0
                 ) -> tuple[Matrix, list[int]]:
    """Приводит матрицу к приведённому ступенчатому виду.

    Опорные столбцы ищутся только среди первых `coeff_cols` столбцов.
    Каждая элементарная операция добавляется в `steps` вместе с матрицей.
    """
    m = [row[:] for row in m]
    rows = len(m)
    pivots: list[int] = []
    r = 0
    for c in range(coeff_cols):
        if r >= rows:
            break
        pr = next((i for i in range(r, rows) if m[i][c] != 0), None)
        if pr is None:
            continue
        if pr != r:
            m[r], m[pr] = m[pr], m[r]
            steps.append(f"R{r + 1} ↔ R{pr + 1}\n{fmt_matrix(m, augmented)}")
        if m[r][c] != 1:
            p = m[r][c]
            m[r] = [x / p for x in m[r]]
            shown = f"({fmt(p)})" if p < 0 or p.denominator != 1 else fmt(p)
            steps.append(f"R{r + 1} ← R{r + 1} / {shown}\n{fmt_matrix(m, augmented)}")
        for i in range(rows):
            if i != r and m[i][c] != 0:
                f = m[i][c]
                m[i] = [a - f * b for a, b in zip(m[i], m[r])]
                steps.append(f"{_row_op(i, f, r)}\n{fmt_matrix(m, augmented)}")
        pivots.append(c)
        r += 1
    return m, pivots


# ------------------------------------------------------------------------ СЛАУ

@dataclass
class SystemResult:
    status: str                                   # 'unique' | 'none' | 'infinite'
    names: list[str]
    # для каждой переменной: (константа, {индекс свободной переменной: коэффициент})
    expressions: list[tuple[Fraction, dict[int, Fraction]]]
    free: list[int]

    def evaluate(self, params: dict[int, Fraction] | None = None) -> list[Fraction]:
        """Значения переменных при заданных значениях свободных переменных."""
        params = params or {}
        return [const + sum(coef * params[j] for j, coef in terms.items())
                for const, terms in self.expressions]


def _fmt_linear(const: Fraction, terms: dict[int, Fraction], names: list[str]) -> str:
    parts: list[str] = []
    if const != 0 or not terms:
        parts.append(fmt(const))
    for j in sorted(terms):
        c = terms[j]
        if c == 0:
            continue
        mag = abs(c)
        body = names[j] if mag == 1 else f"{fmt(mag)}·{names[j]}"
        if not parts:
            parts.append(body if c > 0 else f"−{body}")
        else:
            parts.append(f"{'+' if c > 0 else '−'} {body}")
    return " ".join(parts) if parts else "0"


def solve_system(a: Matrix, b: list[Fraction], names: list[str] | None = None) -> Solution:
    n = len(a[0])
    if len(a) != len(b):
        raise ValueError("число уравнений не совпадает с длиной правой части")
    names = names or [f"x{j + 1}" for j in range(n)]
    aug = [row[:] + [bi] for row, bi in zip(a, b)]
    steps = [f"Расширенная матрица:\n{fmt_matrix(aug, 1)}"]
    m, pivots = gauss_jordan(aug, n, steps, augmented=1)

    if any(all(x == 0 for x in row[:n]) and row[n] != 0 for row in m):
        steps.append("Есть строка вида 0 = c, где c ≠ 0, поэтому система несовместна.")
        return Solution(SystemResult("none", names, [], []), "решений нет", steps)

    free = [j for j in range(n) if j not in pivots]
    if not free:
        values = [m[i][n] for i in range(n)]
        res = SystemResult("unique", names,
                           [(v, {}) for v in values], [])
        steps.append("Ранг равен числу неизвестных, решение единственное.")
        answer = ", ".join(f"{nm} = {fmt(v)}" for nm, v in zip(names, values))
        return Solution(res, answer, steps)

    expressions: list[tuple[Fraction, dict[int, Fraction]]] = [(Fraction(0), {}) for _ in range(n)]
    for j in free:
        expressions[j] = (Fraction(0), {j: Fraction(1)})
    for i, p in enumerate(pivots):
        expressions[p] = (m[i][n], {j: -m[i][j] for j in free if m[i][j] != 0})
    res = SystemResult("infinite", names, expressions, free)
    free_names = ", ".join(names[j] for j in free)
    steps.append(f"Ранг меньше числа неизвестных. Свободные переменные: {free_names}.")
    answer = "; ".join(f"{names[j]} = {_fmt_linear(*expressions[j], names)}"
                       for j in range(n) if j not in free)
    answer += f" ({free_names} — свободные, любые числа)"
    return Solution(res, answer, steps)


# Имя переменной: одна буква с необязательным индексом (x, y, x1, x_2).
# Многобуквенные имена вроде «xy» запрещены: их легко принять за произведение.
_VAR = r"[A-Za-z](?:_?\d+)?"
# слагаемое: [знак] число | [знак] число[*]переменная | [знак] переменная
_TERM = re.compile(rf"^([+-]?)(?:(\d+(?:\.\d+)?(?:/\d+)?)(?:\*?({_VAR}))?|({_VAR}))$")


def _parse_side(side: str, coeffs: dict[str, Fraction]) -> Fraction:
    """Разбирает одну часть уравнения; возвращает свободный член."""
    from .core import to_fraction
    const = Fraction(0)
    side = side.replace("−", "-")
    # «2 x» -> «2x»; другие пробелы между числами и именами недопустимы (иначе «2 3» стало бы 23)
    squeezed = re.sub(r"(?<![\w.])(\d+(?:\.\d+)?(?:/\d+)?)[ \t]+(?=[A-Za-z])", r"\1", side.strip())
    if re.search(r"[\w.][ \t]+[\w.]", squeezed):
        raise ValueError(f"между слагаемыми пропущен знак: {side.strip()!r}")
    text = squeezed.replace(" ", "").replace("\t", "")
    if not text:
        raise ValueError("пустая часть уравнения")
    terms = re.findall(r"[+-]?[^+-]+", text)
    if "".join(terms) != text:  # висящий или двойной знак, например '2 + = 3' или 'x ++ y'
        raise ValueError(f"лишний или недостающий знак в выражении: {side.strip()!r}")
    for term in terms:
        mt = _TERM.match(term)
        if not mt:
            raise ValueError(f"не удалось разобрать слагаемое: {term!r}")
        sign = -1 if mt.group(1) == "-" else 1
        num = to_fraction(mt.group(2)) if mt.group(2) else Fraction(1)
        var = mt.group(3) or mt.group(4)
        if var:
            coeffs[var] = coeffs.get(var, Fraction(0)) + sign * num
        else:
            const += sign * num
    return const


def parse_system(text: str) -> tuple[Matrix, list[Fraction], list[str]]:
    """'2x + y = 5; x - y = 1' -> (A, b, имена переменных по порядку появления)."""
    equations = [e for e in text.replace("\n", ";").split(";") if e.strip()]
    if not equations:
        raise ValueError("нет уравнений")
    parsed: list[tuple[dict[str, Fraction], Fraction]] = []
    names: list[str] = []
    for eq in equations:
        if eq.count("=") != 1:
            raise ValueError(f"в уравнении должен быть один знак '=': {eq.strip()!r}")
        left, right = eq.split("=")
        lc: dict[str, Fraction] = {}
        rc: dict[str, Fraction] = {}
        lconst = _parse_side(left, lc)
        rconst = _parse_side(right, rc)
        coeffs = dict(lc)
        for k, v in rc.items():
            coeffs[k] = coeffs.get(k, Fraction(0)) - v
        for k in (*lc, *rc):  # порядок появления: слева направо
            if k not in names:
                names.append(k)
        parsed.append((coeffs, rconst - lconst))
    if not names:
        raise ValueError("в системе нет неизвестных")
    a = [[coeffs.get(nm, Fraction(0)) for nm in names] for coeffs, _ in parsed]
    return a, [rhs for _, rhs in parsed], names


# ------------------------------------------------------------------ определитель

def determinant(m: Matrix) -> Solution:
    n = len(m)
    if any(len(r) != n for r in m):
        raise ValueError("определитель определён только для квадратных матриц")
    a = [row[:] for row in m]
    steps = [f"Матрица:\n{fmt_matrix(a)}",
             "Приводим к треугольному виду. Замена строки на её сумму с другой "
             "определитель не меняет, перестановка строк меняет знак."]
    sign = 1
    for c in range(n):
        pr = next((i for i in range(c, n) if a[i][c] != 0), None)
        if pr is None:
            steps.append(f"В столбце {c + 1} ниже диагонали (и на ней) одни нули, поэтому det = 0.")
            return Solution(Fraction(0), "det = 0", steps)
        if pr != c:
            a[c], a[pr] = a[pr], a[c]
            sign = -sign
            steps.append(f"R{c + 1} ↔ R{pr + 1} (знак определителя меняется)\n{fmt_matrix(a)}")
        for i in range(c + 1, n):
            if a[i][c] != 0:
                f = a[i][c] / a[c][c]
                a[i] = [x - f * y for x, y in zip(a[i], a[c])]
                steps.append(f"{_row_op(i, f, c)} (det не меняется)\n{fmt_matrix(a)}")
    diag = [a[i][i] for i in range(n)]
    prod = Fraction(1)
    for d in diag:
        prod *= d
    det = sign * prod
    sign_txt = "" if sign == 1 else "−"
    steps.append(f"Определитель треугольной матрицы — произведение диагонали: "
                 f"det = {sign_txt}{'·'.join(f'({fmt(d)})' for d in diag)}")
    return Solution(det, f"det = {fmt(det)}", steps)


# ----------------------------------------------------------------- обратная, ранг

def inverse(m: Matrix) -> Solution:
    n = len(m)
    if any(len(r) != n for r in m):
        raise ValueError("обратная матрица определена только для квадратных матриц")
    eye = identity(n)
    aug = [row[:] + eye[i] for i, row in enumerate(m)]
    steps = [f"Дописываем единичную матрицу:\n{fmt_matrix(aug, n)}"]
    red, pivots = gauss_jordan(aug, n, steps, augmented=n)
    if len(pivots) < n:
        steps.append("Ранг меньше n, матрица вырождена, обратной не существует.")
        return Solution(None, "обратной матрицы не существует (det = 0)", steps)
    inv = [row[n:] for row in red]
    steps.append("Слева получилась единичная матрица, справа — обратная.")
    return Solution(inv, "A⁻¹ =\n" + fmt_matrix(inv), steps)


def rank(m: Matrix) -> Solution:
    steps = [f"Матрица:\n{fmt_matrix(m)}"]
    _, pivots = gauss_jordan(m, len(m[0]), steps)
    r = len(pivots)
    steps.append(f"Число ненулевых строк в ступенчатом виде: {r}.")
    return Solution(r, f"rank = {r}", steps)
