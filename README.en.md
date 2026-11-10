# mathsteps

*[Русская версия](README.md)*

A solver for linear algebra, discrete mathematics and analytic geometry problems that **shows its work step by step**. Everything is computed exactly with rational numbers (`fractions.Fraction`), with no rounding, so the answer is `1/3`, not `0.3333`. The package uses only the Python standard library and has no dependencies.

It is meant for checking homework and walking through problems: the steps show where a hand-written solution may have gone wrong.

## What it does

| Area | Command | What it does |
|---|---|---|
| Linear algebra | `solve` | Systems of linear equations via Gauss–Jordan elimination: a unique solution, infinitely many (in parametric form), or "no solution" |
| | `det` | Determinant with step-by-step reduction to triangular form |
| | `inv` | Inverse matrix (or an explanation of why it does not exist) |
| | `rank` | Matrix rank |
| Discrete mathematics | `relation` | Reflexivity, symmetry, antisymmetry, transitivity **with a counterexample**; equivalence classes; Hasse diagram |
| | `graph` | Degrees, connected components, bipartiteness, tree test, Euler path/cycle, shortest path |
| | `comb`, `multiset` | Arrangements, combinations, permutations, with and without repetition, showing the formula |
| Analytic geometry | `line`, `dist`, `angle`, `area` | Line through two points, point-to-line distance, angle between vectors, triangle area |

## Quick start

Python 3.10+ is required (tested on 3.13).

```bash
git clone https://github.com/EminChyldyrly/mathsteps
cd mathsteps

python -m mathsteps solve "x + y + z = 6; 2y + 5z = -4; 2x + 5y - z = 27"
python -m mathsteps --short det "2 1 3; 0 -1 4; 1 2 5"     # answer only
```

No installation is needed: the package runs straight from the repository folder. The output is in Russian.

## Examples

A system of equations with a unique solution (steps abridged; the full output is in [docs/examples.md](docs/examples.md)):

```
$ python -m mathsteps solve "x + y + z = 6; 2y + 5z = -4; 2x + 5y - z = 27"
Расширенная матрица:
[ 1  1   1 |  6 ]
[ 0  2   5 | -4 ]
[ 2  5  -1 | 27 ]

R3 ← R3 − 2·R1
...
Ответ: x = 5, y = 3, z = -2
```

Properties of a relation, with a counterexample where a property fails:

```
$ python -m mathsteps relation "1 2 3" "(1,1) (2,2) (3,3) (1,2) (2,3)"
...
Транзитивность: не выполняется: есть (1, 2) и (2, 3), но нет (1, 3).
Ответ: не является ни отношением эквивалентности, ни частичным порядком
```

(Transitivity fails: there are (1, 2) and (2, 3) but no (1, 3). The relation is neither an equivalence relation nor a partial order.)

All examples in `docs/examples.md` were produced by running the real commands, not typed by hand.

## Input format

Quote arguments that contain spaces.

- **Numbers:** `3`, `-1/2`, `0.25`. Decimals use a **dot**: a comma is a separator, so `1,5` in a matrix means two numbers, 1 and 5.
- **Matrices:** rows separated by `;`, entries by spaces or commas: `"1 2; 3 4"`.
- **Equations:** `"2x + y = 5; x - y = 1"`. `2*x`, `2 x`, `1/2x`, variables on both sides and numbers on both sides are allowed. A variable name is one letter with an optional index (`x`, `x1`, `x_2`).
- **Relations:** elements `"1 2 3"`, pairs `"(1,1) (1,2)"`.
- **Graphs:** edges `a-b` and isolated vertices separated by spaces: `"1-2 2-3 4"`.
- **Points and vectors:** `"1 2"` or `"1,2,3"`. For `dist`, the line is given by the coefficients `"a b c"` of `ax + by + c = 0`.

Input is parsed strictly: an ambiguous expression is rejected with a clear error instead of being guessed. For example, `x y = 1` and `xy = 1` are not accepted (they could be a product, and the solver is linear), nor is `2 3 = 1` (it would otherwise turn into `23 = 1`).

## Use as a library

Every function returns a `Solution` holding a value for programmatic use, the answer text and the steps:

```python
from mathsteps import linalg, discrete
from mathsteps.core import parse_matrix

res = linalg.determinant(parse_matrix("2 1 3; 0 -1 4; 1 2 5"))
res.value        # Fraction(-19, 1)
res.answer       # 'det = -19'
res.render()     # the full text of the solution

a, b, names = linalg.parse_system("x + y = 3; x - y = 1")
solution = linalg.solve_system(a, b, names).value
solution.status         # 'unique'
solution.evaluate()     # [Fraction(2, 1), Fraction(1, 1)]
```

## How it is verified

The repository has 63 tests using the standard `unittest`. The main idea: the result of each algorithm is compared with an **independent** method, not with a precomputed "correct" number.

| What the code computes | What the tests compare it with |
|---|---|
| determinant (Gaussian elimination) | a separately written cofactor expansion along a row |
| inverse matrix | `A·A⁻¹ = A⁻¹·A = E` |
| solution of a linear system | substitution into the original equations, including random values of free variables |
| rank | rank of the transpose; rank = n ⇔ det ≠ 0 |
| graph bipartiteness | brute force over all two-colourings |
| connected components | a separate implementation using a disjoint-set structure |
| Euler path and cycle | direct enumeration of walks |
| arrangements, combinations | counting with `itertools` |
| distance to a line | the foot of the perpendicular found by projection |

Random tests use a fixed seed, so they are reproducible. I also tested the tests themselves: I deliberately introduced typical bugs (a flipped sign, an off-by-one, a missing condition) and checked whether the tests fail. This exposed a weak check in the Euler path test, which was strengthened. One special case where replacing a condition does not change behaviour (the branch is already handled earlier) is, naturally, not noticed by the tests.

```bash
python -m unittest discover -s tests -v
```

## Limitations

- Only **linear** systems are solved; the parser rejects nonlinear equations.
- Graphs are simple and undirected, with no loops or multiple edges.
- The angle between vectors and the distance to a line are printed approximately (4 and 2 decimal places) when the result is irrational; all other results are exact.
- Lines in `line` and `dist` are in the plane.
- The tool was not optimised for large inputs (graphs with hundreds of vertices, 50×50 matrices): it targets textbook-size problems, and the step-by-step output is unreadable at such sizes anyway.

## Structure

```
mathsteps/
  core.py           Solution, fractions, formatting and matrix parsing
  linalg.py         Gauss–Jordan, linear systems, determinant, inverse, rank, equation parsing
  discrete.py       relations and graphs
  combinatorics.py  arrangements, combinations, permutations
  geometry.py       line, distance, angle, area
  cli.py            command line
tests/              unittest: test_linalg, test_discrete, test_misc
docs/examples.md    sample output (generated by running the commands)
```

## Ideas for development

- directed graphs, shortest paths in weighted graphs (Dijkstra);
- eigenvalues and eigenvectors (exact for rational roots);
- export of solutions to LaTeX;
- a "check my solution" mode: compare the user's steps with the reference ones.

## License

MIT, see [LICENSE](LICENSE).
