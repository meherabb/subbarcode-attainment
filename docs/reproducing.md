# Reproducing the experiments

There are three levels, from seconds to the full run of the paper. All commands run from the root of the
repository; each `make` target is a single command, given below for systems without `make`.

## Environment

The reported run used Python 3.13 with the versions pinned in [`requirements.txt`](../requirements.txt):
NumPy 2.1.3, SciPy 1.16.3, pandas 2.3.3, Numba 0.61.2, Matplotlib 3.10.0, h5py 3.14.0 and hdf5plugin 7.1.0.

```bash
python3.13 -m venv .venv
source .venv/bin/activate
make install          # python -m pip install -r requirements.txt && python -m pip install -e . --no-deps
```

The notebook needs Linux or macOS, because it measures memory with the standard `resource` module; on
Windows, use WSL. The `subbarcode` package and the checks of level 1 need only NumPy and run on Python 3.11,
3.12 and 3.13 on any system.

## Level 1: check the archived run (seconds, no downloads)

```bash
make check
```

runs four independent checks:

| Check | Command | What it shows |
|---|---|---|
| archive | `python scripts/verify_results.py` | every file in `results/` matches `results/SHA256SUMS`, no file was added, and the 60 checksums that the run recorded itself in `logs/reproducibility_report.json` still match |
| claims | `python scripts/check_claims.py` | each of the 95 numbers quoted in the paper is recomputed from `results/` and compared with the value printed in the paper; the table is in [claims.md](claims.md) |
| code | `python scripts/notebook_fingerprint.py` | the code cells of the notebook parse to the same syntax trees, cell by cell, as the code of the reported run; comments, docstrings, formatting and Markdown text are not part of this fingerprint |
| library | `python -m pytest` | the `subbarcode` package against brute-force rank computations over GF(2), the examples, and the checks above as tests |

The claim checker and the archive check use only the standard library.

## Level 2: run every section at reduced size (about a minute, no downloads)

```bash
make quick            # python scripts/run_notebook.py --profile QUICK --results runs/quick
```

The `QUICK` profile runs all 24 sections of the notebook on reduced sizes and skips the SDRBench fields,
so the entry for real compression in `runs/quick/logs/status.json` is `NOT EXECUTED` by design and every
other entry is `EXECUTED`. The numbers differ from the paper because the instances are
smaller. The executed notebook is saved as `runs/quick/socg27_experiments.executed.ipynb`.

## Level 3: the run of the paper (about 72 minutes on 4 cores)

```bash
make full             # python scripts/run_notebook.py --profile FULL --results runs/full
```

The `FULL` profile downloads about 1.5 GB of SDRBench fields (four CESM-ATM fields and one Hurricane-ISABEL
field); [`results/data/manifest.json`](../results/data/manifest.json) records the size and SHA-256 of each
field that the reported run used. The reported run took 71.7 minutes on a Kaggle notebook machine with 4
logical CPUs and 33.7 GB of RAM, with every numerical library limited to one thread; its peak resident
memory in the scaling section was 5.8 GB (`results/scaling.csv`).

To compare a new run with the archived one:

```bash
python scripts/check_claims.py --results runs/full
```

Every count, decision and certificate is determined by the configuration and the seeds. Timings are not:
expect the rows about running times, the machine and the length of the session to differ on other hardware.
We ran the `QUICK` profile twice on one machine; all 82 output files agreed except the timings, the
quantities computed from them, and the creation dates inside the PDF figures.

### Interrupted runs

Each finished configuration is written to `<results>/checkpoints/` as one JSON line, so starting the same
command again with the same `--results` folder resumes where the run stopped. Start from an empty folder
after changing the configuration. `scripts/run_notebook.py` refuses to write into `results/`, which holds
the reported run.

### Running the notebook interactively

The notebook reads two environment variables, `SOCG_PROFILE` (`FULL` or `QUICK`) and `SOCG_RESULTS` (the
output folder), so it can also be run in Jupyter:

```bash
SOCG_PROFILE=QUICK SOCG_RESULTS=runs/quick jupyter lab notebook/socg27_experiments.ipynb
```

Jupyter itself is not in `requirements.txt`; install it with `python -m pip install jupyterlab`.

## Figures and tables

```bash
make figures          # python results/code/make_figures.py results build/figures
```

redraws Figures 1–4 from the archived tables into `build/figures/`. Tables 2 and 3 are in
`results/tables/` as CSV and as the LaTeX rows of the paper.

## The graphics of the README

```bash
make docs             # python scripts/check_claims.py --write docs/claims.md && python scripts/build_assets.py
```

regenerates [claims.md](claims.md) and everything in [`assets/`](assets). The plots are computed with the
`subbarcode` package, the badges and the diagram read their numbers from the repository, and the terminal
recording is the output of `make check` at the time the script runs.
