"""Draw the README graphics in docs/assets.

    python scripts/build_assets.py              # every graphic, the terminal replay and the figure previews
    python scripts/build_assets.py --no-record  # keep docs/assets/terminal.svg as it is

Nothing is drawn by hand. The box, f_U and the barcodes in the banner and in the animated sweep
are computed by the subbarcode package; the attainment map is Table 1 of the paper; the pipeline
and the badges read their numbers from results/, the claim checker and the test suite; and the
terminal replay is the verbatim output of the recipe of `make check`, run when this script runs.
The PNG previews of Figures 1-4 need pdftoppm (poppler); without it they are left as they are.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from functools import lru_cache
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
import subbarcode as sb  # noqa: E402

ASSETS = ROOT / "docs" / "assets"

SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"
SERIF = "'STIX Two Text','Cambria Math',Cambria,'Latin Modern Roman','Times New Roman',Times,serif"

# The page colours of GitHub, and series hues from a palette checked for colour-vision deficiency.
THEMES = {
    "light": dict(bg="#ffffff", panel="#f6f8fa", border="#d1d9e0", grid="#eef1f4", ink="#1f2328",
                  muted="#59636e", faint="#818b98", box="#c1cad3", box_fill="#ffffff", entered="#dde3e9",
                  blue="#2a78d6", blue_fill="#c2daf6", orange="#eb6834",
                  ok="#1a7f37", ok_bg="#dafbe1", warn="#9a6700", warn_bg="#fff8c5",
                  bad="#cf222e", bad_bg="#ffebe9", info="#0969da", info_bg="#ddf4ff"),
    "dark": dict(bg="#0d1117", panel="#151b23", border="#3d444d", grid="#1b2129", ink="#f0f6fc",
                 muted="#9198a1", faint="#656c76", box="#4a525c", box_fill="#0d1117", entered="#2b323c",
                 blue="#4493f8", blue_fill="#1a3a63", orange="#e0703c",
                 ok="#3fb950", ok_bg="#132a1b", warn="#d29922", warn_bg="#2b2111",
                 bad="#f85149", bad_bg="#2d1517", info="#4493f8", info_bg="#121d2f"),
}


# ------------------------------------------------------------------------------------ SVG text
def num(x) -> str:
    """A coordinate with at most two decimals."""
    s = f"{float(x):.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


@lru_cache(maxsize=None)
def _font(bold: bool):
    """DejaVu Sans, shipped with matplotlib. It is wider than the system faces that GitHub readers
    have, so widths measured with it are safe upper bounds for layout."""
    try:
        from matplotlib import font_manager
        from PIL import ImageFont
        prop = font_manager.FontProperties(family="DejaVu Sans", weight="bold" if bold else "normal")
        return ImageFont.truetype(font_manager.findfont(prop), 100)
    except Exception:                                   # pragma: no cover
        return None


def width(s: str, size: float, bold: bool = False) -> float:
    font = _font(bold)
    if font is None:                                    # pragma: no cover
        return 0.62 * size * len(s)
    return font.getlength(s) * size / 100


def _math_tokens(expr: str):
    """Tokens of a small TeX-like syntax: a lone letter is a variable (italic), a longer run of letters
    an operator name such as Bar or log (upright), _x and ^x are sub- and superscripts, {..} groups."""
    i = 0
    while i < len(expr):
        ch = expr[i]
        if ch in "_^" and i + 1 < len(expr):
            if expr[i + 1] == "{":
                j = expr.index("}", i + 1)
                yield ("sub" if ch == "_" else "sup"), expr[i + 2:j]
                i = j + 1
            else:
                yield ("sub" if ch == "_" else "sup"), expr[i + 1]
                i += 2
        elif ch.isalpha():
            j = i
            while j < len(expr) and expr[j].isalpha():
                j += 1
            yield ("var" if j - i == 1 else "word"), expr[i:j]
            i = j
        else:
            j = i
            while j < len(expr) and not expr[j].isalpha() and expr[j] not in "_^":
                j += 1
            yield "other", expr[i:j]
            i = j


def rich(content: str, size: float) -> str:
    """Tspans for text with $...$ segments set as mathematics in a serif face.

    Sub- and superscripts are moved with dy on the tspan that carries them, and the baseline is
    restored by the dy of the next tspan, because a shift on an empty tspan is ignored.
    """
    segments = []                                       # (text, italic, level, math)
    for k, part in enumerate(content.split("$")):
        if not part:
            continue
        if k % 2 == 0:
            segments.append((part, False, 0, False))
            continue
        for kind, s in _math_tokens(part):
            if kind in ("sub", "sup"):
                level = -1 if kind == "sub" else 1
                segments += [(ss, kk == "var", level, True) for kk, ss in _math_tokens(s)]
            else:
                segments.append((s, kind == "var", 0, True))
    shift = {0: 0.0, -1: 0.3 * size, 1: -0.42 * size}
    out, level = [], 0
    for s, italic, lev, is_math in segments:
        attrs = []
        if lev != level:
            attrs.append(f'dy="{num(shift[lev] - shift[level])}"')
            level = lev
        if is_math:
            attrs.append(f'font-family="{SERIF}"')
        fs = size * (1.1 if is_math else 1.0) * (0.72 if lev else 1.0)
        if abs(fs - size) > 1e-9:
            attrs.append(f'font-size="{num(fs)}"')
        if italic:
            attrs.append('font-style="italic"')
        out.append(f"<tspan {' '.join(attrs)}>{escape(s)}</tspan>" if attrs else escape(s))
    return "".join(out)


def text(x, y, content, size=13.0, fill="#000", anchor="start", weight=None, family=SANS) -> str:
    w = f' font-weight="{weight}"' if weight else ""
    return (f'<text x="{num(x)}" y="{num(y)}" font-family="{family}" font-size="{num(size)}" fill="{fill}" '
            f'text-anchor="{anchor}"{w}>{rich(content, size)}</text>')


def svg(w: int, h: int, body: str, title: str, desc: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-labelledby="title desc">\n<title id="title">{escape(title)}</title>\n'
            f'<desc id="desc">{escape(desc)}</desc>\n{body}\n</svg>\n')


# ------------------------------------------------------------------------------------ glyphs
GLYPHS = {                                              # 24 x 24 line icons
    "notebook": '<rect x="6" y="3" width="13" height="18" rx="2"/><path d="M3.5 7.5h4M3.5 12h4M3.5 16.5h4M10 8h6M10 12h6M10 16h3.5"/>',
    "archive": '<rect x="3" y="4" width="18" height="5" rx="1.2"/><path d="M4.8 9v9.2a2 2 0 0 0 2 2h10.4a2 2 0 0 0 2-2V9M10 13h4"/>',
    "paper": '<path d="M14 3H7.5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h9a2 2 0 0 0 2-2V7.5z"/><path d="M14 3v4.5h4.5M8.8 12.5h6.4M8.8 16.5h4.4"/>',
    "package": '<path d="M12 2.8l8 4.6v9.2l-8 4.6-8-4.6V7.4z"/><path d="M4 7.4l8 4.6 8-4.6M12 12v9.2"/>',
    "matrix": '<path d="M7 4H4.5v16H7M17 4h2.5v16H17"/>'
              + "".join(f'<circle cx="{x}" cy="{y}" r=".95" class="dot"/>' for y in (8.5, 12, 15.5) for x in (9, 12, 15)),
    "terminal": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M7 9.5l3 2.5-3 2.5M12.5 15h4.5"/>',
    "tests": '<path d="M9 3h6M10 3v5.5L5.2 17.3A2.4 2.4 0 0 0 7.3 21h9.4a2.4 2.4 0 0 0 2.1-3.7L14 8.5V3M7.3 14.5h9.4"/>',
    "book": '<path d="M12 6.5C10.3 5 7.9 4.4 4 4.5v13.8c3.9-.1 6.3.5 8 2 1.7-1.5 4.1-2.1 8-2V4.5c-3.9-.1-6.3.5-8 2zM12 6.5v13.8"/>',
    "code": '<path d="M8.5 8L4.5 12l4 4M15.5 8l4 4-4 4M13.3 5.5l-2.6 13"/>',
}


def glyph(name: str, x: float, y: float, size: float, stroke: str, stroke_width: float = 1.6) -> str:
    s = size / 24
    body = GLYPHS[name].replace('class="dot"', f'fill="{stroke}" stroke="none"')
    return (f'<g transform="translate({num(x)} {num(y)}) scale({num(s)})" fill="none" stroke="{stroke}" '
            f'stroke-width="{num(stroke_width / s)}" stroke-linecap="round" stroke-linejoin="round">{body}</g>')


def status_icon(kind: str, cx: float, cy: float, color: str) -> str:
    """A check (attained), a cross (can fail), a half disc (depends) or a diamond (decidable)."""
    if kind == "ok":
        return (f'<path d="M{num(cx - 4)} {num(cy + .2)}l2.8 2.8 5.2-5.6" fill="none" stroke="{color}" '
                f'stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/>')
    if kind == "bad":
        return (f'<path d="M{num(cx - 3.4)} {num(cy - 3.4)}l6.8 6.8M{num(cx + 3.4)} {num(cy - 3.4)}l-6.8 6.8" '
                f'stroke="{color}" stroke-width="1.9" stroke-linecap="round"/>')
    if kind == "warn":
        return (f'<circle cx="{num(cx)}" cy="{num(cy)}" r="4.6" fill="none" stroke="{color}" stroke-width="1.6"/>'
                f'<path d="M{num(cx)} {num(cy - 4.6)}a4.6 4.6 0 0 1 0 9.2z" fill="{color}"/>')
    return (f'<path d="M{num(cx)} {num(cy - 5)}l5 5-5 5-5-5z" fill="none" stroke="{color}" stroke-width="1.6" '
            f'stroke-linejoin="round"/>')


def write_icons() -> None:
    """One-colour icons for the layout table of the README; the mid-tone blue reads on light and dark pages."""
    for name in ("notebook", "archive", "package", "terminal", "tests", "book", "code"):
        (ASSETS / "icons" / f"{name}.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" aria-hidden="true">'
            + glyph(name, 0, 0, 24, "#3d8fe0", 1.7) + "</svg>\n", encoding="utf-8")


# ------------------------------------------------------------------------------------ data
def figure1_box():
    """The box of Figure 1 of the paper, on a path with 14 vertices."""
    lower = np.array([4, 1, 3, 6, 2, 5, 7, 3, 1, 4, 6, 5, 2, 4], dtype=float)
    upper = np.array([6, 2, 7, 8, 5, 6, 9, 7, 3, 8, 7, 9, 6, 6], dtype=float)
    return sb.path_edges(14), lower, upper


def banner_box(n: int = 60, seed: int = 24):
    """A random box on a path: a smooth profile plus noise, with intervals of varying width."""
    rng = np.random.default_rng(seed)
    x = np.linspace(0.0, 1.0, n)
    profile = (np.sin(2 * np.pi * (1.3 * x + rng.random())) + 0.55 * np.sin(2 * np.pi * (3.1 * x + rng.random()))
               + 0.35 * np.sin(2 * np.pi * (7.3 * x + rng.random())) + 0.3 * rng.standard_normal(n))
    half = 0.18 + 0.55 * rng.random(n) ** 2
    return sb.path_edges(n), profile - half, profile + half


# ------------------------------------------------------------------------------------ banner
def banner(theme: str) -> str:
    c = THEMES[theme]
    W, H = 960, 236
    edges, lo, up = banner_box()
    fU = sb.reconstruct_erosion(edges, lo, up)
    bars = sb.image_barcode0(edges, lo, up)
    assert np.array_equal(bars, sb.barcode0(edges, fU))                   # Theorem 5
    n = lo.size
    vmin, vmax = float(lo.min()) - 0.15, float(up.max()) + 0.15
    top, bottom = 34.0, 204.0
    x0, x1 = 44.0, 744.0
    X = np.linspace(x0, x1, n)

    def Y(v):
        return bottom - (v - vmin) / (vmax - vmin) * (bottom - top)

    out = [f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="{c["panel"]}" stroke="{c["border"]}"/>']
    for v in np.linspace(vmin, vmax, 6)[1:-1]:
        out.append(f'<line x1="{num(x0 - 14)}" x2="{W - 28}" y1="{num(Y(v))}" y2="{num(Y(v))}" stroke="{c["grid"]}"/>')
    out += [f'<rect x="{num(X[i] - 3)}" y="{num(Y(up[i]))}" width="6" height="{num(Y(lo[i]) - Y(up[i]))}" rx="3" '
            f'fill="{c["entered"]}"/>' for i in range(n)]
    pts = " ".join(f"{num(X[i])},{num(Y(fU[i]))}" for i in range(n))
    out.append(f'<polyline points="{pts}" fill="none" stroke="{c["blue"]}" stroke-width="2" stroke-linejoin="round"/>')
    out += [f'<circle cx="{num(X[i])}" cy="{num(Y(fU[i]))}" r="2.6" fill="{c["blue"]}"/>' for i in range(n)]

    lane = 792.0                                         # the barcode, vertical, on the same value axis
    gap = min((W - 52 - lane) / max(len(bars) - 1, 1), 16.0)
    out.append(f'<line x1="{num(lane - 24)}" x2="{num(lane - 24)}" y1="{num(top - 6)}" y2="{num(bottom + 4)}" '
               f'stroke="{c["border"]}"/>')
    for k, (b, d) in enumerate(bars):
        xk = lane + k * gap
        yd = Y(d) if np.isfinite(d) else top - 2
        out.append(f'<line x1="{num(xk)}" x2="{num(xk)}" y1="{num(Y(b))}" y2="{num(yd)}" stroke="{c["blue"]}" stroke-width="5"/>')
        if not np.isfinite(d):
            out.append(f'<path d="M{num(xk - 5)} {num(yd + 1)}h10l-5-8z" fill="{c["blue"]}"/>')

    left = np.arange(n) < 0.45 * n                     # label a wide box on the left, just above it
    i_box = int(np.argmax(np.where(left, up - lo, -np.inf)))
    out.append(text(X[i_box], Y(up[i_box]) - 9, "box $[ℓ, u]$", 12.5, c["muted"], anchor="middle"))
    out.append(text(lane - 10, bottom + 22, "$Bar_0(u ≥ ℓ)$", 12.5, c["muted"]))
    i_lab = int(np.argmin(np.abs(X - (x0 + 0.17 * (x1 - x0)))))
    out.append(text(X[i_lab], Y(fU[i_lab]) + 24, "$f_U$", 14, c["blue"]))
    desc = (f"A box on a path with {n} vertices, drawn as vertical intervals; the function f_U computed from it by "
            f"subbarcode.reconstruct_erosion; and, on the same value axis, the degree-0 barcode of f_U, which equals "
            f"the image barcode of the box ({len(bars)} bars, one of them infinite).")
    return svg(W, H, "\n".join(out), "A box, the function f_U and the image barcode", desc)


# ------------------------------------------------------------------------------------ attainment map
TABLE1 = [   # complex, degree, rows of (status, attainment, result, witness): Table 1 of the paper
    ("any complex", "$0$", [("ok", "always", "Theorem 5", "$f_U$, near-linear")]),
    ("full subcomplex of $S^d$", "$d − 1$", [("ok", "always", "Theorem 8", "$f_D$, near-linear")]),
    ("triangulated $S^d$, $d ≥ 3$", "$1, …, d − 2$", [("bad", "can fail, even for counts", "Theorem 21", "")]),
    ("graph", "$1$", [("ok", "always", "Proposition 15", "$u$")]),
    ("compact surface", "$1$", [("ok", "finite bars always", "Theorem 10", "$f_D$, near-linear"),
                                ("warn", "every box iff planar", "Theorem 11", ""),
                                ("info", "decided in polynomial time", "Theorem 13", "at most $n + 1$ candidates")]),
    ("2-complex", "$1$", [("bad", "can fail, even for counts", "Examples 18, 20", "")]),
]


def attainment(theme: str) -> str:
    c = THEMES[theme]
    W = 960
    col = dict(complex=24, degree=258, status=352, result=618, witness=746)
    row_h, sub_h = 46, 34
    out = []
    for key, label in (("complex", "complex"), ("degree", "degree $k$"), ("status", "$Bar_k(u ≥ ℓ)$ attained"),
                       ("result", "in the paper"), ("witness", "attaining function")):
        out.append(text(col[key], 36, label, 12, c["muted"], weight="600"))
    out.append(f'<line x1="16" x2="{W - 16}" y1="50" y2="50" stroke="{c["border"]}"/>')
    y = 50.0
    for r, (complex_, degree, entries) in enumerate(TABLE1):
        mid0 = y + row_h / 2
        out.append(text(col["complex"], mid0 + 5, complex_, 14.5, c["ink"]))
        out.append(text(col["degree"], mid0 + 5, degree, 14.5, c["ink"]))
        for j, (kind, label, result, witness) in enumerate(entries):
            mid = mid0 + j * sub_h
            fg, bg = c[kind], c[kind + "_bg"]
            pill = 40 + width(label, 13, bold=True)
            out.append(f'<rect x="{col["status"]}" y="{num(mid - 13)}" width="{num(pill)}" height="26" rx="13" '
                       f'fill="{bg}" stroke="{fg}" stroke-opacity=".35"/>')
            out.append(status_icon(kind, col["status"] + 16, mid, fg))
            out.append(text(col["status"] + 29, mid + 4.6, label, 13, fg, weight="600"))
            out.append(text(col["result"], mid + 5, result, 13.5, c["muted"]))
            if witness:
                out.append(text(col["witness"], mid + 5, witness, 13.5, c["ink"]))
        y += row_h + (len(entries) - 1) * sub_h
        last = r == len(TABLE1) - 1
        out.append(f'<line x1="16" x2="{W - 16}" y1="{num(y)}" y2="{num(y)}" stroke="{c["border"]}" '
                   f'stroke-opacity="{1 if last else .55}"/>')
    foot = y + 26
    out.append(text(24, foot, "Table 1 of the paper. Near-linear means $O(n log n + m α(n))$ time for $n$ vertices and "
                    "$m$ edges.", 12, c["muted"]))
    H = int(foot + 16)
    desc = ("Table 1 of the paper. Degree 0, any complex: always attained (Theorem 5), by f_U in near-linear time. "
            "Degree d-1, full subcomplex of a triangulated d-sphere: always (Theorem 8), by f_D. Degrees 1 to d-2 on "
            "triangulated d-spheres, d at least 3: can fail, even for counts (Theorem 21). Graphs, degree 1: always "
            "(Proposition 15), by u. Compact surfaces, degree 1: finite bars always (Theorem 10), by f_D; every box "
            "if and only if the surface is planar (Theorem 11); decided in polynomial time with at most n+1 "
            "candidates (Theorem 13). 2-complexes, degree 1: can fail, even for counts (Examples 18 and 20).")
    body = f'<rect width="{W}" height="{H}" fill="{c["bg"]}"/>\n' + "\n".join(out)
    return svg(W, H, body, "Where the sub-barcode bound is attained", desc)


# ------------------------------------------------------------------------------------ animation
class Clock:
    """One loop of an SMIL animation. Every animate element shares the loop length, so all of them
    stay in step however long the page is open."""

    def __init__(self, cycle: float):
        self.cycle = cycle

    def times(self, *seconds: float) -> str:
        vals = [min(max(s / self.cycle, 0.0), 1.0) for s in seconds]
        for i in range(1, len(vals)):                   # strictly increasing, as some renderers require
            vals[i] = max(vals[i], vals[i - 1] + 1e-4)
        return ";".join(f"{v:.4f}" for v in vals)

    def animate(self, attr: str, values, seconds, discrete: bool = False) -> str:
        vals = ";".join(v if isinstance(v, str) else num(v) for v in values)
        mode = ' calcMode="discrete"' if discrete else ""
        return (f'<animate attributeName="{attr}" dur="{num(self.cycle)}s" repeatCount="indefinite" '
                f'keyTimes="{self.times(*seconds)}" values="{vals}"{mode}/>')

    def appear(self, at: float, ramp: float = 0.12) -> str:
        return self.animate("opacity", [0, 0, 1, 1], [0, at, at + ramp, self.cycle])


# The sweep stops at every value where something happens and says what happened. The sentences
# describe the box of Figure 1; sweep() asserts the facts they state before drawing them.
NARRATION = [
    (0, "The threshold $t$ rises. A vertex enters $K[ℓ ≤ t]$ once $t ≥ ℓ(v)$."),
    (1, "Vertices 1 and 8 enter. No vertex has $u(v) ≤ t$ yet, so nothing is assigned."),
    (2, "$u(1) ≤ 2$ activates the component {1}: $f_U(1) = 2$, and a bar is born."),
    (3, "Vertex 2 joins the active component. $u(8) ≤ 3$ activates {7, 8}: a second bar."),
    (4, "Vertices 0 and 9 join active components; {12, 13} is still inactive."),
    (5, "$u(4) ≤ 5$ activates {4, 5}: a third bar is born."),
    (6, "Vertex 3 merges {4, 5} into an older component, so [5, 6) ends. Vertex 10 joins {11, 12, 13} to an active component: $f_U = 6$ on all four."),
    (7, "Vertex 6 merges the last two components, so the younger bar, [3, 7), ends."),
    (10, "Every vertex has its value. $Bar_0(f_U) = Bar_0(u ≥ ℓ)$, bar for bar (Theorem 5)."),
]


def _check_narration(lo, up, fU, bars) -> None:
    assert fU.tolist() == [4, 2, 3, 6, 5, 5, 7, 3, 3, 4, 6, 6, 6, 6]
    assert bars.tolist() == [[2, np.inf], [3, 7], [5, 6]]
    assert sorted(np.flatnonzero(lo == 1)) == [1, 8] and up.min() == 2 and up[1] == 2 and up[8] == 3 and up[4] == 5
    assert lo[2] == lo[7] == 3 and lo[0] == lo[9] == lo[13] == 4 and lo[5] == lo[11] == 5 and lo[3] == lo[10] == 6
    assert lo[6] == 7 and min(up[11:14]) == 6 and lo[12] == 2


def sweep(theme: str) -> str:
    c = THEMES[theme]
    W, H = 960, 520
    edges, lo, up = figure1_box()
    fU = sb.reconstruct_erosion(edges, lo, up)
    bars = sb.image_barcode0(edges, lo, up)
    assert np.array_equal(bars, sb.barcode0(edges, fU))                   # Theorem 5
    _check_narration(lo, up, fU, bars)
    n, tmax = lo.size, 10.0

    # schedule: (time, value) breakpoints of the threshold, which rises quickly and stops at each event
    stops = [s for s, _ in NARRATION]
    first_hold, hold, last_hold, rise = 2.2, 2.9, 3.4, 0.45
    points, clock_t = [(0.0, 0.0)], first_hold
    points.append((clock_t, 0.0))
    for a, b in zip(stops, stops[1:]):
        clock_t += rise * (b - a)
        points.append((clock_t, float(b)))
        clock_t += last_hold if b == stops[-1] else hold
        points.append((clock_t, float(b)))
    hold_end, gone = clock_t, clock_t + 0.5
    clock = Clock(gone + 0.1)

    def at(v: float) -> float:
        """The moment the threshold reaches the value v."""
        for (t1, v1), (t2, v2) in zip(points, points[1:]):
            if v2 > v1 and v1 <= v <= v2:
                return t1 + (v - v1) / (v2 - v1) * (t2 - t1)
        return 0.0

    def track(a: float, b: float, f):
        """Times and values of f(threshold) while the threshold goes from a to b."""
        ta, tb = at(a), at(b)
        inner = [(t, f(v)) for t, v in points if ta < t < tb]
        return [ta] + [t for t, _ in inner] + [tb], [f(a)] + [y for _, y in inner] + [f(b)]

    def Y(t):
        return 368.0 - 28.0 * t

    def X(v):
        return 104.0 + 38.0 * v

    axis_x, lane_x, gy = 70.0, 690.0, 420.0
    out = [f'<rect width="{W}" height="{H}" fill="{c["bg"]}"/>']

    lx, ly = axis_x, 30.0                                # legend
    out.append(f'<rect x="{num(lx)}" y="{num(ly - 11)}" width="10" height="16" rx="3" fill="{c["box_fill"]}" stroke="{c["box"]}"/>')
    out.append(text(lx + 18, ly + 2, "box $[ℓ(v), u(v)]$", 13, c["muted"]))
    lx += 36 + width("box [ℓ(v), u(v)]", 13)
    out.append(f'<rect x="{num(lx)}" y="{num(ly - 11)}" width="10" height="16" rx="3" fill="{c["entered"]}"/>')
    out.append(text(lx + 18, ly + 2, "$ℓ(v) ≤ t$", 13, c["muted"]))
    lx += 36 + width("ℓ(v) ≤ t", 13)
    out.append(f'<line x1="{num(lx - 2)}" x2="{num(lx + 12)}" y1="{num(ly - 3)}" y2="{num(ly - 3)}" stroke="{c["orange"]}" '
               f'stroke-width="3" stroke-linecap="round"/>')
    out.append(text(lx + 20, ly + 2, "$u(v) ≤ t$", 13, c["muted"]))
    lx += 38 + width("u(v) ≤ t", 13)
    out.append(f'<rect x="{num(lx)}" y="{num(ly - 11)}" width="10" height="16" rx="3" fill="{c["blue_fill"]}"/>')
    out.append(f'<circle cx="{num(lx + 5)}" cy="{num(ly - 3)}" r="3.4" fill="{c["blue"]}"/>')
    out.append(text(lx + 18, ly + 2, "the component of $v$ meets $K[u ≤ t]$, so $f_U(v) = t$", 13, c["muted"]))
    out.append(text(lane_x - 10, 62, "$Bar_0(f_U) = Bar_0(u ≥ ℓ)$", 13.5, c["ink"]))

    for t in range(0, 11, 2):                           # axes
        out.append(f'<line x1="{num(axis_x)}" x2="{W - 40}" y1="{num(Y(t))}" y2="{num(Y(t))}" stroke="{c["grid"]}"/>')
        out.append(text(axis_x - 10, Y(t) + 4.5, str(t), 12, c["faint"], anchor="end"))
    out.append(f'<line x1="{num(axis_x)}" x2="{num(axis_x)}" y1="{num(Y(tmax) - 6)}" y2="{num(Y(0))}" stroke="{c["box"]}"/>')
    out.append(f'<line x1="{num(lane_x - 22)}" x2="{num(lane_x - 22)}" y1="{num(Y(tmax) - 6)}" y2="{num(Y(0))}" '
               f'stroke="{c["border"]}"/>')
    for v in range(n):                                  # the box
        out.append(f'<rect x="{num(X(v) - 7)}" y="{num(Y(up[v]))}" width="14" height="{num(Y(lo[v]) - Y(up[v]))}" rx="3" '
                   f'fill="{c["box_fill"]}" stroke="{c["box"]}"/>')
    for v in range(n - 1):                              # the graph K, a path
        out.append(f'<line x1="{num(X(v) + 6)}" x2="{num(X(v + 1) - 6)}" y1="{gy}" y2="{gy}" stroke="{c["box"]}" '
                   f'stroke-dasharray="2 3"/>')
    for v in range(n):
        out.append(f'<circle cx="{num(X(v))}" cy="{gy}" r="5.5" fill="{c["bg"]}" stroke="{c["box"]}"/>')
        out.append(text(X(v), gy + 26, str(v), 11.5, c["faint"], anchor="middle"))
    out.append(text(axis_x - 10, gy + 4.5, "$K$", 13, c["muted"], anchor="end"))
    out.append(f'<line x1="16" x2="{W - 16}" y1="{gy + 44}" y2="{gy + 44}" stroke="{c["border"]}"/>')

    dyn = []
    # the values <= t, which uncover the boxes from below as the threshold rises
    ys = track(0.0, tmax, Y)
    times = [0] + ys[0] + [gone + 0.05, clock.cycle]
    dyn.append(f'<clipPath id="below"><rect x="0" y="{num(Y(0))}" width="{W}" height="0">'
               + clock.animate("y", [Y(0)] + ys[1] + [Y(tmax), Y(0)], times)
               + clock.animate("height", [0] + [Y(0) - y for y in ys[1]] + [Y(0) - Y(tmax), 0], times)
               + "</rect></clipPath>")
    fills = []
    for v in range(n):
        geom = f'x="{num(X(v) - 7)}" y="{num(Y(up[v]))}" width="14" height="{num(Y(lo[v]) - Y(up[v]))}" rx="3"'
        fills.append(f'<rect {geom} fill="{c["entered"]}"/>')
        fills.append(f'<rect {geom} fill="{c["blue_fill"]}" opacity="0">{clock.appear(at(fU[v]))}</rect>')
    dyn.append('<g clip-path="url(#below)">' + "".join(fills) + "</g>")
    for v in range(n):                                  # u(v) <= t
        dyn.append(f'<line x1="{num(X(v) - 8)}" x2="{num(X(v) + 8)}" y1="{num(Y(up[v]))}" y2="{num(Y(up[v]))}" '
                   f'stroke="{c["orange"]}" stroke-width="3" stroke-linecap="round" opacity="0">{clock.appear(at(up[v]))}</line>')
    for v in range(n - 1):                              # f_U, a segment once both ends are assigned
        x1, y1, x2, y2 = X(v), Y(fU[v]), X(v + 1), Y(fU[v + 1])
        length = float(np.hypot(x2 - x1, y2 - y1))
        on = at(max(fU[v], fU[v + 1])) + 0.15
        dyn.append(f'<line x1="{num(x1)}" y1="{num(y1)}" x2="{num(x2)}" y2="{num(y2)}" stroke="{c["blue"]}" '
                   f'stroke-width="2.2" stroke-dasharray="{num(length)}" stroke-dashoffset="{num(length)}">'
                   + clock.animate("stroke-dashoffset", [length, length, 0, 0], [0, on, on + 0.35, clock.cycle]) + "</line>")
    for v in range(n):
        on = at(fU[v])
        dyn.append(f'<circle cx="{num(X(v))}" cy="{num(Y(fU[v]))}" r="0" fill="{c["blue"]}">'
                   + clock.animate("r", [0, 0, 6.5, 4.6, 4.6], [0, on, on + 0.14, on + 0.32, clock.cycle]) + "</circle>")
    for v in range(n - 1):                              # the graph: grey once in K[l <= t], blue once assigned
        seg = f'x1="{num(X(v) + 6)}" x2="{num(X(v + 1) - 6)}" y1="{gy}" y2="{gy}"'
        dyn.append(f'<line {seg} stroke="{c["faint"]}" stroke-width="2" opacity="0">{clock.appear(at(max(lo[v], lo[v + 1])))}</line>')
        dyn.append(f'<line {seg} stroke="{c["blue"]}" stroke-width="2.4" opacity="0">{clock.appear(at(max(fU[v], fU[v + 1])))}</line>')
    for v in range(n):
        dot = f'cx="{num(X(v))}" cy="{gy}" r="5.5"'
        dyn.append(f'<circle {dot} fill="{c["faint"]}" opacity="0">{clock.appear(at(lo[v]))}</circle>')
        dyn.append(f'<circle {dot} fill="{c["blue"]}" opacity="0">{clock.appear(at(fU[v]))}</circle>')
    for k, (b, d) in enumerate(bars):                   # the barcode grows with the threshold
        xk = lane_x + 20 + 74 * k
        dd = min(d, tmax)
        yb, yd = Y(b), Y(dd)
        times, ys = track(b, dd, Y)
        dyn.append(f'<line x1="{num(xk)}" x2="{num(xk)}" y1="{num(yb)}" y2="{num(yb)}" stroke="{c["blue"]}" '
                   f'stroke-width="7" opacity="0">{clock.appear(at(b), 0.05)}'
                   + clock.animate("y2", [yb] + ys + [yd], [0] + times + [clock.cycle]) + "</line>")
        if np.isfinite(d):                              # beside the middle of the bar, clear of the threshold
            label, label_y = f"[{b:g}, {d:g})", (yb + yd) / 2 + 4.5
        else:
            label, label_y = f"[{b:g}, ∞)", yd + 18
            dyn.append(f'<path d="M{num(xk - 7)} {num(yd + 1)}h14l-7-10z" fill="{c["blue"]}" opacity="0">'
                       f'{clock.appear(at(dd))}</path>')
        dyn.append(f'<g opacity="0">{clock.appear(at(dd) + 0.15)}{text(xk + 12, label_y, label, 13, c["ink"], family=MONO)}</g>')
    tag = (f'<line x1="{num(axis_x)}" x2="{W - 36}" y1="{num(Y(0))}" y2="{num(Y(0))}" stroke="{c["ink"]}" '
           f'stroke-width="1.4" stroke-dasharray="6 4" opacity=".75"/>'
           f'<rect x="{W - 34}" y="{num(Y(0) - 11)}" width="24" height="22" rx="6" fill="{c["ink"]}"/>'
           + text(W - 22, Y(0) + 5, "$t$", 15, c["bg"], anchor="middle"))
    times, ys = track(0.0, tmax, Y)
    shifts = ";".join(f"0 {num(y - Y(0))}" for y in [Y(0)] + ys + [Y(tmax), Y(0)])
    dyn.append(f'<g>{tag}<animateTransform attributeName="transform" type="translate" dur="{num(clock.cycle)}s" '
               f'repeatCount="indefinite" keyTimes="{clock.times(0, *times, gone + 0.05, clock.cycle)}" '
               f'values="{shifts}"/></g>')

    # the narration, one sentence (at most two lines) while the threshold rests at each stop
    ny = gy + 72
    for s, sentence in NARRATION:
        begin = at(s) if s else 0.0
        end = next((t for t, v in points if v == s and t > begin), hold_end)
        lines, current = [], ""
        for word in sentence.split(" "):
            trial = (current + " " + word).strip()
            if width(trial.replace("$", ""), 13.5) > W - 200 and current:
                lines.append(current)
                current = word
            else:
                current = trial
        lines.append(current)
        label = "start" if s == 0 else f"t = {s:g}"
        block = (f'<rect x="{num(axis_x)}" y="{num(ny - 15)}" width="62" height="22" rx="6" fill="{c["panel"]}" '
                 f'stroke="{c["border"]}"/>' + text(axis_x + 31, ny + 0.5, label, 12, c["muted"], anchor="middle", family=MONO))
        block += "".join(text(axis_x + 78, ny + 21 * j, line, 13.5, c["ink"]) for j, line in enumerate(lines))
        fade_in = begin + (0.0 if s == 0 else 0.1)
        dyn.append(f'<g opacity="0">' + clock.animate("opacity", [0, 0, 1, 1, 0, 0],
                   [0, fade_in, fade_in + 0.2, end - 0.15, end, clock.cycle]) + block + "</g>")

    fade = clock.animate("opacity", [1, 1, 0, 0], [0, hold_end, gone, clock.cycle])
    body = "\n".join(out) + f"\n<g>{fade}\n" + "\n".join(dyn) + "\n</g>"
    desc = ("An animation of the sweep that computes f_U for the box of Figure 1 of the paper, on a path with 14 "
            "vertices. A threshold t rises from 0 to 10 and stops at every value where something happens. "
            + " ".join(f"At t = {s}: {re.sub(r'[$]', '', line)}" for s, line in NARRATION[1:])
            + " On the right the degree-0 barcode of f_U grows with t: [2, inf), [3, 7) and [5, 6).")
    return svg(W, H, body, "Computing f_U by one upward sweep", desc)


# ------------------------------------------------------------------------------------ terminal replay
TERM = dict(bg="#0d1117", bar="#161b22", border="#30363d", text="#e6edf3", muted="#8b949e", green="#3fb950",
            blue="#79c0ff")
DOTS = re.compile(r"^(\.+)([\s\u00a0]+)(\[[\s\u00a0]*\d+%\])$")


def record_check() -> list[str]:
    """Run the recipe of `make check` and return what the terminal shows, with `python` as the interpreter."""
    recipe, inside = [], False
    for line in (ROOT / "Makefile").read_text(encoding="utf-8").splitlines():
        if line.startswith("check:"):
            inside = True
        elif inside and line.startswith("\t"):
            recipe.append(line.strip())
        elif inside:
            break
    env = {**os.environ, "COLUMNS": "80", "PYTHONDONTWRITEBYTECODE": "1"}
    shown = ["$ make check"]
    for command in recipe:
        shown.append(command.replace("$(PYTHON)", "python"))
        argv = command.replace("$(PYTHON)", sys.executable).split()
        run = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, env=env)
        if run.returncode != 0:
            raise SystemExit(f"`{command}` failed, so there is nothing to record:\n{run.stdout}{run.stderr}")
        shown += [line.rstrip() for line in run.stdout.splitlines() if line.strip()]
    return shown + ["$"]


def _keep_spaces(s: str) -> str:
    """Runs of spaces as no-break spaces: SVG renderers collapse ordinary ones, whatever xml:space says."""
    return re.sub(r" {2,}", lambda m: "\u00a0" * len(m.group(0)), s)


def terminal(lines: list[str]) -> str:
    T = TERM
    lines = [_keep_spaces(line) for line in lines]
    W, lh, pad, bar_h, cw = 880, 20.0, 22.0, 36.0, 7.8      # cw: advance of 13 px monospace, for the typing
    H = int(bar_h + 2 * pad + lh * (len(lines) - 1) + 6)

    # when each line appears: the command is typed, each step prints, pytest prints its dots one by one
    type_at = [0.5 + 0.09 * k for k in range(1, len(lines[0]) - 1)]
    t, events = type_at[-1] + 0.45, []
    for i, line in enumerate(lines[1:], start=1):
        m = DOTS.match(line)
        if m:
            reveal = 0.018 * len(m.group(1))
            events.append((i, t + 0.1, reveal))
            t += 0.1 + reveal
        else:
            t += 0.42 if line.startswith("python ") else 0.5 if line == "$" else 0.16
            events.append((i, t, None))
    clock = Clock(t + 4.5)

    def colour(line: str) -> str:
        if line.startswith("$"):
            return f'<tspan fill="{T["green"]}">$</tspan>{escape(line[1:])}'
        if line.startswith("python "):
            return f'<tspan fill="{T["muted"]}">{escape(line)}</tspan>'
        if line.startswith("OK:"):
            return f'<tspan fill="{T["green"]}" font-weight="700">OK:</tspan>{escape(line[3:])}'
        if re.match(r"^\d+ passed", line):
            return f'<tspan fill="{T["green"]}" font-weight="700">{escape(line)}</tspan>'
        m = re.match(r"^(code fingerprint|reported run)([\s\u00a0]+)([0-9a-f]{64})$", line)
        if m:
            return f'{escape(m.group(1))}{m.group(2)}<tspan fill="{T["blue"]}">{m.group(3)}</tspan>'
        return escape(line)

    out = [f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="10" fill="{T["bg"]}" stroke="{T["border"]}"/>',
           f'<path d="M.5 {bar_h}V10.5a10 10 0 0 1 10-10h{W - 21}a10 10 0 0 1 10 10V{bar_h}z" fill="{T["bar"]}"/>',
           f'<line x1=".5" x2="{W - .5}" y1="{bar_h}" y2="{bar_h}" stroke="{T["border"]}"/>']
    out += [f'<circle cx="{20 + 18 * k}" cy="{bar_h / 2}" r="5.5" fill="{T["border"]}"/>' for k in range(3)]
    out.append(f'<text x="{W / 2}" y="{bar_h / 2 + 4.5}" font-family="{SANS}" font-size="12.5" fill="{T["muted"]}" '
               f'text-anchor="middle">subbarcode-attainment</text>')
    out.append(f'<g font-family="{MONO}" font-size="13" fill="{T["text"]}" xml:space="preserve" style="white-space:pre">')
    x0, y0 = pad, bar_h + pad + 9
    # the prompt and the typed command, revealed one character at a time behind a moving cursor
    widths = [0] + [cw * k for k in range(1, len(type_at) + 1)]
    out.append(f'<text x="{num(x0)}" y="{num(y0)}"><tspan fill="{T["green"]}">$</tspan></text>')
    out.append(f'<clipPath id="typed"><rect x="{num(x0 + 2 * cw)}" y="{num(y0 - 14)}" width="0" height="20">'
               + clock.animate("width", widths, [0] + type_at, discrete=True) + "</rect></clipPath>")
    out.append(f'<text x="{num(x0)}" y="{num(y0)}" clip-path="url(#typed)">{escape(lines[0])}</text>')
    out.append(f'<rect x="{num(x0 + 2 * cw)}" y="{num(y0 - 12)}" width="{num(cw)}" height="16" fill="{T["text"]}" opacity=".85">'
               + clock.animate("x", [x0 + 2 * cw + w for w in widths], [0] + type_at, discrete=True)
               + clock.animate("opacity", [.85, 0], [0, type_at[-1] + 0.3], discrete=True) + "</rect>")
    for i, at, reveal in events:
        y, line = y0 + lh * i, lines[i]
        if reveal is None:
            content = f'<text x="{num(x0)}" y="{num(y)}">{colour(line)}</text>'
            if line == "$":
                content += (f'<rect x="{num(x0 + 2 * cw)}" y="{num(y - 12)}" width="{num(cw)}" height="16" fill="{T["text"]}">'
                            f'<animate attributeName="opacity" dur="1.1s" repeatCount="indefinite" calcMode="discrete" '
                            f'keyTimes="0;.5" values=".85;0"/></rect>')
            out.append(f'<g opacity="0">{clock.appear(at, 0.01)}{content}</g>')
            continue
        dots, space, percent = DOTS.match(line).groups()
        full = cw * len(dots) + 1
        out.append(f'<clipPath id="row{i}"><rect x="{num(x0)}" y="{num(y - 14)}" width="0" height="20">'
                   + clock.animate("width", [0, 0, full, full], [0, at, at + reveal, clock.cycle]) + "</rect></clipPath>")
        out.append(f'<g opacity="0">{clock.appear(at, 0.01)}<text x="{num(x0)}" y="{num(y)}" clip-path="url(#row{i})" '
                   f'fill="{T["green"]}">{dots}</text></g>')
        out.append(f'<g opacity="0">{clock.appear(at + reveal, 0.01)}<text x="{num(x0 + cw * len(dots + space))}" '
                   f'y="{num(y)}" fill="{T["muted"]}">{escape(percent)}</text></g>')
    out.append("</g>")
    desc = "A replay of make check, recorded by scripts/build_assets.py. The terminal shows:\n" + "\n".join(lines)
    return svg(W, H, "\n".join(out), "make check", desc)


# ------------------------------------------------------------------------------------ pipeline
def facts() -> dict:
    """The numbers shown by the pipeline and the badges, read from the repository."""
    import check_claims
    import notebook_fingerprint
    results = ROOT / "results"
    report = json.loads((results / "logs" / "reproducibility_report.json").read_text(encoding="utf-8"))
    numbers = json.loads((results / "paper_numbers.json").read_text(encoding="utf-8"))
    setup = next(v for k, v in numbers.items() if k.startswith("Paper Section 7 and Appendix D"))
    rows = check_claims.claims(check_claims.Run(results))
    collected = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"],
                               cwd=ROOT, capture_output=True, text=True,
                               env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    per_file = re.findall(r"^\S+\.py: (\d+)$", collected.stdout, flags=re.M)    # the form printed with -qq
    total = re.search(r"(\d+) tests? collected", collected.stdout)
    tests = sum(map(int, per_file)) if per_file else int(total.group(1))
    assert notebook_fingerprint.fingerprint() == notebook_fingerprint.REPORTED_RUN
    return dict(files=len((results / "SHA256SUMS").read_text(encoding="utf-8").splitlines()),
                run_checksums=len(report["checksums"]), profile=report["profile"], config=report["config_hash"],
                seed=setup["seed"], minutes=setup["session_minutes"], claims=len(rows),
                claims_ok=sum(r[2] == r[3] for r in rows), tests=tests)


def fits(s: str, size: float, room: float, bold: bool = False) -> str:
    """Return s after checking that it fits in `room` pixels, measured in the wide reference face."""
    measured = width(re.sub(r"[$_{}]", "", s), size, bold)
    if measured > room:
        raise ValueError(f"{s!r} needs {measured:.0f} px but has {room:.0f}")
    return s


def pipeline(theme: str, f: dict) -> str:
    c = THEMES[theme]
    W, H = 960, 352
    cw, ch, xs = 232, 68, (60, 384, 708)                # three columns of cards, labels in the left margin
    out = [f'<rect width="{W}" height="{H}" fill="{c["bg"]}"/>',
           f'<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
           f'orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="{c["muted"]}"/></marker></defs>']

    def card(x, y, icon, title, sub):
        return (f'<rect x="{num(x)}" y="{num(y)}" width="{cw}" height="{ch}" rx="12" fill="{c["panel"]}" stroke="{c["border"]}"/>'
                + glyph(icon, x + 15, y + ch / 2 - 14, 28, c["ink"])
                + text(x + 56, y + ch / 2 - 3, fits(title, 14.5, cw - 66, True), 14.5, c["ink"], weight="600", family=MONO)
                + text(x + 56, y + ch / 2 + 16, fits(sub, 12.5, cw - 66), 12.5, c["muted"]))

    def chip(x, y, target, result):
        return (f'<rect x="{num(x)}" y="{num(y)}" width="{cw}" height="50" rx="10" fill="{c["ok_bg"]}" '
                f'stroke="{c["ok"]}" stroke-opacity=".45"/>' + status_icon("ok", x + 18, y + 25, c["ok"])
                + text(x + 34, y + 21, fits(target, 13, cw - 44, True), 13, c["ink"], weight="600", family=MONO)
                + text(x + 34, y + 39, fits(result, 12.5, cw - 44), 12.5, c["muted"]))

    def arrow(xa, xb, y, label, both=False):
        start = ' marker-start="url(#arrow)"' if both else ""
        return (f'<line x1="{num(xa)}" x2="{num(xb)}" y1="{num(y)}" y2="{num(y)}" stroke="{c["muted"]}" '
                f'stroke-width="1.4"{start} marker-end="url(#arrow)"/>'
                + text((xa + xb) / 2, y - 9, fits(label, 11.5, xb - xa), 11.5, c["muted"], anchor="middle"))

    def dashed(x1, y1, x2, y2):
        return (f'<line x1="{num(x1)}" y1="{num(y1)}" x2="{num(x2)}" y2="{num(y2)}" stroke="{c["ok"]}" '
                f'stroke-opacity=".6" stroke-width="1.4" stroke-dasharray="3 4"/>')

    def side(label, y_mid):
        return (f'<text transform="translate(30 {num(y_mid)}) rotate(-90)" font-family="{SANS}" font-size="10.5" '
                f'font-weight="600" letter-spacing="1.4" fill="{c["faint"]}" text-anchor="middle">{label}</text>')

    y1, y2, y3 = 24, 128, 258
    out.append(side("RUN", y1 + ch / 2))
    out.append(card(xs[0], y1, "notebook", "notebook/", "24 sections, 67 cells"))
    out.append(card(xs[1], y1, "archive", "results/", f"{f['profile']} run, seed {f['seed']}"))
    out.append(card(xs[2], y1, "paper", "the paper", "tables, figures, numbers"))
    out.append(arrow(xs[0] + cw + 6, xs[1] - 8, y1 + ch / 2, f"{f['minutes']} min"))
    out.append(arrow(xs[1] + cw + 6, xs[2] - 8, y1 + ch / 2, "read by"))
    out.append(side("CHECKS", y2 + 25))
    checks = (("make fingerprint", "same code as the run"),
              ("make verify", f"{f['files']} files, {f['run_checksums']} run checksums"),
              ("make claims", f"{f['claims_ok']} of {f['claims']} numbers agree"))
    for x, (target, result) in zip(xs, checks):
        out.append(dashed(x + cw / 2, y1 + ch + 2, x + cw / 2, y2 - 2))
        out.append(chip(x, y2, target, result))
    out.append(f'<line x1="16" x2="{W - 16}" y1="{y3 - 34}" y2="{y3 - 34}" stroke="{c["border"]}" stroke-dasharray="2 4"/>')
    out.append(side("LIBRARY", y3 + ch / 2))
    out.append(card(xs[0], y3, "package", "src/subbarcode", "$f_U$, $f_D$, image barcodes"))
    out.append(card(xs[1], y3, "matrix", "tests/oracle.py", "brute-force GF(2) ranks"))
    out.append(arrow(xs[0] + cw + 8, xs[1] - 8, y3 + ch / 2, "compared", both=True))
    out.append(dashed(xs[1] + cw + 4, y3 + ch / 2, xs[2] - 4, y3 + ch / 2))
    out.append(chip(xs[2], y3 + (ch - 50) / 2, "make test", f"{f['tests']} tests pass"))
    desc = (f"How the parts of the repository fit together. The notebook produced the archived run in results/ "
            f"({f['profile']}, {f['minutes']} minutes, seed {f['seed']}), from which every table, figure and number "
            f"of the paper is taken. make fingerprint checks that the notebook is the code of the reported run, make "
            f"verify checks the {f['files']} files against SHA256SUMS and the {f['run_checksums']} checksums the run "
            f"recorded, and make claims recomputes the {f['claims']} numbers quoted in the paper. The subbarcode "
            f"package is compared with brute-force rank computations over GF(2); make test runs {f['tests']} tests.")
    return svg(W, H, "\n".join(out), "How the repository fits together", desc)


# ------------------------------------------------------------------------------------ badges
def badge(label: str, value: str, color: str) -> str:
    """A flat badge in the manner of shields.io, drawn locally so that the README makes no requests."""
    lw, vw = round(width(label, 11) + 14), round(width(value, 11) + 14)

    def t(x, s):
        w = width(s, 11)
        return (f'<text x="{num((x - w / 2) * 10)}" y="140" transform="scale(.1)" textLength="{num(w * 10)}" '
                f'lengthAdjust="spacing">{escape(s)}</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{lw + vw}" height="20" role="img" '
            f'aria-label="{escape(label)}: {escape(value)}"><title>{escape(label)}: {escape(value)}</title>'
            f'<clipPath id="r"><rect width="{lw + vw}" height="20" rx="3"/></clipPath>'
            f'<g clip-path="url(#r)"><rect width="{lw}" height="20" fill="#30363d"/>'
            f'<rect x="{lw}" width="{vw}" height="20" fill="{color}"/></g>'
            f'<g fill="#fff" font-family="Verdana,Geneva,\'DejaVu Sans\',sans-serif" font-size="110" '
            f'text-rendering="geometricPrecision">{t(lw / 2, label)}{t(lw + vw / 2, value)}</g></svg>\n')


def badges(f: dict) -> dict[str, str]:
    return {
        "socg": badge("SoCG 2027", "submission", "#0969da"),
        "python": badge("python", "3.11 | 3.12 | 3.13", "#0969da"),
        "license": badge("license", "MIT", "#6e7781"),
        "run": badge("reported run", f"{f['profile']} · {f['config']}", "#8250df"),
        "claims": badge("paper numbers", f"{f['claims_ok']} / {f['claims']} reproduced", "#1a7f37"),
        "archive": badge("archive", "SHA-256 verified", "#1a7f37"),
        "tests": badge("tests", f"{f['tests']} passed", "#1a7f37"),
    }


# ------------------------------------------------------------------------------------ main
def previews() -> None:
    if not shutil.which("pdftoppm"):
        print("pdftoppm not found; the PNG previews of the figures are left as they are")
        return
    for pdf in sorted((ROOT / "results" / "figures").glob("*.pdf")):
        stem = ASSETS / "figures" / pdf.stem
        subprocess.run(["pdftoppm", "-png", "-r", "240", "-singlefile", str(pdf), str(stem)], check=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--no-record", action="store_true", help="keep docs/assets/terminal.svg instead of rerunning make check")
    args = ap.parse_args(argv)
    for sub in ("badges", "icons", "figures"):
        (ASSETS / sub).mkdir(parents=True, exist_ok=True)
    f = facts()
    for theme in THEMES:
        for name, make in (("banner", banner), ("attainment", attainment), ("sweep", sweep)):
            (ASSETS / f"{name}-{theme}.svg").write_text(make(theme), encoding="utf-8")
        (ASSETS / f"pipeline-{theme}.svg").write_text(pipeline(theme, f), encoding="utf-8")
    for name, content in badges(f).items():
        (ASSETS / "badges" / f"{name}.svg").write_text(content, encoding="utf-8")
    write_icons()
    if not args.no_record:
        (ASSETS / "terminal.svg").write_text(terminal(record_check()), encoding="utf-8")
    previews()
    print(f"wrote {len(list(ASSETS.rglob('*.*')))} files to {ASSETS.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
