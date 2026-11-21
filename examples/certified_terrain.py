"""Counting the basins and hills of a terrain that is known only up to an error bound.

A smooth 96 x 96 terrain is perturbed by at most eps at every vertex, as an error-bounded lossy
compressor would do, so the box [g - eps, g + eps] around the perturbed terrain g contains the
true one. Counting the bars of g overcounts: the perturbation creates many small basins and hills.
The certified counts of the box never exceed the true counts (Theorem 1), and no certificate
computed from the box can certify more: in degree 0 by Theorem 5, and in degree 1 on a grid by
Theorem 8.

    python examples/certified_terrain.py
"""
import numpy as np

import subbarcode as sb

rng = np.random.default_rng(0)
n, eps = 96, 0.02
y, x = np.mgrid[0:n, 0:n] / (n - 1)
truth = np.zeros((n, n))
for _ in range(14):                                    # smooth hills and pits
    cx, cy, height, width = rng.random(), rng.random(), rng.uniform(-1, 1), rng.uniform(0.03, 0.09)
    truth += height * np.exp(-((x - cx) ** 2 + (y - cy) ** 2) / (2 * width ** 2))
g = truth + rng.uniform(-eps, eps, truth.shape)        # what we are given: |g - truth| <= eps
lower, upper = g - eps, g + eps

edges = sb.grid_edges((n, n))                          # Freudenthal triangulation: 6 neighbours per vertex
basins = {"given": sb.barcode0(edges, g.ravel()), "true": sb.barcode0(edges, truth.ravel()),
          "certified": sb.image_barcode0(edges, lower.ravel(), upper.ravel())}
hills = {"given": sb.image_barcode_grid(g, g), "true": sb.image_barcode_grid(truth, truth),
         "certified": sb.image_barcode_grid(lower, upper)}

print(f"bars longer than tau, {n} x {n} terrain known up to {eps}\n")
print(f"{'':>6}{'degree 0 (basins)':^30}{'degree 1 (hills)':^30}")
print(f"{'tau':>6}" + f"{'given':>10}{'true':>8}{'certified':>12}" * 2)
for tau in (0.01, 0.02, 0.05, 0.1, 0.2):
    row = [sb.count_longer(bars[k], tau) for bars in (basins, hills) for k in ("given", "true", "certified")]
    assert row[2] <= row[1] and row[5] <= row[4]       # a certificate never exceeds the truth
    print(f"{tau:>6}" + "".join(f"{a:>10}{b:>8}{c:>12}" for a, b, c in (row[:3], row[3:])))
