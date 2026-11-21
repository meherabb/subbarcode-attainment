"""Run the experiment notebook headless and keep the executed copy.

    python scripts/run_notebook.py --profile QUICK            # every section at reduced size, no downloads
    python scripts/run_notebook.py --profile FULL             # the sizes of the paper (about 72 min on 4 cores)
    python scripts/run_notebook.py --profile FULL --results runs/full

Results go to runs/<profile>/ by default. The archived run in results/ is never overwritten.
Each finished configuration is checkpointed, so an interrupted run resumes when started again
with the same --results folder.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebook" / "socg27_experiments.ipynb"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Run notebook/socg27_experiments.ipynb headless.")
    ap.add_argument("--profile", choices=["QUICK", "FULL"], default="QUICK")
    ap.add_argument("--results", type=Path, help="output folder (default: runs/<profile>)")
    ap.add_argument("--notebook", type=Path, default=NOTEBOOK)
    args = ap.parse_args(argv)

    import nbformat
    from nbclient import NotebookClient
    from nbclient.exceptions import CellExecutionError

    results = (args.results or ROOT / "runs" / args.profile.lower()).resolve()
    if results == (ROOT / "results").resolve():
        print("results/ holds the archived run; choose another folder with --results", file=sys.stderr)
        return 2
    results.mkdir(parents=True, exist_ok=True)
    os.environ["SOCG_PROFILE"] = args.profile
    os.environ["SOCG_RESULTS"] = str(results)

    nb = nbformat.read(args.notebook, as_version=4)
    for cell in nb.cells:
        if cell.cell_type == "code":
            cell.outputs, cell.execution_count = [], None
    out = results / "socg27_experiments.executed.ipynb"
    client = NotebookClient(nb, timeout=None, kernel_name="python3", resources={"metadata": {"path": str(ROOT)}})

    t0, section = time.perf_counter(), "setup"
    print(f"profile {args.profile} -> {results}", flush=True)
    with client.setup_kernel():
        for index, cell in enumerate(nb.cells):
            if cell.cell_type == "markdown":
                first = cell.source.strip().splitlines()[0] if cell.source.strip() else ""
                if first.startswith("## "):
                    section = first[3:].strip()
                    print(f"  {time.perf_counter() - t0:7.1f} s  {section}", flush=True)
                continue
            try:
                client.execute_cell(cell, index)
            except CellExecutionError as err:
                nbformat.write(nb, out)
                print(f"\nfailed in section '{section}' (cell {index}); partial notebook: {out}\n{err}", file=sys.stderr)
                return 1
    nbformat.write(nb, out)
    print(f"done in {(time.perf_counter() - t0) / 60:.1f} min\nresults:  {results}\nnotebook: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
