"""Дискретная математика: свойства бинарных отношений и анализ простых графов."""
from __future__ import annotations

import re
from collections import deque
from itertools import product

from .core import Solution

Pair = tuple[str, str]


def _key(x: str):
    """Естественный порядок: числа как числа, остальное как строки."""
    try:
        return (0, int(x), "")
    except ValueError:
        return (1, 0, x)


def _pair(p: Pair) -> str:
    return f"({p[0]}, {p[1]})"


# ------------------------------------------------------------------- отношения

def parse_relation(elements: str, pairs: str) -> tuple[list[str], set[Pair]]:
    """elements: '1 2 3', pairs: '(1,1) (1,2)' -> (элементы, множество пар)."""
    elems = sorted(set(elements.replace(",", " ").split()), key=_key)
    if not elems:
        raise ValueError("пустое множество элементов")
    found = re.findall(r"\(\s*([^,()\s]+)\s*,\s*([^,()\s]+)\s*\)", pairs)
    rel = {(a, b) for a, b in found}
    outside = sorted({x for p in rel for x in p if x not in elems}, key=_key)
    if outside:
        raise ValueError(f"в парах есть элементы вне множества: {', '.join(outside)}")
    return elems, rel


def is_reflexive(elems: list[str], rel: set[Pair]) -> tuple[bool, Pair | None]:
    for a in elems:
        if (a, a) not in rel:
            return False, (a, a)
    return True, None


def is_symmetric(elems: list[str], rel: set[Pair]) -> tuple[bool, Pair | None]:
    for a, b in sorted(rel, key=lambda p: (_key(p[0]), _key(p[1]))):
        if (b, a) not in rel:
            return False, (a, b)
    return True, None


def is_antisymmetric(elems: list[str], rel: set[Pair]) -> tuple[bool, Pair | None]:
    for a, b in sorted(rel, key=lambda p: (_key(p[0]), _key(p[1]))):
        if a != b and (b, a) in rel:
            return False, (a, b)
    return True, None


def is_transitive(elems: list[str], rel: set[Pair]) -> tuple[bool, tuple[Pair, Pair] | None]:
    for a, b in sorted(rel, key=lambda p: (_key(p[0]), _key(p[1]))):
        for c in elems:
            if (b, c) in rel and (a, c) not in rel:
                return False, ((a, b), (b, c))
    return True, None


def equivalence_classes(elems: list[str], rel: set[Pair]) -> list[list[str]]:
    seen: set[str] = set()
    classes = []
    for a in elems:
        if a in seen:
            continue
        cls = sorted((b for b in elems if (a, b) in rel), key=_key)
        seen.update(cls)
        classes.append(cls)
    return classes


def hasse_edges(elems: list[str], rel: set[Pair]) -> list[Pair]:
    """Покрытия частичного порядка: a < b без элемента строго между ними."""
    edges = []
    for a, b in product(elems, repeat=2):
        if a == b or (a, b) not in rel:
            continue
        if not any(c not in (a, b) and (a, c) in rel and (c, b) in rel for c in elems):
            edges.append((a, b))
    return edges


def analyze_relation(elems: list[str], rel: set[Pair]) -> Solution:
    steps = [f"Множество A = {{{', '.join(elems)}}}, "
             f"отношение R = {{{', '.join(_pair(p) for p in sorted(rel, key=lambda p: (_key(p[0]), _key(p[1]))))}}}"]

    refl, w = is_reflexive(elems, rel)
    steps.append("Рефлексивность: " + ("выполняется, все (a, a) на месте." if refl
                                       else f"не выполняется: нет пары {_pair(w)}."))
    sym, w = is_symmetric(elems, rel)
    steps.append("Симметричность: " + ("выполняется." if sym
                                       else f"не выполняется: есть {_pair(w)}, но нет {_pair((w[1], w[0]))}."))
    anti, w = is_antisymmetric(elems, rel)
    steps.append("Антисимметричность: " + ("выполняется." if anti
                                           else f"не выполняется: есть и {_pair(w)}, и {_pair((w[1], w[0]))} при {w[0]} ≠ {w[1]}."))
    trans, w = is_transitive(elems, rel)
    steps.append("Транзитивность: " + ("выполняется." if trans
                                       else f"не выполняется: есть {_pair(w[0])} и {_pair(w[1])}, но нет {_pair((w[0][0], w[1][1]))}."))

    props = {"reflexive": refl, "symmetric": sym, "antisymmetric": anti, "transitive": trans}
    kinds = []
    if refl and sym and trans:
        kinds.append("отношение эквивалентности")
        classes = equivalence_classes(elems, rel)
        steps.append("Классы эквивалентности: " + ", ".join("{" + ", ".join(c) + "}" for c in classes))
        props["classes"] = classes
    if refl and anti and trans:
        kinds.append("частичный порядок")
        edges = hasse_edges(elems, rel)
        steps.append("Рёбра диаграммы Хассе (покрытия): "
                     + (", ".join(f"{a} → {b}" for a, b in edges) if edges else "нет"))
        props["hasse"] = edges
    answer = (" и ".join(kinds) if kinds
              else "не является ни отношением эквивалентности, ни частичным порядком")
    return Solution(props, answer, steps)


# ---------------------------------------------------------------------- графы

Graph = dict[str, set[str]]


def parse_graph(text: str) -> Graph:
    """'1-2 2-3 4' -> граф: токен 'a-b' — ребро, одиночный токен — изолированная вершина."""
    g: Graph = {}
    for token in text.replace(",", " ").split():
        if "-" in token:
            parts = token.split("-")
            if len(parts) != 2 or not all(parts):
                raise ValueError(f"не удалось разобрать ребро: {token!r}")
            u, v = parts
            if u == v:
                raise ValueError(f"петли не поддерживаются: {token!r}")
            g.setdefault(u, set()).add(v)
            g.setdefault(v, set()).add(u)
        else:
            g.setdefault(token, set())
    if not g:
        raise ValueError("пустой граф")
    return g


def components(g: Graph) -> list[list[str]]:
    seen: set[str] = set()
    out = []
    for s in sorted(g, key=_key):
        if s in seen:
            continue
        comp, queue = [], deque([s])
        seen.add(s)
        while queue:
            u = queue.popleft()
            comp.append(u)
            for v in sorted(g[u], key=_key):
                if v not in seen:
                    seen.add(v)
                    queue.append(v)
        out.append(sorted(comp, key=_key))
    return out


def bipartition(g: Graph) -> tuple[bool, object]:
    """(True, (часть A, часть B)) или (False, ребро-нарушитель)."""
    color: dict[str, int] = {}
    for s in sorted(g, key=_key):
        if s in color:
            continue
        color[s] = 0
        queue = deque([s])
        while queue:
            u = queue.popleft()
            for v in sorted(g[u], key=_key):
                if v not in color:
                    color[v] = 1 - color[u]
                    queue.append(v)
                elif color[v] == color[u]:
                    return False, (u, v)
    a = sorted((v for v, c in color.items() if c == 0), key=_key)
    b = sorted((v for v, c in color.items() if c == 1), key=_key)
    return True, (a, b)


def shortest_path(g: Graph, source: str, target: str) -> list[str] | None:
    if source not in g or target not in g:
        raise ValueError("вершина не найдена в графе")
    prev: dict[str, str | None] = {source: None}
    queue = deque([source])
    while queue:
        u = queue.popleft()
        if u == target:
            path = []
            while u is not None:
                path.append(u)
                u = prev[u]
            return path[::-1]
        for v in sorted(g[u], key=_key):
            if v not in prev:
                prev[v] = u
                queue.append(v)
    return None


def analyze_graph(g: Graph) -> Solution:
    verts = sorted(g, key=_key)
    n = len(verts)
    edges = sum(len(g[v]) for v in g) // 2
    degrees = {v: len(g[v]) for v in verts}
    comps = components(g)
    connected = len(comps) == 1

    steps = [
        f"Вершин: {n}, рёбер: {edges}.",
        "Степени вершин: " + ", ".join(f"{v}:{d}" for v, d in degrees.items())
        + f" (сумма {sum(degrees.values())} = 2·{edges}, проверка рукопожатий).",
        f"Компонент связности: {len(comps)}: " + "; ".join("{" + ", ".join(c) + "}" for c in comps),
    ]

    ok, info = bipartition(g)
    if ok:
        steps.append(f"Двудольность: да, доли {{{', '.join(info[0])}}} и {{{', '.join(info[1])}}}.")
    else:
        steps.append(f"Двудольность: нет, при раскраске в два цвета вершины {info[0]} и {info[1]} "
                     "смежны, но получили один цвет (граф содержит нечётный цикл).")

    is_tree = connected and edges == n - 1
    steps.append("Дерево: " + ("да (связный, рёбер на одно меньше, чем вершин)." if is_tree
                               else "нет."))

    odd = [v for v in verts if degrees[v] % 2 == 1]
    with_edges = [c for c in comps if any(degrees[v] > 0 for v in c)]
    if edges == 0:
        euler = "рёбер нет"
    elif len(with_edges) > 1:
        euler = "нет: рёбра лежат в разных компонентах связности"
    elif not odd:
        euler = "есть эйлеров цикл (все степени чётные, рёбра в одной компоненте)"
    elif len(odd) == 2:
        euler = f"есть эйлеров путь между {odd[0]} и {odd[1]} (ровно две нечётные вершины), цикла нет"
    else:
        euler = f"нет: нечётных вершин {len(odd)} ({', '.join(odd)}), а допустимо 0 или 2"
    steps.append(f"Эйлеров обход: {euler}.")

    value = {"vertices": n, "edges": edges, "connected": connected, "bipartite": ok,
             "tree": is_tree, "components": comps, "degrees": degrees, "euler": euler}
    answer = (f"вершин {n}, рёбер {edges}, "
              f"{'связный' if connected else 'несвязный'}, "
              f"{'двудольный' if ok else 'не двудольный'}"
              f"{', дерево' if is_tree else ''}")
    return Solution(value, answer, steps)
