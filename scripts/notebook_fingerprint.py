"""Fingerprint the executable code of the experiment notebook.

The fingerprint is a SHA-256 over a canonical form of the abstract syntax tree of every
code cell, with comments and docstrings removed. Edits to markdown, comments or
docstrings leave it unchanged; any change to executable code changes it. The canonical
form ignores empty and unset AST fields, so the value is the same on Python 3.11-3.13.

    python scripts/notebook_fingerprint.py           # compare with the reported run
    python scripts/notebook_fingerprint.py --cells   # also list one hash per code cell
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebook" / "socg27_experiments.ipynb"

# Fingerprint of the code that produced results/ (profile FULL, configuration 8f4b785c7a4a).
REPORTED_RUN = "b1f881bad12004cde9d5162bc66d5774115dffad3ee36a40ba59619dbd50f04b"

_DOC_OWNERS = (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


def _strip_docstrings(tree: ast.AST) -> ast.AST:
    for node in ast.walk(tree):
        if isinstance(node, _DOC_OWNERS) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                node.body = node.body[1:] or [ast.Pass()]
    return tree


def _canon(x) -> str:
    if isinstance(x, ast.AST):
        parts = []
        for name in sorted(x._fields):
            value = getattr(x, name, None)
            if value is None or value == [] or value == ():
                continue
            parts.append(f"{name}={_canon(value)}")
        return f"{type(x).__name__}({','.join(parts)})"
    if isinstance(x, (list, tuple)):
        return "[" + ",".join(_canon(v) for v in x) + "]"
    return f"{type(x).__name__}:{x!r}"


def cell_hashes(path: Path = NOTEBOOK) -> list[tuple[int, str]]:
    nb = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for i, cell in enumerate(nb["cells"]):
        if cell["cell_type"] != "code":
            continue
        src = "".join(cell["source"])
        tree = _strip_docstrings(ast.parse(src))
        out.append((i, hashlib.sha256(_canon(tree).encode()).hexdigest()))
    return out


def fingerprint(path: Path = NOTEBOOK) -> str:
    h = hashlib.sha256()
    for i, cell_hash in cell_hashes(path):
        h.update(f"{i}:{cell_hash}\n".encode())
    return h.hexdigest()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("notebook", nargs="?", type=Path, default=NOTEBOOK)
    ap.add_argument("--cells", action="store_true", help="list the hash of every code cell")
    args = ap.parse_args(argv)
    if args.cells:
        for i, cell_hash in cell_hashes(args.notebook):
            print(f"cell {i:2d}  {cell_hash[:16]}")
    fp = fingerprint(args.notebook)
    ok = fp == REPORTED_RUN
    print(f"code fingerprint  {fp}")
    print(f"reported run      {REPORTED_RUN}")
    print("OK: the executable code is the code of the reported run" if ok else "DIFFERENT: the executable code was changed")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
