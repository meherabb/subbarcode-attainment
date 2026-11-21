"""The box of Figure 1 of the paper: the bars that every function in it has, and a function that has exactly those.

    python examples/figure1.py
"""
import numpy as np

import subbarcode as sb

lower = np.array([4, 1, 3, 6, 2, 5, 7, 3, 1, 4, 6, 5, 2, 4])
upper = np.array([6, 2, 7, 8, 5, 6, 9, 7, 3, 8, 7, 9, 6, 6])
edges = sb.path_edges(len(lower))                   # the graph is a path with 14 vertices

bars = sb.image_barcode0(edges, lower, upper)       # Bar_0(u >= l), the sub-barcode bound
f_U = sb.reconstruct_erosion(edges, lower, upper)   # the smallest function in the box that attains it
print("image barcode       ", bars.tolist())
print("f_U                 ", f_U.astype(int).tolist())
print("barcode of f_U      ", sb.barcode0(edges, f_U).tolist())

# Every other function in the box has these bars too, possibly inside longer ones (Theorem 1).
rng = np.random.default_rng(1)
for _ in range(3):
    f = rng.uniform(lower, upper)
    print("a function in the box", np.round(sb.barcode0(edges, f), 2).tolist(),
          "contains it:", sb.is_sub_barcode(bars, sb.barcode0(edges, f)))

# So the bars longer than tau that the box certifies are exactly those of f_U.
for tau in (0, 1, 2, 4):
    print(f"bars longer than {tau}: {sb.certified_count(edges, lower, upper, tau)}")
