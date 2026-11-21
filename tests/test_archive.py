"""The archived run: checksums, every number of the paper, the notebook code and the figures."""
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_results_are_the_archived_run():
    assert _script("verify_results").main(["verify_results", str(ROOT / "results")]) == 0


def test_every_number_of_the_paper_matches_the_run():
    claims = _script("check_claims")
    rows = claims.claims(claims.Run(ROOT / "results"))
    assert len(rows) >= 90
    assert [row for row in rows if row[2] != row[3]] == []


def test_claim_checker_notices_a_wrong_number():
    claims = _script("check_claims")
    run = claims.Run(ROOT / "results")
    run.section("Compression")["overcount_runs"] += 1
    assert any(row[2] != row[3] for row in claims.claims(run))


def test_claims_page_is_up_to_date():
    claims = _script("check_claims")
    rendered = claims.render_markdown(claims.claims(claims.Run(ROOT / "results")))
    assert (ROOT / "docs" / "claims.md").read_text(encoding="utf-8") == rendered


def test_notebook_code_is_the_code_of_the_run():
    fingerprint = _script("notebook_fingerprint")
    assert fingerprint.fingerprint() == fingerprint.REPORTED_RUN


def test_figures_are_redrawn_from_the_tables(tmp_path):
    pytest.importorskip("matplotlib")
    pytest.importorskip("pandas")
    subprocess.run([sys.executable, str(ROOT / "results" / "code" / "make_figures.py"), str(ROOT / "results"), str(tmp_path)],
                   check=True, capture_output=True)
    names = sorted(p.name for p in tmp_path.glob("*.pdf"))
    assert names == ["fig1_fU_path.pdf", "fig2_certificate_D.pdf", "fig3_experiments.pdf", "fig4_surface_checks.pdf"]
