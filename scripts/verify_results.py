"""Verify that results/ is byte-for-byte the archived run.

Two independent checks:
  1. every file listed in results/SHA256SUMS (written when the repository was packaged) is
     present and unchanged, and no other file was added;
  2. every checksum the run recorded itself in results/logs/reproducibility_report.json
     still matches.

    python scripts/verify_results.py [RESULTS_DIR]
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGING = {"SHA256SUMS", "README.md"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main(argv: list[str]) -> int:
    folder = Path(argv[1]) if len(argv) > 1 else ROOT / "results"
    problems = []

    listed = {}
    for line in (folder / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, rel = line.split(maxsplit=1)
        listed[rel] = digest
    unchanged = 0
    for rel, digest in listed.items():
        p = folder / rel
        if not p.is_file():
            problems.append(f"missing   {rel}")
        elif sha256(p) != digest:
            problems.append(f"changed   {rel}")
        else:
            unchanged += 1
    present = {p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()}
    extra = sorted(present - set(listed) - PACKAGING)
    problems += [f"added     {rel}" for rel in extra]

    report = json.loads((folder / "logs" / "reproducibility_report.json").read_text(encoding="utf-8"))
    recorded = report["checksums"]
    matching = 0
    for rel, digest in recorded.items():
        p = folder / rel
        if p.is_file() and sha256(p) == digest:
            matching += 1
        else:
            problems.append(f"differs from the run's own record   {rel}")

    for line in problems:
        print(line)
    print(f"SHA256SUMS      {unchanged} of {len(listed)} files unchanged, "
          + (f"{len(extra)} added" if extra else "none added"))
    print(f"run checksums   {matching} of {len(recorded)} match logs/reproducibility_report.json")
    if problems:
        print(f"FAILED: {len(problems)} problems")
        return 1
    print(f"OK: results/ is the archived run (profile {report['profile']}, configuration {report['config_hash']})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
