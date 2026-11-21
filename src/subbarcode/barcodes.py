"""Degree-0 barcodes of lower-star filtrations, counts of long bars, and sub-barcodes."""
from __future__ import annotations

import math

import numpy as np

from ._graph import _adjacency, _as_edges, _as_function

__all__ = ["barcode0", "count_longer", "is_sub_barcode"]


def barcode0(edges, f) -> np.ndarray:
    """Degree-0 barcode of the lower-star filtration of a function on the vertices of a graph.

    Vertices enter in the order of (f(v), v); when components merge, the younger one dies
    (elder rule). Bars of length zero are dropped, and every connected component of the graph
    contributes one essential bar [b, inf).

    Returns a float array of shape (k, 2) of bars [birth, death), sorted.
    """
    f = _as_function(f, "f")
    n = f.size
    if n == 0:
        return np.zeros((0, 2))
    indptr, indices = _adjacency(n, _as_edges(edges, n))
    order = np.lexsort((np.arange(n), f)).tolist()
    rank = [0] * n
    for i, v in enumerate(order):
        rank[v] = i
    fl = f.tolist()

    parent = list(range(n))
    size = [1] * n
    present = [False] * n
    birth = [0.0] * n          # birth value of the component, kept at its root
    oldest = [0] * n           # rank of the vertex that created it, for ties
    bars: list[tuple[float, float]] = []

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for v in order:
        t = fl[v]
        present[v] = True
        birth[v], oldest[v] = t, rank[v]
        r = v
        for q in range(indptr[v], indptr[v + 1]):
            w = indices[q]
            if not present[w]:
                continue
            rw = find(w)
            if rw == r:
                continue
            if (birth[rw], oldest[rw]) < (birth[r], oldest[r]):
                old, young = rw, r
            else:
                old, young = r, rw
            if birth[young] < t:
                bars.append((birth[young], t))
            keep_birth, keep_oldest = birth[old], oldest[old]
            if size[r] < size[rw]:
                r, rw = rw, r
            parent[rw] = r
            size[r] += size[rw]
            birth[r], oldest[r] = keep_birth, keep_oldest
    for v in range(n):
        if parent[v] == v:
            bars.append((birth[v], math.inf))
    bars.sort()
    return np.asarray(bars, dtype=np.float64).reshape(-1, 2)


def count_longer(bars, tau: float) -> int:
    """Number of bars [b, d) with d - b > tau. Essential bars are longer than every tau."""
    b = np.asarray(bars, dtype=np.float64).reshape(-1, 2)
    if b.size == 0:
        return 0
    with np.errstate(invalid="ignore"):
        return int(np.sum((b[:, 1] - b[:, 0]) > tau))


def is_sub_barcode(a, b) -> bool:
    """True if barcode ``a`` is a sub-barcode of ``b``.

    That is, if there is an injection phi from the bars of ``a`` to the bars of ``b`` with
    J contained in phi(J) for every bar J, in the sense of Chubet, Gardner and Sheehy.
    Decided exactly by a maximum bipartite matching (augmenting paths).
    """
    A = [tuple(x) for x in np.asarray(a, dtype=np.float64).reshape(-1, 2)]
    B = [tuple(x) for x in np.asarray(b, dtype=np.float64).reshape(-1, 2)]
    if len(A) > len(B):
        return False
    fits = [[j for j, (bb, dd) in enumerate(B) if bb <= ab and ad <= dd] for ab, ad in A]
    match_b = [-1] * len(B)
    return all(_augment(i, fits, match_b, [False] * len(B)) for i in range(len(A)))


def _augment(i: int, fits: list[list[int]], match_b: list[int], seen: list[bool]) -> bool:
    """Search for an augmenting path from the left vertex i (iterative depth-first search)."""
    stack = [[i, 0, -1]]                   # left vertex, next position in fits, right vertex used to reach it
    while stack:
        top = stack[-1]
        u, k = top[0], top[1]
        if k == len(fits[u]):
            stack.pop()
            continue
        top[1] += 1
        j = fits[u][k]
        if seen[j]:
            continue
        seen[j] = True
        if match_b[j] == -1:
            match_b[j] = u
            for depth in range(len(stack) - 1, 0, -1):
                match_b[stack[depth][2]] = stack[depth - 1][0]
            return True
        stack.append([match_b[j], 0, j])
    return False
