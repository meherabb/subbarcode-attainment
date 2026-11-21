# From the paper to the code

For every result of the paper with a computational part: the section of
[`notebook/socg27_experiments.ipynb`](../notebook/socg27_experiments.ipynb) that checks it, the files in
[`results/`](../results) that hold the outcome of the reported run, and the function of the `subbarcode`
package that implements the construction, where there is one. Section numbers (§) refer to the notebook.
Every number that the paper quotes is recomputed from these files by `make claims`; [claims.md](claims.md)
lists all of them.

## Theorems, lemmas and examples

| Paper | What is checked | Notebook | Files in `results/` | `subbarcode` |
|---|---|---|---|---|
| Theorem 1 | The image barcode is a sub-barcode of the barcode of every function in the box, reproduced on sampled functions | §5, tests T17, T28, T30 | `tables/unit_tests.csv` | `is_sub_barcode` |
| Lemma 2 | One function minimises the count of bars in every region closed under enlarging intervals: 3,000 persistence regions and 4,000 quadrants, against exhaustive minimisation | §6 | `optimality_regions.csv` | |
| Theorem 5 | f<sub>U</sub> lies in the box and Bar<sub>0</sub>(f<sub>U</sub>) = Bar<sub>0</sub>(u ≥ ℓ) bar for bar, on 100,000 random boxes with up to 225 vertices | §4, §5 (T25–T27), §6 | `optimality.csv` | `reconstruct_erosion`, `image_barcode0` |
| Theorem 5, related work | The number of image bars equals the minimum number of local minima (500 instances) and the number of mandatory minima (1,000) | §5 (T08, T20), §6 | `raw/gkls_objective.csv`, `tables/unit_tests.csv` | `certified_count` |
| Theorem 8 (d = 2) | f<sub>D</sub>, computed on a sphere that contains the complex, attains Bar<sub>1</sub>(u ≥ ℓ) on 1,500 boxes over five planar families; f<sub>D</sub> computed on the complex itself does not always | §9 | `degree1_planar.csv` | `attaining_function_grid`, `image_barcode_grid` |
| Theorem 8 (d = 3), Lemma 4 | Voids (degree 2) on 500 boxes on coned 3-D Freudenthal grids up to 5×5×5, and the padding lemma on each | §18 | `grid3d_degree2.csv`, `raw/grid3d_degree2.csv` | `image_barcode_grid` |
| Theorem 10 | Finite bars and counts of long bars on 7,199 boxes over 18 surface families | §13 | `theorem_c.csv`, `raw/v5_theorem_c.csv` | |
| Theorem 11, Figure 2 | The Möbius band of Figure 2 and the punctured torus of Appendix B are not attained, nor are five closed surfaces built from them; decided by complete enumeration | §10 | `degree1_transfers.csv`, `paper_numbers.json` | |
| Lemma 12, Theorem 13 | Deciding attainment with boundary (by f<sub>D</sub>) and on closed surfaces (by f<sub>D</sub> and at most n modifications of it) | §16 | `theorem13.csv`, `raw/theorem13_checks.csv` | |
| Corollary 14 | The near-linear degree-1 bound on terrains and tori up to 2.56·10⁶ vertices; exact agreement with the rank-invariant computation on 42 small grids | §15 | `degree1_fast_timing.csv`, `raw/v5_degree1_fast.csv` | |
| Proposition 15 | Graphs attain in degree 1, by u, on 600 graphs | §14 | `results.json`, `paper_numbers.json` | |
| Lemma 16 | The counts at KC vertices on 6,000 functions over 1,500 complexes | §8 | `results.json`, `paper_numbers.json` | |
| Examples 17–19 | Image barcodes and non-attainment, by complete enumeration | §10 | `paper_numbers.json` | |
| Example 20 | A count gap on a complex without KC vertices | §10 | `example20_grid.csv` | |
| Theorem 21 | Middle degrees: the Möbius band in a 3-sphere and in a 3-ball, Example 18 in a 3-sphere, and both suspended into S⁴; degree 1 on 2,000 boxes on 3-D grids | §17, §18 | `middle_degrees.csv`, `grid3d_degree1_census.csv` | |

## Tables and figures

| Paper | Notebook | Files in `results/` |
|---|---|---|
| Table 1 | (summary of the theorems) | |
| Table 2, degree-1 paragraph of Section 7 | §7 (self-checks of the exact machinery), §11, §12 | `tables/table2_census.csv`, `tables/table2_census.tex`, `degree1_census.csv`, `degree1_census_instances.csv`, `tables/census_by_decision_method.csv`, `raw/degree1_exact.json` |
| Table 3, compression paragraph of Section 7, Appendix D | §20 | `tables/table3_compression.csv`, `tables/table3_compression.tex`, `compression.csv`, `compression_uniform_baseline.csv`, `processed/compression_summary.csv`, `data/manifest.json` |
| Figure 1 | §22 | `figures/fig1_fU_path.pdf` |
| Figure 2 | §22 | `figures/fig2_certificate_D.pdf` |
| Figure 3a, scaling paragraph | §19 | `figures/fig3_experiments.pdf`, `p2_memory_hierarchy.csv`, `scaling.csv`, `raw/p2_scaling_runs.csv`, `processed/scaling_v2.csv` |
| Figure 3b, Figure 4b | §15 | `figures/fig3_experiments.pdf`, `figures/fig4_surface_checks.pdf`, `degree1_fast_timing.csv`, `raw/v5_degree1_fast.csv` |
| Figure 3c | §20 | `figures/fig3_experiments.pdf`, `compression.csv` |
| Figure 4a | §13 | `figures/fig4_surface_checks.pdf`, `theorem_c.csv` |
| Setup of Section 7, Appendix D | §1, §2, §24 | `configs/configuration.json`, `logs/reproducibility_report.json` |

The figures are drawn by `results/code/make_figures.py` from the tables above; `make figures` redraws them
into `build/figures/`.

## The `subbarcode` package

The package is a separate, plain implementation of the constructions of Sections 3 and 4 of the paper. It
does not use Numba and shares no code with the notebook. Its tests compare it with rank invariants of
persistence modules computed by brute force over GF(2) in [`tests/oracle.py`](../tests/oracle.py), and with
the run on the example of Figure 1.

| Function | Computes | Paper |
|---|---|---|
| `reconstruct_erosion(edges, lower, upper)` | f<sub>U</sub>, the smallest function in the box that attains Bar<sub>0</sub>(u ≥ ℓ) | Theorem 5 |
| `reconstruct_dilation(edges, lower, upper)` | f<sub>D</sub>(ℓ, u) = −f<sub>U</sub>(−u, −ℓ) | Section 3 |
| `image_barcode0(edges, lower, upper)` | Bar<sub>0</sub>(u ≥ ℓ) on any graph | Theorem 5 |
| `certified_count(edges, lower, upper, tau)` | the number of bars longer than τ that every function in the box has | Theorem 1, Lemma 2 |
| `image_barcode_grid(lower, upper)` | Bar<sub>d−1</sub>(u ≥ ℓ) on a Freudenthal-triangulated 2-D or 3-D grid | Theorem 8 |
| `attaining_function_grid(lower, upper)` | f<sub>D</sub> on the grid, which attains it | Theorem 8 |
| `absolute_box(values, error_bound)` | the box of an absolute error bound | Section 7 |
| `barcode0`, `count_longer`, `is_sub_barcode` | degree-0 barcodes, counts of long bars, sub-barcodes | Section 2 |
| `path_edges`, `grid_edges`, `grid_simplices`, `grid_boundary` | paths and Freudenthal grids | |

## Names inside the files

Some file and checkpoint names keep the identifiers of the experiments that produced them:

| Identifier | Result of the paper |
|---|---|
| `v3_optimality`, `optimality_regions` | Theorem 5 and Lemma 2 |
| `p1_gkls_objective` | Section 7, minimum number of local minima |
| `v4_degree1_selfcheck` | the self-checks of the exact degree-1 machinery, among them the independent enumeration on 60 instances |
| `degree1_exact` | the exact degree-1 results of §7–§12 in one file |
| `v4_degree1_kclemma` | Lemma 16 |
| `v4_degree1_planar` | Theorem 8, d = 2 |
| `v4_degree1_census` | Table 2 |
| `v5_theorem_c`, `theorem_c` | Theorem 10 |
| `v5_prop_g` | Proposition 15 |
| `v5_degree1_fast` | Corollary 14 |
| `v6_theorem13` | Lemma 12 and Theorem 13 |
| `v6_grid3d_*` | Theorem 8 with d = 3, and degree 1 on 3-D grids for Theorem 21 |
| `p2_scaling`, `p2_density`, `p2_tau`, `v4_p2_memory` | Figure 3a and the scaling paragraph |
| `compression_v6` | Table 3 and Figure 3c |

In `paper_numbers.md` and `paper_numbers.json`, the group "Middle degrees (new theorem)" holds the numbers
of Theorem 21. The names of the unit tests are explained in [unit-tests.md](unit-tests.md).
