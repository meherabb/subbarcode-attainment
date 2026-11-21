"""Degree 0 on graphs: Theorem 1, Lemma 2, Theorem 5 and the smoothing identity, against brute force."""
import itertools
import math

import numpy as np
import pytest

import subbarcode as sb
from oracle import (SimplicialComplex, as_multiset, bars_rank_function, critical_values, image_rank_function,
                    path_minimax, random_box, random_graph)

# The example of Figure 1, as printed by the reported run (results/logs/run_log.txt).
FIG1_LOWER = [4, 1, 3, 6, 2, 5, 7, 3, 1, 4, 6, 5, 2, 4]
FIG1_UPPER = [6, 2, 7, 8, 5, 6, 9, 7, 3, 8, 7, 9, 6, 6]
FIG1_FU = [4, 2, 3, 6, 5, 5, 7, 3, 3, 4, 6, 6, 6, 6]


def test_figure1_example():
    e = sb.path_edges(len(FIG1_LOWER))
    f_u = sb.reconstruct_erosion(e, FIG1_LOWER, FIG1_UPPER)
    assert f_u.tolist() == FIG1_FU
    assert as_multiset(sb.barcode0(e, FIG1_LOWER)) == [(1, 7), (1, math.inf), (2, 6), (2, 6)]
    assert as_multiset(sb.barcode0(e, FIG1_UPPER)) == [(2, math.inf), (3, 9), (5, 8), (6, 9), (7, 8)]
    assert as_multiset(sb.barcode0(e, f_u)) == [(2, math.inf), (3, 7), (5, 6)]
    assert as_multiset(sb.image_barcode0(e, FIG1_LOWER, FIG1_UPPER)) == [(2, math.inf), (3, 7), (5, 6)]


def test_barcode0_elder_rule_and_components():
    # two components; in the first, the later minimum dies where it meets the older one
    e = np.array([[0, 1], [1, 2], [3, 4]])
    f = [0.0, 3.0, 1.0, 5.0, 2.0]
    assert as_multiset(sb.barcode0(e, f)) == [(0, math.inf), (1, 3), (2, math.inf)]
    assert sb.barcode0(np.zeros((0, 2)), [1.0, 2.0]).tolist() == [[1.0, math.inf], [2.0, math.inf]]


@pytest.mark.parametrize("seed", range(40))
def test_reconstruction_matches_definition(seed):
    rng = np.random.default_rng(seed)
    n = int(rng.integers(1, 30))
    e = random_graph(rng, n, float(rng.uniform(0.05, 0.4)))
    lo, hi = random_box(rng, n, top=10, width=5)
    f_u = sb.reconstruct_erosion(e, lo, hi)
    assert np.array_equal(f_u, path_minimax(n, e, lo, hi))
    assert np.all(lo <= f_u) and np.all(f_u <= hi)
    f_d = sb.reconstruct_dilation(e, lo, hi)
    assert np.array_equal(f_d, -path_minimax(n, e, -hi, -lo))
    assert np.all(lo <= f_d) and np.all(f_d <= hi)


@pytest.mark.parametrize("seed", range(60))
def test_theorem5_image_barcode_equals_rank_invariant(seed):
    """Bar_0(f_U) has the rank function of the image module t -> im H_0(K[u<=t]) -> H_0(K[l<=t])."""
    rng = np.random.default_rng(1000 + seed)
    n = int(rng.integers(2, 11))
    e = random_graph(rng, n, float(rng.uniform(0.1, 0.6)))
    lo, hi = random_box(rng, n, top=6, width=3)
    cx = SimplicialComplex(n, [tuple(x) for x in e])
    vals = critical_values(lo, hi)
    image = sb.image_barcode0(e, lo, hi)
    assert bars_rank_function(image, vals) == image_rank_function(cx, lo, hi, 0, vals)


@pytest.mark.parametrize("seed", range(25))
def test_theorem5_fU_is_the_smallest_attaining_function(seed):
    """f_U attains, and every integer function in a small integer box that attains lies above f_U."""
    rng = np.random.default_rng(2000 + seed)
    n = int(rng.integers(2, 6))
    e = random_graph(rng, n, 0.5)
    lo, hi = random_box(rng, n, top=4, width=2)
    target = as_multiset(sb.image_barcode0(e, lo, hi))
    f_u = sb.reconstruct_erosion(e, lo, hi)
    attaining = []
    for vals in itertools.product(*[range(int(a), int(b) + 1) for a, b in zip(lo, hi)]):
        f = np.asarray(vals, float)
        if as_multiset(sb.barcode0(e, f)) == target:
            attaining.append(f)
    assert any(np.array_equal(f, f_u) for f in attaining)
    assert all(np.all(f >= f_u) for f in attaining)


@pytest.mark.parametrize("seed", range(40))
def test_theorem1_and_lemma2_for_sampled_functions(seed):
    """The image barcode is a sub-barcode of Bar_0(f) for every f in the box, so its counts are lower bounds."""
    rng = np.random.default_rng(3000 + seed)
    n = int(rng.integers(2, 25))
    e = random_graph(rng, n, float(rng.uniform(0.05, 0.4)))
    lo, hi = random_box(rng, n, top=12, width=6)
    image = sb.image_barcode0(e, lo, hi)
    taus = [0.0, 0.5, 1.0, 2.5, 4.0]
    for _ in range(10):
        f = lo + rng.random(n) * (hi - lo)
        bars = sb.barcode0(e, f)
        assert sb.is_sub_barcode(image, bars)
        for tau in taus:
            assert sb.count_longer(bars, tau) >= sb.count_longer(image, tau)
    f_u = sb.reconstruct_erosion(e, lo, hi)
    for tau in taus:
        assert sb.count_longer(sb.barcode0(e, f_u), tau) == sb.certified_count(e, lo, hi, tau)


@pytest.mark.parametrize("seed", range(20))
def test_absolute_box_is_eps_smoothing(seed):
    """For the box f +- eps the image barcode is Bar_0(f) shortened by eps at both ends (Section 7)."""
    rng = np.random.default_rng(4000 + seed)
    shape = (int(rng.integers(3, 12)), int(rng.integers(3, 12)))
    f = rng.integers(0, 40, size=shape).astype(float)
    eps = float(rng.integers(0, 4))
    e = sb.grid_edges(shape, 6)
    lo, hi = sb.absolute_box(f, eps)
    bars = sb.barcode0(e, f)
    expected = [(b + eps, d - eps) for b, d in bars if d - b > 2 * eps]
    assert as_multiset(sb.image_barcode0(e, lo, hi)) == as_multiset(expected)
    for tau in [0.5, 1.5, 3.5, 7.5]:
        assert sb.certified_count(e, lo, hi, tau) == sb.count_longer(bars, tau + 2 * eps)


def test_is_sub_barcode():
    assert sb.is_sub_barcode([(1, 2)], [(0, 3)])
    assert not sb.is_sub_barcode([(1, 2), (1, 2)], [(0, 3)])
    assert sb.is_sub_barcode([(1, 2), (1, 5)], [(0, 6), (1, 2)])
    assert not sb.is_sub_barcode([(0, math.inf)], [(0, 9)])
    assert sb.is_sub_barcode([], [])


def test_input_validation():
    with pytest.raises(ValueError):
        sb.reconstruct_erosion([[0, 1]], [1.0, 2.0], [0.0, 3.0])
    with pytest.raises(ValueError):
        sb.reconstruct_erosion([[0, 2]], [0.0, 0.0], [1.0, 1.0])
    with pytest.raises(ValueError):
        sb.barcode0([[0, 1]], [0.0, float("nan")])
    with pytest.raises(ValueError):
        sb.absolute_box([1.0], -1.0)
