"""Brute-force oracles over Z/2, used only by the tests.

Rank invariants of maps between full subcomplexes are computed from the definitions, with
chains stored as Python integers (bit vectors) and Gaussian elimination over Z/2.
"""
from __future__ import annotations

import heapq
import math
from itertools import combinations

import numpy as np


def gf2_rank(vectors) -> int:
    basis: dict[int, int] = {}
    for v in vectors:
        while v:
            p = v.bit_length() - 1
            if p in basis:
                v ^= basis[p]
            else:
                basis[p] = v
                break
    return len(basis)


class SimplicialComplex:
    """A finite simplicial complex given by its maximal simplices (all faces are added)."""

    def __init__(self, n_vertices: int, simplices):
        faces = {(v,) for v in range(n_vertices)}
        for s in simplices:
            s = tuple(sorted(int(v) for v in s))
            for k in range(1, len(s) + 1):
                faces.update(combinations(s, k))
        top = max(len(f) for f in faces)
        self.by_dim = {k: sorted(f for f in faces if len(f) == k + 1) for k in range(top)}
        self.index = {k: {s: i for i, s in enumerate(fs)} for k, fs in self.by_dim.items()}

    def _boundary(self, s) -> int:
        k = len(s) - 1
        if k == 0:
            return 0
        bits = 0
        for i in range(len(s)):
            bits ^= 1 << self.index[k - 1][s[:i] + s[i + 1:]]
        return bits

    def rank(self, A, B, k: int) -> int:
        """rank(H_k(K[A]) -> H_k(K[B])) for vertex sets A within B (full subcomplexes)."""
        A, B = set(A), set(B)
        assert A <= B
        pivots: dict[int, tuple[int, int]] = {}
        cycles = []
        for s in self.by_dim.get(k, []):
            if not all(v in A for v in s):
                continue
            vec, tag = self._boundary(s), 1 << self.index[k][s]
            while vec:
                p = vec.bit_length() - 1
                if p in pivots:
                    pv, pt = pivots[p]
                    vec ^= pv
                    tag ^= pt
                else:
                    pivots[p] = (vec, tag)
                    break
            if vec == 0:
                cycles.append(tag)
        bounds = [self._boundary(s) for s in self.by_dim.get(k + 1, []) if all(v in B for v in s)]
        return gf2_rank(bounds + cycles) - gf2_rank(bounds)


def image_rank_function(cx: SimplicialComplex, lower, upper, k: int, values):
    """r(s, t) = rank(H_k(K[u <= s]) -> H_k(K[l <= t])) for all s <= t in ``values``."""
    lower, upper = np.asarray(lower, float).ravel(), np.asarray(upper, float).ravel()
    out = {}
    for i, s in enumerate(values):
        A = np.flatnonzero(upper <= s)
        for t in values[i:]:
            B = np.flatnonzero(lower <= t)
            out[(s, t)] = cx.rank(A, B, k)
    return out


def bars_rank_function(bars, values):
    """r(s, t) = number of bars [b, d) with b <= s <= t < d."""
    bars = np.asarray(bars, float).reshape(-1, 2)
    return {(s, t): int(np.sum((bars[:, 0] <= s) & (t < bars[:, 1])))
            for i, s in enumerate(values) for t in values[i:]}


def critical_values(*arrays):
    vals = sorted({float(x) for a in arrays for x in np.asarray(a).ravel()})
    lo, hi = vals[0], vals[-1]
    mids = [(a + b) / 2 for a, b in zip(vals, vals[1:])]
    return sorted(vals + mids + [lo - 1.0, hi + 1.0])


def path_minimax(n: int, edges, lower, upper):
    """f_U from its definition: min over w and paths w -> v of max(u(w), max of l on the path)."""
    adj = [[] for _ in range(n)]
    for a, b in np.asarray(edges, dtype=int).reshape(-1, 2):
        adj[a].append(b)
        adj[b].append(a)
    lower, upper = list(map(float, np.ravel(lower))), list(map(float, np.ravel(upper)))
    best = upper[:]
    heap = [(best[v], v) for v in range(n)]
    heapq.heapify(heap)
    while heap:
        d, v = heapq.heappop(heap)
        if d > best[v]:
            continue
        for w in adj[v]:
            c = max(d, lower[w])
            if c < best[w]:
                best[w] = c
                heapq.heappush(heap, (c, w))
    return np.asarray(best)


def random_graph(rng, n: int, p: float):
    edges = [(a, b) for a in range(n) for b in range(a + 1, n) if rng.random() < p]
    return np.asarray(edges, dtype=np.int64).reshape(-1, 2)


def random_box(rng, n: int, top: int = 6, width: int = 3):
    lower = rng.integers(0, top, size=n)
    upper = lower + rng.integers(0, width + 1, size=n)
    return lower.astype(float), upper.astype(float)


def as_multiset(bars):
    return sorted((float(b), float(d)) for b, d in np.asarray(bars, float).reshape(-1, 2))


INF = math.inf
