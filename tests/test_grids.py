"""Theorem 8 on Freudenthal-triangulated grids: degree 1 for 2-D boxes and degree 2 for 3-D boxes."""
import itertools

import numpy as np
import pytest

import subbarcode as sb
from oracle import SimplicialComplex, bars_rank_function, critical_values, image_rank_function


def _complex(shape):
    n = int(np.prod(shape))
    return SimplicialComplex(n, [tuple(s) for s in sb.grid_simplices(shape)])


@pytest.mark.parametrize("shape", [(2, 2), (3, 4), (4, 3), (2, 2, 2), (3, 3, 3)])
def test_grid_triangulation(shape):
    """The simplices have the grid edges as their 1-skeleton, and the coned grid is a sphere."""
    d = len(shape)
    simp = sb.grid_simplices(shape)
    skeleton = {tuple(sorted(e)) for s in simp for e in itertools.combinations(s.tolist(), 2)}
    edges = {tuple(sorted(e)) for e in sb.grid_edges(shape, 6 if d == 2 else 14).tolist()}
    assert skeleton == edges
    n = int(np.prod(shape))
    bnd = set(sb.grid_boundary(shape).tolist())
    faces = {k: set() for k in range(d + 1)}
    for s in simp.tolist():
        for k in range(d + 1):
            faces[k].update(itertools.combinations(s, k + 1))
    # boundary faces lie in exactly one top simplex; coning them gives the sphere
    count = {}
    for s in simp.tolist():
        for f in itertools.combinations(s, d):
            count[f] = count.get(f, 0) + 1
    boundary = [f for f, c in count.items() if c == 1]
    assert {v for f in boundary for v in f} == bnd
    bfaces = {k: set() for k in range(d)}
    for f in boundary:
        for k in range(d):
            bfaces[k].update(itertools.combinations(f, k + 1))
    chi_k = sum((-1) ** k * len(faces[k]) for k in range(d + 1))
    chi_boundary = sum((-1) ** k * len(bfaces[k]) for k in range(d))
    assert chi_k == 1                                   # a d-ball
    assert chi_boundary == 1 + (-1) ** (d - 1)          # its boundary, a (d-1)-sphere
    assert chi_k + 1 - chi_boundary == 1 + (-1) ** d    # K with its boundary coned: a d-sphere
    assert len(faces[0]) == n


@pytest.mark.parametrize("seed", range(40))
def test_theorem8_degree1_on_2d_grids(seed):
    """Bar_1(u >= l) from f_D on the coned grid has the rank function of the image module on the grid."""
    rng = np.random.default_rng(5000 + seed)
    shape = (int(rng.integers(2, 5)), int(rng.integers(2, 6)))
    lo = rng.integers(0, 8, size=shape).astype(float)
    hi = lo + rng.integers(0, 4, size=shape)
    cx = _complex(shape)
    vals = critical_values(lo, hi)
    image = sb.image_barcode_grid(lo, hi)
    assert bars_rank_function(image, vals) == image_rank_function(cx, lo, hi, 1, vals)
    # f_D attains: Bar_1(f_D) has the same rank function (Theorem 8)
    f_d = sb.attaining_function_grid(lo, hi)
    assert np.all(lo <= f_d) and np.all(f_d <= hi)
    vals_f = critical_values(lo, hi, f_d)
    assert image_rank_function(cx, f_d, f_d, 1, vals_f) == bars_rank_function(image, vals_f)


@pytest.mark.parametrize("seed", range(12))
def test_theorem8_degree2_on_3d_grids(seed):
    """Voids: the degree-2 image barcode of a 3-D box, against the rank invariant on the grid."""
    rng = np.random.default_rng(6000 + seed)
    shape = [(2, 2, 3), (2, 3, 3), (3, 3, 3)][seed % 3]
    lo = rng.integers(0, 6, size=shape).astype(float)
    if seed % 2 == 0 and shape == (3, 3, 3):
        lo[1, 1, 1] = 9.0                       # a raised interior vertex, so that a void occurs
    hi = lo + rng.integers(0, 3, size=shape)
    cx = _complex(shape)
    vals = critical_values(lo, hi)
    image = sb.image_barcode_grid(lo, hi)
    assert bars_rank_function(image, vals) == image_rank_function(cx, lo, hi, 2, vals)
    if shape == (3, 3, 3) and seed % 2 == 0:
        assert len(image) >= 1


def test_terrain_example():
    """A peak inside a lower ring: the ring closes a loop at 1, and the peak fills it at 9 (Theorem 8, d = 2)."""
    lo = np.full((5, 5), 5.0)
    lo[1:4, 1:4] = 1.0
    lo[2, 2] = 9.0
    assert sb.image_barcode_grid(lo, lo).tolist() == [[1.0, 9.0]]
    assert np.array_equal(sb.attaining_function_grid(lo, lo), lo)


def test_grid_validation():
    with pytest.raises(ValueError):
        sb.image_barcode_grid(np.zeros((1, 4)), np.zeros((1, 4)))
    with pytest.raises(ValueError):
        sb.grid_edges((3, 3), 5)
