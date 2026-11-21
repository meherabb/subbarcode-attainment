"""Regenerate every figure of the paper as a vector PDF.

Usage:  python3 make_figures.py RESULTS_DIR OUT_DIR

RESULTS_DIR is the results/ folder of the experiment bundle (it must contain
p2_memory_hierarchy.csv, degree1_fast_timing.csv and compression.csv).
Figures 1 and 2 are computed here from first principles (small exact examples).
"""
import sys, math
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("pdf")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, FancyArrowPatch

RES = Path(sys.argv[1]); OUT = Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "text.usetex": False,
    "font.family": "serif", "font.serif": ["cmr10"], "mathtext.fontset": "cm",
    "axes.formatter.use_mathtext": True, "axes.unicode_minus": False,
    "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
    "axes.linewidth": 0.5, "xtick.major.width": 0.5, "ytick.major.width": 0.5,
    "xtick.minor.width": 0.4, "ytick.minor.width": 0.4,
    "axes.spines.top": False, "axes.spines.right": False,
    "pdf.fonttype": 42, "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
})
# categorical slots (validated light-mode order), plus neutral inks
BLUE, ORANGE, AQUA, YELLOW, VIOLET = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#6250d6"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#d9d8d4"
TEXTW = 5.2  # inches, a little under the LIPIcs text width


def barcode0(adj, f):
    """Degree-0 barcode of the lower-star filtration of a graph (union-find, elder rule)."""
    n = len(f); order = sorted(range(n), key=lambda v: (f[v], v))
    parent = list(range(n)); birth = {}; present = [False] * n; bars = []
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for v in order:
        present[v] = True; birth[v] = f[v]
        for w in adj[v]:
            if not present[w]:
                continue
            a, b = find(v), find(w)
            if a == b:
                continue
            young, old = (a, b) if (birth[a], a) > (birth[b], b) else (b, a)
            if birth[young] < f[v]:
                bars.append((birth[young], f[v]))
            parent[young] = old
    roots = {find(v) for v in range(n)}
    bars += [(birth[r], math.inf) for r in roots]
    return sorted(bars)


def f_U(adj, lo, up):
    """Pointwise smallest attaining function: min over w, paths w->v of max(u(w), max of l on the path)."""
    import heapq
    n = len(lo); d = [math.inf] * n; h = []
    for v in range(n):
        d[v] = up[v]; heapq.heappush(h, (d[v], v))
    while h:
        dv, v = heapq.heappop(h)
        if dv > d[v]:
            continue
        for w in adj[v]:
            c = max(dv, lo[w])
            if c < d[w]:
                d[w] = c; heapq.heappush(h, (c, w))
    return d


# ---------------------------------------------------------------- Figure 1: f_U on a path
def figure_path():
    lo = [4, 1, 3, 6, 2, 5, 7, 3, 1, 4, 6, 5, 2, 4]
    up = [6, 2, 7, 8, 5, 6, 9, 7, 3, 8, 7, 9, 6, 6]
    n = len(lo); adj = [[w for w in (v - 1, v + 1) if 0 <= w < n] for v in range(n)]
    fu = f_U(adj, lo, up)
    assert all(l <= x <= u for l, x, u in zip(lo, fu, up))
    bl, bu, bf = barcode0(adj, lo), barcode0(adj, up), barcode0(adj, fu)
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(TEXTW, 1.75), gridspec_kw=dict(width_ratios=[1.55, 1]))
    xs = np.arange(n)
    for v in range(n):
        ax.plot([v, v], [lo[v], up[v]], color=GRID, lw=4.5, solid_capstyle="butt", zorder=1)
    ax.plot(xs, lo, ls=":", lw=0.8, color=INK2, zorder=2, label=r"$\ell$")
    ax.plot(xs, up, ls="--", lw=0.8, color=INK2, zorder=2, label=r"$u$")
    ax.plot(xs, fu, "-o", ms=3.2, lw=1.2, color=BLUE, zorder=3, label=r"$f_U$")
    ax.set_xticks(xs, [str(v) for v in xs]); ax.set_xlabel(r"vertex of the path")
    ax.set_ylabel(r"value"); ax.set_ylim(0, 10); ax.set_xlim(-0.6, n - 0.4)
    ax.legend(frameon=False, ncol=3, loc="lower left", bbox_to_anchor=(0.0, 1.0), handlelength=1.6,
              columnspacing=1.2, borderaxespad=0.1)
    rows = [(r"$\mathrm{Bar}_0(\ell)$", bl, INK2), (r"$\mathrm{Bar}_0(u)$", bu, INK2),
            (r"$\mathrm{Bar}_0(f_U)=\mathrm{Bar}_0(u\geq\ell)$", bf, BLUE)]
    y = 0; ticks = []
    top = 10.6
    for name, B, col in rows:
        start = y
        for (b, d) in sorted(B, key=lambda p: (p[0], -p[1] if math.isfinite(p[1]) else -99)):
            e = top if not math.isfinite(d) else d
            bx.plot([b, e], [y, y], color=col, lw=1.6, solid_capstyle="butt")
            if not math.isfinite(d):
                bx.annotate("", xy=(top + 0.35, y), xytext=(top - 0.1, y),
                            arrowprops=dict(arrowstyle="-|>", lw=0.8, color=col, shrinkA=0, shrinkB=0, mutation_scale=6))
            y += 1
        ticks.append(((start + y - 1) / 2, name)); y += 1.2
    bx.set_yticks([t for t, _ in ticks], [nm for _, nm in ticks]); bx.invert_yaxis()
    bx.set_xlim(0, top + 0.6); bx.set_xlabel(r"value"); bx.tick_params(axis="y", length=0)
    bx.spines["left"].set_visible(False)
    fig.tight_layout(w_pad=1.0)
    fig.savefig(OUT / "fig1_fU_path.pdf")
    plt.close(fig)
    return dict(lo=lo, up=up, fU=fu, bar_l=bl, bar_u=bu, bar_fU=bf)


# ---------------------------------------------------------------- Figure 2: certificate D (Moebius band)
def figure_certD():
    # vertex ids follow the paper: a, b, c on the boundary (fixed at 0); x, y, z interior
    P = {"b": (0, 2), "p": (0, 1), "c": (0, 0), "q": (2, 1), "a": (3, 2), "r": (4, 1),
         "p'": (6, 1), "c'": (6, 2), "b'": (6, 0)}
    T = [("b", "p", "q"), ("p", "c", "q"), ("a", "b", "q"), ("a", "q", "r"), ("c", "q", "r"),
         ("b'", "c", "r"), ("b'", "p'", "r"), ("a", "p'", "r"), ("a", "p'", "c'")]
    box = {"a": "0", "b": "0", "c": "0", "p": "[1,3]", "q": "[1,4]", "r": "[2,4]"}
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(TEXTW, 1.55), gridspec_kw=dict(width_ratios=[1.25, 1]))
    for t in T:
        ax.add_patch(Polygon([P[v] for v in t], closed=True, facecolor="#eef3fb", edgecolor=INK2, lw=0.6))
    # boundary edges drawn heavier
    for e in [("b", "a"), ("a", "c'"), ("c", "b'")]:
        (x0, y0), (x1, y1) = P[e[0]], P[e[1]]
        ax.plot([x0, x1], [y0, y1], color=INK, lw=1.4, solid_capstyle="round")
    # identified sides: left side read top to bottom, right side bottom to top
    for (xa, ya, xb, yb) in [(-0.32, 1.85, -0.32, 0.15), (6.32, 0.15, 6.32, 1.85)]:
        ax.add_patch(FancyArrowPatch((xa, ya), (xb, yb), arrowstyle="-|>", mutation_scale=7, lw=0.7, color=ORANGE))
    off = {"b": (0.0, 0.3), "p": (-0.72, 0.0), "c": (0.0, -0.3), "q": (0.0, -0.33), "a": (0.0, 0.3),
           "r": (0.0, -0.33), "p'": (0.5, 0.0), "c'": (0.0, 0.3), "b'": (0.0, -0.3)}
    for v, (x, y) in P.items():
        ax.plot([x], [y], "o", ms=3.2, color=INK, zorder=5)
        base = v.rstrip("'")
        lab = rf"${base}$" if v.endswith("'") else rf"${base}\colon {box[base]}$"
        dx, dy = off[v]
        ax.text(x + dx, y + dy, lab, ha="center", va="center", fontsize=7,
                bbox=dict(boxstyle="square,pad=0.08", fc="white", ec="none"), zorder=6)
    ax.set_xlim(-1.35, 7.0); ax.set_ylim(-0.55, 2.55); ax.set_aspect("equal"); ax.axis("off")
    rows = [(r"$\mathrm{Bar}_1(u\geq\ell)$", [(0, 2), (3, math.inf)], BLUE),
            (r"$\mathrm{Bar}_1(f_D)$", [(0, 2), (2, math.inf)], INK2),
            (r"$\mathrm{Bar}_1(u)$", [(0, 4), (3, math.inf)], INK2)]
    top = 5.4; y = 0; ticks = []
    for name, B, col in rows:
        start = y
        for (b, d) in B:
            e = top if not math.isfinite(d) else d
            bx.plot([b, e], [y, y], color=col, lw=1.6, solid_capstyle="butt")
            if not math.isfinite(d):
                bx.annotate("", xy=(top + 0.3, y), xytext=(top - 0.1, y),
                            arrowprops=dict(arrowstyle="-|>", lw=0.8, color=col, shrinkA=0, shrinkB=0, mutation_scale=6))
            y += 1
        ticks.append(((start + y - 1) / 2, name)); y += 0.9
    bx.set_yticks([t for t, _ in ticks], [nm for _, nm in ticks]); bx.invert_yaxis()
    bx.set_xlim(0, top + 0.5); bx.set_xticks(range(0, 6)); bx.set_xlabel(r"value")
    bx.tick_params(axis="y", length=0); bx.spines["left"].set_visible(False)
    fig.tight_layout(w_pad=0.8)
    fig.savefig(OUT / "fig2_certificate_D.pdf")
    plt.close(fig)


def check_certD():
    """The drawn triangles are certificate D of the notebook under 0->a, 1->b, 2->p, 3->c, 4->q, 5->r."""
    spec = [(0,1,4),(0,2,3),(0,2,5),(0,4,5),(1,2,4),(1,2,5),(1,3,5),(2,3,4),(3,4,5)]
    name = dict(enumerate("abpcqr"))
    drawn = [("b","p","q"),("p","c","q"),("a","b","q"),("a","q","r"),("c","q","r"),
             ("b","c","r"),("b","p","r"),("a","p","r"),("a","p","c")]
    assert sorted(tuple(sorted(name[i] for i in t)) for t in spec) == sorted(tuple(sorted(t)) for t in drawn)


# ---------------------------------------------------------------- Figure 3: experiments
def figure_experiments():
    mh = pd.read_csv(RES / "p2_memory_hierarchy.csv").sort_values("n")
    d1 = pd.read_csv(RES / "degree1_fast_timing.csv")
    cp = pd.read_csv(RES / "compression.csv")
    fig, (ax, bx, cx) = plt.subplots(1, 3, figsize=(TEXTW + 0.3, 2.05))
    # (a) degree-0 pipeline vs plain persistence, ns per vertex
    ax.plot(mh.n, mh.cert_ns_per_vertex, "-o", ms=3, lw=1.0, color=BLUE, label=r"bound")
    ax.plot(mh.n, mh.pers_ns_per_vertex, "--s", ms=3, lw=1.0, color=ORANGE, label=r"persistence")
    ax.set_xscale("log"); ax.set_ylim(0, max(1100, 1.08 * float(np.nanmax([mh.cert_ns_per_vertex.max(), mh.pers_ns_per_vertex.max()]))))
    ax.set_xlabel(r"vertices $n$"); ax.set_ylabel(r"ns per vertex")
    ax.legend(frameon=False, loc="upper left", handlelength=1.8)
    ax.set_title(r"(a) degree 0", loc="left")
    # (b) Corollary 14: degree-1 image barcode, total seconds
    for kind, col, st, mk, fc, lab in [("terrain", AQUA, "-", "o", AQUA, r"terrain"), ("torus", VIOLET, "--", "s", "white", r"torus")]:
        s = d1[d1.kind == kind].sort_values("n")
        bx.plot(s.n, 1e9 * s.t_total / s.n, ls=st, marker=mk, ms=3.6, mfc=fc, mew=0.9, lw=1.0, color=col, label=lab)
    bx.set_xscale("log"); bx.set_ylim(0, max(2300, 1.08 * float(np.nanmax(1e9 * d1.t_total / d1.n))))
    bx.set_xlabel(r"vertices $n$"); bx.set_ylabel(r"ns per vertex")
    bx.legend(frameon=False, loc="upper left", handlelength=1.8)
    bx.set_title(r"(b) degree 1", loc="left")
    # (c) certified fraction vs bits per value, SDRBench fields, tau = 0.5% of the range
    s = cp[(cp.kind != "synthetic") & (cp.tau_frac == 0.005)]
    g = s.groupby(["method", "rel_bound"]).agg(cf=("cert_fraction", "mean"), bpv=("bits_per_value", "mean")).reset_index()
    styles = [("SZ", BLUE, "-", "o"), ("SZ3", ORANGE, "--", "s"), ("SZ3-pwrel", AQUA, "-.", "^"), ("ZFP", YELLOW, ":", "D")]
    for m, col, st, mk in styles:
        r = g[g.method == m].sort_values("rel_bound")
        cx.plot(r.bpv, r.cf, ls=st, marker=mk, ms=3, lw=1.0, color=col, label=m.replace("-pwrel", r"-rel"))
    cx.set_xscale("log"); cx.set_ylim(0, 1.05); cx.set_xlim(0.012, 10)
    cx.set_xlabel(r"bits per value"); cx.set_ylabel(r"certified fraction")
    cx.legend(frameon=False, loc="upper left", handlelength=1.8, borderaxespad=0.1)
    cx.set_title(r"(c) compression", loc="left")
    for a in (ax, bx, cx):
        a.grid(True, which="major", color=GRID, lw=0.4); a.set_axisbelow(True)
    fig.tight_layout(w_pad=0.9)
    fig.savefig(OUT / "fig3_experiments.pdf")
    plt.close(fig)
    return g


# ---------------------------------------------------------------- Figure 4 (appendix): surface checks
FAMILY_NAMES = {
    "RP^2 (7 vertices)": "projective plane (7 v.)", "torus 3x3": r"torus $3\times3$", "torus 4x4": r"torus $4\times4$",
    "torus 3x5": r"torus $3\times5$", "Klein bottle 3x3": r"Klein bottle $3\times3$", "Klein bottle 4x4": r"Klein bottle $4\times4$",
    "Klein bottle (D+D)": "Klein bottle (glued)", "genus 2 (E+E)": "genus 2 (glued)", "N3 (D+E)": "non-orient. genus 3 (glued)",
    "Moebius band (6 v.)": r"M$\ddot{\rm o}$bius band (6 v.)", "Moebius band (grid)": r"M$\ddot{\rm o}$bius band (grid)",
    "punctured torus (7 v.)": "punctured torus (7 v.)", "punctured torus 4x4": r"punctured torus $4\times4$",
    "punctured Klein bottle": "punctured Klein bottle", "torus with two holes": "torus with two holes",
    "disk": "disk", "annulus": "annulus", "sphere": "sphere"}


def figure_appendix():
    tc = pd.read_csv(RES / "theorem_c.csv")
    raw = pd.read_csv(RES / "raw" / "v5_degree1_fast.csv")
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(TEXTW + 0.3, 3.4), gridspec_kw=dict(width_ratios=[1.3, 1]))
    tc = tc.assign(order=tc.closed.map({True: 0, False: 1})).sort_values(["bhat", "order", "family"], ascending=[True, True, True])
    ys = np.arange(len(tc))[::-1]
    cols = [INK2 if b == 0 else BLUE for b in tc.bhat]
    ax.barh(ys, tc.barcode_attained_by_fD, height=0.62, color=cols)
    ax.set_yticks(ys, [rf"{FAMILY_NAMES[f]}, $\hat b={b}$" for f, b in zip(tc.family, tc.bhat)], fontsize=7)
    ax.set_xlim(0, 1.0); ax.set_xlabel(r"share of boxes where $f_D$ attains $\mathrm{Bar}_1(u\geq\ell)$")
    ax.tick_params(axis="y", length=0)
    ax.set_title(r"(a) checks of Theorem 10", loc="left")
    # (b) Corollary 14 against the exact rank-invariant computation (exact-agreement runs)
    from matplotlib.lines import Line2D
    from matplotlib.ticker import NullFormatter, FixedLocator, FixedFormatter
    ex = raw[raw.t_exact.notna()]
    for kind, mk, fc in [("terrain", "o", None), ("torus", "s", "white")]:
        s = ex[ex.kind == kind].groupby("n")[["t_fast", "t_exact"]].median().reset_index()
        bx.plot(s.n, s.t_exact, ls="--", marker=mk, ms=3.4, lw=1.0, color=ORANGE, mfc=fc or ORANGE, mew=0.9)
        bx.plot(s.n, s.t_fast, ls="-", marker=mk, ms=3.4, lw=1.0, color=BLUE, mfc=fc or BLUE, mew=0.9)
    bx.set_xscale("log"); bx.set_yscale("log")
    ticks = [16, 25, 49, 100]
    bx.xaxis.set_major_locator(FixedLocator(ticks)); bx.xaxis.set_major_formatter(FixedFormatter([str(t) for t in ticks]))
    bx.xaxis.set_minor_formatter(NullFormatter())
    bx.set_xlabel(r"vertices $n$"); bx.set_ylabel(r"seconds (median)")
    handles = [Line2D([], [], color=ORANGE, ls="--", lw=1.0, label="exact rank invariant"),
               Line2D([], [], color=BLUE, ls="-", lw=1.0, label="Corollary 14"),
               Line2D([], [], color=INK2, ls="", marker="o", ms=3.4, label="terrain"),
               Line2D([], [], color=INK2, ls="", marker="s", ms=3.4, mfc="white", label="torus")]
    bx.legend(handles=handles, frameon=False, loc="lower right", bbox_to_anchor=(1.0, 0.16), fontsize=7, handlelength=1.8)
    bx.set_title(r"(b) degree 1, small grids", loc="left")
    for a in (ax, bx):
        a.grid(True, which="major", color=GRID, lw=0.4, axis="x" if a is ax else "both"); a.set_axisbelow(True)
    fig.tight_layout(w_pad=1.0)
    fig.savefig(OUT / "fig4_surface_checks.pdf")
    plt.close(fig)
    return ex


if __name__ == "__main__":
    info = figure_path()
    check_certD()
    figure_certD()
    g = figure_experiments()
    ex = figure_appendix()
    print("exact-agreement runs:", len(ex), "all agree:", bool(ex.agree.all()))
    for k, v in info.items():
        print(k, v)
    print(g.to_string())
