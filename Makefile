# Run `make help` for a short description of every target.
PYTHON ?= python

.PHONY: help install test verify claims fingerprint check quick full figures docs clean

help:  ## list the targets
	@grep -E "^[a-z]+:.*## " $(MAKEFILE_LIST) | sed -E "s/:.*## /\t/" | expand -t 14

install:  ## install the pinned environment of the reported run and the subbarcode package
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m pip install -e . --no-deps

test:  ## the test suite: the library against brute force, the examples, the archived run
	$(PYTHON) -m pytest

verify:  ## results/ is byte-for-byte the archived run
	$(PYTHON) scripts/verify_results.py

claims:  ## every number quoted in the paper, recomputed from results/
	$(PYTHON) scripts/check_claims.py

fingerprint:  ## the notebook runs the code of the reported run
	$(PYTHON) scripts/notebook_fingerprint.py

check:  ## verify, claims, fingerprint and test, with short output (seconds, no downloads)
	$(PYTHON) scripts/verify_results.py
	$(PYTHON) scripts/check_claims.py --quiet
	$(PYTHON) scripts/notebook_fingerprint.py
	$(PYTHON) -m pytest

quick:  ## run every section of the notebook at reduced size into runs/quick
	$(PYTHON) scripts/run_notebook.py --profile QUICK --results runs/quick

full:  ## rerun the paper into runs/full (about 72 minutes on 4 cores, 1.5 GB download)
	$(PYTHON) scripts/run_notebook.py --profile FULL --results runs/full

figures:  ## redraw Figures 1-4 from the archived tables into build/figures
	$(PYTHON) results/code/make_figures.py results build/figures

docs:  ## regenerate docs/claims.md and the README graphics
	$(PYTHON) scripts/check_claims.py --write docs/claims.md
	$(PYTHON) scripts/build_assets.py

clean:  ## remove build/ and runs/
	rm -rf build runs .pytest_cache
