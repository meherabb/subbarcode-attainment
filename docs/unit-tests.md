# The unit tests of the notebook

Section 5 of the notebook runs 33 tests before any experiment, and the run records them in
[`results/tables/unit_tests.csv`](../results/tables/unit_tests.csv). All 33 passed in the reported run.
They test the compiled kernels and helpers that the experiments use; the `subbarcode` package has its own
test suite in [`tests/`](../tests).

The test names were fixed while the degree-0 sweep was developed. The references in four of them, `Prop.3(b)`
(T02), `Cor.2` (T09), `Prop.3` (T14) and `Lemma 1` (T17), point to an internal draft and not to the numbered
results of the paper; the table below says what each test checks in the terms of the paper. The names are
left unchanged because the notebook is the code of the reported run (see `make fingerprint`).

## Notation

For a box (ℓ, u) on a graph and τ ≥ 0, the notebook's sweep (`certify_graph`) returns

- **T<sub>τ</sub>**, the number of bars longer than τ that every function in the box has. T25 checks that it
  is the number of bars of Bar<sub>0</sub>(u ≥ ℓ) longer than τ;
- **f\***, a function in the box with exactly T<sub>τ</sub> bars longer than τ.

**N<sub>τ</sub>(f)** is the number of bars of Bar<sub>0</sub>(f) longer than τ. The **rank certificate** is the
largest rank of the image module over an interval longer than τ, that is, the most that the rank invariant
alone can certify. It is never larger than T<sub>τ</sub> (T14), and it can be much smaller (T03).

## The tests

| Test | What it checks | Instances |
|---|---|---|
| T01 | Degree-0 persistence on a known example: the path with values 0, 2, 1, 3 has the diagram {(0, ∞), (1, 2)} | 1 |
| T02 | The staircase with three basins and exact values: T<sub>1</sub> = N<sub>1</sub> = 3, while the rank certificate is 2 | 1 |
| T03 | Staircases with K + 1 basins, K = 1, …, 8: T<sub>1</sub> = K + 1, while the rank certificate stays at 2 | 8 |
| T04 | Combs with K teeth, K = 2, …, 20: T<sub>0.5</sub> = 1, although typical functions in the box have many basins | 19 |
| T05 | Nested pockets, D = 1, …, 14, which give a merge forest of depth D: T<sub>1</sub> = D + 1 | 14 |
| T06 | A degenerate box, ℓ = u = f: T<sub>τ</sub> = N<sub>τ</sub>(f) | 500 |
| T07 | A symmetric box f̂ ± δ: T<sub>τ</sub> is the number of bars of f̂ longer than τ + 2δ, the ε-smoothing identity of Section 7 | 500 |
| T08 | T<sub>0</sub> equals the number of mandatory minima of Günther, Salmon and Tierny (Section 7) | 1,000 |
| T09 | Along the merge forest of the sweep, the largest τ at which a node is certified never decreases towards the root | 500 |
| T09 | The whole curve τ ↦ T<sub>τ</sub>, read off these values in one pass, equals T<sub>τ</sub> recomputed at 40 values of τ | 500 |
| T10 | The general graph kernel and the grid kernel give the same T<sub>τ</sub> and f\* on 4-, 6- and 8-connected grids | 180 |
| T10b | The same for plain degree-0 persistence | 180 |
| T11 | The compiled kernel agrees with a direct transcription in exact rational arithmetic, in T<sub>τ</sub> and f\* | 200 |
| T12 | T<sub>τ</sub> does not change when a constant is added, when values and τ are multiplied by a positive integer, or when the vertices are relabelled | 300 |
| T13 | Shrinking the box never decreases T<sub>τ</sub>, and T<sub>τ</sub> never increases with τ | 300 |
| T14 | The rank certificate computed by a sweep equals brute force over all pairs of values | 400 |
| T14 | The rank certificate is at most T<sub>τ</sub> | 400 |
| T15 | Agreement with priority-flood depression filling on random terrains: the filled terrain has no interior pits, and the number of depressions deeper than τ is at most the number of pits with persistence greater than τ | 100 |
| T16 | A box with ℓ > u at some vertex is rejected | 1 |
| T17 | For functions f in the box, the image bars longer than τ match injectively to bars of f that contain them, which is Theorem 1 for long bars; checked by an explicit injection and by a maximum matching | 900 |
| T18 | A variant that tests lengths after the sweep instead of during it is a valid lower bound, and exact on staircases | 308 |
| T19 | The exact predicate for a + b < c, used in the length test, agrees with rational arithmetic, near-ties included; plain floating point is wrong in 3,101 of the cases | 20,000 |
| T20 | N<sub>0</sub>(f) is the number of minimal plateaus, the local minima of Gray, Kammer, Löffler and Silveira | 1,000 |
| T21 | The rank certificate equals a formula on the merge forest | 1,000 |
| T22 | The largest set of pairwise intersecting windows is at most the rank certificate, which is at most T<sub>τ</sub> | 1,000 |
| T23 | The implicit-neighbour kernels on 2-D grids (4-, 6-, 8-connected) and 3-D grids (6-, 26-connected) equal the general kernel, for T<sub>τ</sub>, f\* and persistence | 150 |
| T24 | The kernel that relabels vertices in sweep order, which is timed in Figure 3a, equals the original kernel | 80 |
| T25 | The number of image bars longer than τ is T<sub>τ</sub>, for five values of τ | 500 |
| T26 | f<sub>U</sub> lies in the box and Bar<sub>0</sub>(f<sub>U</sub>) = Bar<sub>0</sub>(u ≥ ℓ) bar for bar, with ties and with real values (Theorem 5) | 600 |
| T27 | N<sub>τ</sub>(f<sub>U</sub>) = T<sub>τ</sub> for τ = 0, 1, …, 12: one function attains every count (Theorem 5 and Lemma 2) | 400 |
| T28 | The image barcode is a sub-barcode of Bar<sub>0</sub>(f) for functions f in the box (Theorem 1, reproduced) | 1,800 |
| T29 | The greedy sub-barcode matching is maximum, compared with augmenting paths | 2,000 |
| T30 | Widening the box gives a sub-barcode of the image barcode of the narrower box | 500 |

Tests whose outcome depends on exact arithmetic use integer data, and every random instance is drawn from a
seed derived from the master seed of the run.
