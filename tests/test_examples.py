"""The examples run and print what the README shows."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(name: str) -> list[str]:
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    done = subprocess.run([sys.executable, str(ROOT / "examples" / name)], capture_output=True, text=True,
                          check=True, env=env)
    return done.stdout.splitlines()


def test_figure1():
    out = run("figure1.py")
    assert out[0] == "image barcode        [[2.0, inf], [3.0, 7.0], [5.0, 6.0]]"
    assert out[1] == "f_U                  [4, 2, 3, 6, 5, 5, 7, 3, 3, 4, 6, 6, 6, 6]"
    assert out[2] == "barcode of f_U       [[2.0, inf], [3.0, 7.0], [5.0, 6.0]]"
    assert all(line.endswith("contains it: True") for line in out[3:6])
    assert out[6:] == ["bars longer than 0: 3", "bars longer than 1: 2", "bars longer than 2: 2", "bars longer than 4: 1"]


def test_certified_terrain():
    rows = [line.split() for line in run("certified_terrain.py")[4:]]
    assert rows[0] == ["0.01", "321", "5", "4", "239", "7", "5"]
    assert rows[-1] == ["0.2", "3", "3", "3", "3", "3", "3"]
