"""Certified bars of functions known only up to a box, and the functions that attain them.

A reference implementation of the algorithms of "When Is the Sub-Barcode Bound Attained?":
the reconstructions f_U and f_D, degree-0 barcodes, the degree-0 image barcode of a box on any
graph (Theorem 5), and the degree-(d-1) image barcode on Freudenthal-triangulated 2-D and 3-D
grids (Theorem 8). Pure Python and NumPy; every function is checked against brute-force rank
invariants in ``tests/``.
"""
from ._graph import grid_boundary, grid_edges, grid_simplices, path_edges
from .barcodes import barcode0, count_longer, is_sub_barcode
from .certificates import (
    absolute_box,
    attaining_function_grid,
    certified_count,
    image_barcode0,
    image_barcode_grid,
)
from .reconstruction import reconstruct_dilation, reconstruct_erosion

__version__ = "1.0.0"

__all__ = [
    "absolute_box",
    "attaining_function_grid",
    "barcode0",
    "certified_count",
    "count_longer",
    "grid_boundary",
    "grid_edges",
    "grid_simplices",
    "image_barcode0",
    "image_barcode_grid",
    "is_sub_barcode",
    "path_edges",
    "reconstruct_dilation",
    "reconstruct_erosion",
]
