"""Graphs and Freudenthal-triangulated grids."""
from __future__ import annotations

from itertools import permutations
from typing import Sequence

import numpy as np

__all__ = ["grid_edges", "grid_simplices", "grid_boundary", "path_edges"]

# Edge directions of the grids. In the Freudenthal (Kuhn) triangulation every edge joins two
# vertices whose coordinates differ by a non-zero 0/1 vector.
_STEPS = {
    (1, 2): [(1,)],
    (2, 4): [(0, 1), (1, 0)],
    (2, 6): [(0, 1), (1, 0), (1, 1)],
    (2, 8): [(0, 1), (1, 0), (1, 1), (1, -1)],
    (3, 6): [(0, 0, 1), (0, 1, 0), (1, 0, 0)],
    (3, 14): [(0, 0, 1), (0, 1, 0), (1, 0, 0), (0, 1, 1), (1, 0, 1), (1, 1, 0), (1, 1, 1)],
}
_DEFAULT = {1: 2, 2: 6, 3: 6}


def _check_shape(shape: Sequence[int]) -> tuple[int, ...]:
    shape = tuple(int(s) for s in shape)
    if not shape or any(s < 1 for s in shape):
        raise ValueError(f"invalid grid shape {shape}")
    return shape


def grid_edges(shape: Sequence[int], connectivity: int | None = None) -> np.ndarray:
    """Edges of a regular grid whose vertices are numbered in C (row-major) order.

    connectivity
        1-D: 2 (a path).
        2-D: 4 (axis neighbours), 6 (Freudenthal triangulation, one diagonal per square from
        (i, j) to (i+1, j+1)), or 8 (both diagonals).
        3-D: 6 (face neighbours) or 14 (Freudenthal triangulation, seven directions).
        The default is 2, 6 and 6 in dimensions 1, 2 and 3: the grids of the compression
        experiments (triangulated in 2-D, face-adjacent in 3-D).

    Returns an int64 array of shape (m, 2).
    """
    shape = _check_shape(shape)
    d = len(shape)
    conn = _DEFAULT.get(d) if connectivity is None else int(connectivity)
    if (d, conn) not in _STEPS:
        raise ValueError(f"connectivity {connectivity} is not available for {d}-D grids")
    idx = np.arange(int(np.prod(shape)), dtype=np.int64).reshape(shape)
    parts = []
    for step in _STEPS[(d, conn)]:
        src = tuple(slice(max(0, -s), n - max(0, s)) for s, n in zip(step, shape))
        dst = tuple(slice(max(0, s), n + min(0, s)) for s, n in zip(step, shape))
        a, b = idx[src].ravel(), idx[dst].ravel()
        if a.size:
            parts.append(np.stack([a, b], axis=1))
    return np.concatenate(parts) if parts else np.zeros((0, 2), np.int64)


def grid_simplices(shape: Sequence[int]) -> np.ndarray:
    """Top-dimensional simplices of the Freudenthal triangulation of a 2-D or 3-D grid.

    Every unit square (cube) with corner v is split into the 2 (6) simplices
    v, v + e_p1, v + e_p1 + e_p2, ... over the permutations p of the axes. The 1-skeleton
    is ``grid_edges(shape, 6)`` in 2-D and ``grid_edges(shape, 14)`` in 3-D.

    Returns an int64 array of shape (k, d + 1) with sorted rows.
    """
    shape = _check_shape(shape)
    d = len(shape)
    if d not in (2, 3):
        raise ValueError("Freudenthal simplices are provided for 2-D and 3-D grids")
    idx = np.arange(int(np.prod(shape)), dtype=np.int64).reshape(shape)
    corner = idx[tuple(slice(0, n - 1) for n in shape)].ravel()
    if corner.size == 0:
        return np.zeros((0, d + 1), np.int64)
    strides = np.array([int(np.prod(shape[a + 1:])) for a in range(d)], dtype=np.int64)
    out = []
    for perm in permutations(range(d)):
        verts, offset = [corner], 0
        for axis in perm:
            offset += strides[axis]
            verts.append(corner + offset)
        out.append(np.stack(verts, axis=1))
    return np.sort(np.concatenate(out), axis=1)


def grid_boundary(shape: Sequence[int]) -> np.ndarray:
    """Indices of the vertices on the boundary of the grid (some coordinate is extreme)."""
    shape = _check_shape(shape)
    coords = np.indices(shape).reshape(len(shape), -1)
    on = np.zeros(coords.shape[1], dtype=bool)
    for axis, n in enumerate(shape):
        on |= (coords[axis] == 0) | (coords[axis] == n - 1)
    return np.flatnonzero(on).astype(np.int64)


def path_edges(n: int) -> np.ndarray:
    """Edges of the path 0 - 1 - ... - (n-1)."""
    return grid_edges((int(n),), 2)


# ---------------------------------------------------------------- internal helpers
def _as_function(x, name: str) -> np.ndarray:
    a = np.asarray(x, dtype=np.float64).ravel()
    if not np.all(np.isfinite(a)):
        raise ValueError(f"{name} must be finite")
    return a


def _as_box(lower, upper) -> tuple[np.ndarray, np.ndarray]:
    lo, hi = _as_function(lower, "lower"), _as_function(upper, "upper")
    if lo.shape != hi.shape:
        raise ValueError("lower and upper must have the same number of vertices")
    if np.any(lo > hi):
        raise ValueError("the box is empty: lower > upper at some vertex")
    return lo, hi


def _as_edges(edges, n: int) -> np.ndarray:
    e = np.asarray(edges, dtype=np.int64)
    if e.size == 0:
        return np.zeros((0, 2), np.int64)
    if e.ndim != 2 or e.shape[1] != 2:
        raise ValueError("edges must be an array of shape (m, 2)")
    if e.min() < 0 or e.max() >= n:
        raise ValueError("edge endpoints must be vertex indices in [0, n)")
    return e


def _adjacency(n: int, edges: np.ndarray) -> tuple[list[int], list[int]]:
    """Both directions of every edge in CSR form, as Python lists for fast scalar access."""
    e = edges[edges[:, 0] != edges[:, 1]]
    src = np.concatenate([e[:, 0], e[:, 1]])
    dst = np.concatenate([e[:, 1], e[:, 0]])
    order = np.argsort(src, kind="stable")
    indptr = np.zeros(n + 1, dtype=np.int64)
    np.cumsum(np.bincount(src, minlength=n), out=indptr[1:])
    return indptr.tolist(), dst[order].tolist()
