"""The reconstructions f_U and f_D of a box (Section 3 of the paper)."""
from __future__ import annotations

import numpy as np

from ._graph import _adjacency, _as_box, _as_edges

__all__ = ["reconstruct_erosion", "reconstruct_dilation"]


def reconstruct_erosion(edges, lower, upper) -> np.ndarray:
    """The reconstruction by erosion f_U of the marker ``upper`` over the mask ``lower``.

    For every vertex v,

        f_U(v) = min over vertices w and paths gamma from w to v of max(u(w), max of l on gamma),

    so f_U(v) <= t exactly when v lies in a component of the subgraph {l <= t} that meets
    {u <= t}. By Theorem 5, f_U attains the degree-0 image barcode Bar_0(u >= l) and is the
    pointwise smallest function in the box that does.

    One upward sweep over the values of l and u with a union-find structure: a component
    becomes active when it first contains a vertex with u <= t, and its members receive
    f_U = t at that moment. O(n log n + m alpha(n)) time.

    Parameters
    ----------
    edges : (m, 2) int array, the edges of the graph (the 1-skeleton of the complex).
    lower, upper : arrays with one value per vertex, lower <= upper.
    """
    lo, hi = _as_box(lower, upper)
    n = lo.size
    indptr, indices = _adjacency(n, _as_edges(edges, n))

    # events (value, kind, vertex): kind 0 = the vertex enters {l <= t}, kind 1 = it enters {u <= t}.
    # At equal values entering comes first, so a vertex is always present when it is activated.
    vals = np.concatenate([lo, hi])
    kind = np.concatenate([np.zeros(n, np.int8), np.ones(n, np.int8)])
    vert = np.concatenate([np.arange(n), np.arange(n)])
    order = np.lexsort((vert, kind, vals))
    ev_val, ev_kind, ev_vert = vals[order].tolist(), kind[order].tolist(), vert[order].tolist()

    parent = list(range(n))
    size = [1] * n
    present = [False] * n
    active = [False] * n
    head = [-1] * n            # pending (not yet assigned) members of a root, as a linked list
    tail = [-1] * n
    nxt = [-1] * n
    out = [0.0] * n

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def assign(r: int, t: float) -> None:
        v = head[r]
        while v != -1:
            out[v] = t
            v = nxt[v]
        head[r] = tail[r] = -1

    def union(a: int, b: int, t: float) -> int:
        if size[a] < size[b]:
            a, b = b, a
        parent[b] = a
        size[a] += size[b]
        if active[a] or active[b]:
            if not active[a]:
                assign(a, t)
            if not active[b]:
                assign(b, t)
            active[a] = True
        elif head[b] != -1:                    # both inactive: concatenate the pending lists
            if head[a] == -1:
                head[a], tail[a] = head[b], tail[b]
            else:
                nxt[tail[a]] = head[b]
                tail[a] = tail[b]
        head[b] = tail[b] = -1
        return a

    for t, k, v in zip(ev_val, ev_kind, ev_vert):
        if k == 0:
            present[v] = True
            head[v] = tail[v] = v
            r = v
            for q in range(indptr[v], indptr[v + 1]):
                w = indices[q]
                if present[w]:
                    rw = find(w)
                    if rw != r:
                        r = union(r, rw, t)
        else:
            r = find(v)
            if not active[r]:
                active[r] = True
                assign(r, t)
    return np.asarray(out, dtype=np.float64)


def reconstruct_dilation(edges, lower, upper) -> np.ndarray:
    """The reconstruction by dilation f_D = -f_U(-u, -l) of the marker ``lower`` under the mask ``upper``.

    f_D(v) > t exactly when v lies in a component of {u > t} that meets {l > t}. Computed on a
    triangulated d-sphere L that contains the complex as a full subcomplex, it attains the
    degree-(d-1) image barcode (Theorem 8); see :func:`subbarcode.image_barcode_grid`.
    """
    lo, hi = _as_box(lower, upper)
    return -reconstruct_erosion(edges, -hi, -lo)
