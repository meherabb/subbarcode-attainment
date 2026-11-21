"""Image barcodes of boxes, and the bars every function in a box must have."""
from __future__ import annotations

import numpy as np

from ._graph import _as_box, _as_edges, grid_boundary, grid_edges
from .barcodes import barcode0, count_longer
from .reconstruction import reconstruct_dilation, reconstruct_erosion

__all__ = [
    "image_barcode0",
    "certified_count",
    "absolute_box",
    "image_barcode_grid",
    "attaining_function_grid",
]


def image_barcode0(edges, lower, upper) -> np.ndarray:
    """The degree-0 image barcode Bar_0(u >= l) of a box on a graph.

    This is the barcode of the persistence module t -> im(H_0(K[u <= t]) -> H_0(K[l <= t])).
    By the theorem of Chubet, Gardner and Sheehy (Theorem 1) it is a sub-barcode of
    Bar_0(f) for every f with l <= f <= u, and by Theorem 5 it equals Bar_0(f_U), which is
    how it is computed here.
    """
    lo, hi = _as_box(lower, upper)
    e = _as_edges(edges, lo.size)
    return barcode0(e, reconstruct_erosion(e, lo, hi))


def certified_count(edges, lower, upper, tau: float) -> int:
    """Number of degree-0 bars longer than tau that every function in the box has.

    This is the number of bars of the image barcode longer than tau. It is a lower bound for
    every function in the box, and f_U attains it (Theorem 5 and Lemma 2), so no certificate
    computed from the box alone can certify more.
    """
    return count_longer(image_barcode0(edges, lower, upper), tau)


def absolute_box(values, error_bound: float) -> tuple[np.ndarray, np.ndarray]:
    """The box [v - eps, v + eps] around decompressed values with absolute error bound eps.

    For such a box the degree-0 image barcode is Bar_0 of the decompressed field with eps cut
    from both ends of every bar (the eps-smoothing), so the certified count at tau equals the
    number of its bars longer than tau + 2 eps.
    """
    v = np.asarray(values, dtype=np.float64)
    eps = float(error_bound)
    if not eps >= 0:
        raise ValueError("the error bound must be non-negative")
    return v - eps, v + eps


def _coned_grid(lower, upper):
    lo = np.asarray(lower, dtype=np.float64)
    hi = np.asarray(upper, dtype=np.float64)
    if lo.shape != hi.shape or lo.ndim not in (2, 3):
        raise ValueError("lower and upper must be 2-D or 3-D arrays of the same shape")
    if min(lo.shape) < 2:
        raise ValueError("every side of the grid needs at least two vertices, so that the grid is a d-ball")
    lo_flat, hi_flat = _as_box(lo, hi)
    shape, n = lo.shape, lo.size
    conn = 6 if lo.ndim == 2 else 14
    edges = grid_edges(shape, conn)
    apex = np.full(grid_boundary(shape).size, n, dtype=np.int64)
    cone = np.stack([apex, grid_boundary(shape)], axis=1)
    big = float(max(hi_flat.max(), lo_flat.max())) + 1.0          # any value above max u
    lo_L = np.append(lo_flat, big)
    hi_L = np.append(hi_flat, big)
    return np.concatenate([edges, cone]), lo_L, hi_L, shape


def attaining_function_grid(lower, upper) -> np.ndarray:
    """f_D of Theorem 8 for a box on a Freudenthal-triangulated 2-D or 3-D grid.

    The grid K is a full subcomplex of the d-sphere L obtained by coning its boundary to one
    new vertex, which gets the fixed value M > max u. The function f_D is computed on L and
    restricted to K; it lies in the box and attains Bar_{d-1}(u >= l), and it is the pointwise
    largest function in the box that does.

    Returns an array of the shape of ``lower``.
    """
    edges_L, lo_L, hi_L, shape = _coned_grid(lower, upper)
    return reconstruct_dilation(edges_L, lo_L, hi_L)[:-1].reshape(shape)


def image_barcode_grid(lower, upper) -> np.ndarray:
    """The image barcode Bar_{d-1}(u >= l) of a box on a Freudenthal-triangulated d-grid, d = 2 or 3.

    Degree 1 for 2-D images and terrains, degree 2 (voids) for 3-D volumes. By Lemmas 6 and 7
    (Alexander duality), its rank function is that of the reduced degree-0 persistence of the
    superlevel sets of f_D on the coned grid L: a component of {f_D > t} born at its maximum B
    and merged at value D gives the bar [D, B). Two union-find sweeps, O(n log n + m alpha(n)).

    The grid triangulation is that of :func:`subbarcode.grid_simplices`: one diagonal per
    square in 2-D, six tetrahedra per cube in 3-D. Returns a float array of shape (k, 2).
    """
    edges_L, lo_L, hi_L, _ = _coned_grid(lower, upper)
    f_d = reconstruct_dilation(edges_L, lo_L, hi_L)
    bars = barcode0(edges_L, -f_d)                    # superlevel sets of f_D are sublevel sets of -f_D
    finite = bars[np.isfinite(bars[:, 1])]            # reduced homology: drop the essential class
    out = np.stack([-finite[:, 1], -finite[:, 0]], axis=1) if finite.size else np.zeros((0, 2))
    order = np.lexsort((out[:, 1], out[:, 0])) if out.size else np.zeros(0, dtype=np.int64)
    return out[order]
