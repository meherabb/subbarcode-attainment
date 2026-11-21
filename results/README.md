# The reported run

Everything in this folder was written by [`notebook/socg27_experiments.ipynb`](../notebook/socg27_experiments.ipynb) in a single session:

| | |
|---|---|
| profile | `FULL` |
| configuration hash | `8f4b785c7a4a` |
| master seed | `20260925` |
| wall time | 71.7 minutes |
| machine | x86-64, 4 logical CPUs, 33.7 GB of RAM, one thread |
| software | Python 3.13, NumPy 2.1.3, SciPy 1.16.3, pandas 2.3.3, Numba 0.61.2, Matplotlib 3.10.0, hdf5plugin 7.1.0 |
| status | 33 of 33 unit tests passed, every section `EXECUTED`, no validation warnings |

The files are exactly as the run wrote them. Two files were added when the repository was packaged: this README and `SHA256SUMS`. Run `make verify` to check every file against `SHA256SUMS` and against the checksums that the run recorded itself in `logs/reproducibility_report.json`.

## Layout

| Path | Contents |
|---|---|
| `paper_numbers.md`, `paper_numbers.json` | every number quoted in the paper, recomputed from the run and grouped by the sentence or table it belongs to |
| `*.csv`, `results.json` | top-level exports, which the figure script reads |
| `tables/` | Tables 2 and 3 as CSV and LaTeX rows, the census by decision method, and the 33 unit-test results |
| `figures/` | Figures 1–4 of the paper as vector PDFs |
| `raw/`, `processed/` | per-instance results and their summaries |
| `checkpoints/` | one JSON line per finished configuration; a rerun pointed at this folder resumes instead of recomputing |
| `configs/configuration.json` | the complete configuration; its SHA-256 prefix is the configuration hash |
| `data/manifest.json` | the five SDRBench fields used, with their sizes and SHA-256 checksums |
| `logs/` | run log, section statuses, validation, reproducibility report, anonymity scan |
| `code/` | `make_figures.py`, which draws Figures 1–4 from the tables, and the notebook-scrub utility, both as written by the run |

## Redrawing the figures

```bash
python results/code/make_figures.py results build/figures
```

Figures 1 and 2 are computed inside the script from the small exact examples of the paper. Figures 3 and 4 are drawn from `p2_memory_hierarchy.csv`, `degree1_fast_timing.csv`, `compression.csv`, `theorem_c.csv` and `raw/v5_degree1_fast.csv`.

## Names inside the files

Some file and checkpoint names (`v3_optimality`, `p2_scaling`, `v5_theorem_c`, ...) keep the identifiers of the experiments that produced them. [`docs/paper-map.md`](../docs/paper-map.md) links each file to the result of the paper it supports. The heading "Middle degrees (new theorem)" in `paper_numbers.md` refers to Theorem 21.
