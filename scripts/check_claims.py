"""Check every number quoted in the paper against the archived run.

Each claim pairs a statement of the paper, the value as the paper prints it, and the same
value recomputed from the files in results/. The script exits with status 1 if any claim
disagrees, and ``--write docs/claims.md`` renders the table. Standard library only.

    python scripts/check_claims.py                          # one line per claim
    python scripts/check_claims.py --quiet                  # disagreements and the summary only
    python scripts/check_claims.py --write docs/claims.md
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Run:
    """Read-only access to a results folder."""

    def __init__(self, folder: Path):
        self.dir = Path(folder)
        self.pn = self.json("paper_numbers.json")
        self.config = self.json("configs/configuration.json")
        self.report = self.json("logs/reproducibility_report.json")

    def json(self, rel: str):
        return json.loads((self.dir / rel).read_text(encoding="utf-8"))

    def rows(self, rel: str) -> list[dict]:
        with open(self.dir / rel, newline="", encoding="utf-8") as fh:
            return list(csv.DictReader(fh))

    def section(self, prefix: str) -> dict:
        keys = [k for k in self.pn if k.startswith(prefix)]
        assert len(keys) == 1, (prefix, keys)
        return self.pn[keys[0]]


# ---------------------------------------------------------------- formatting
def num(x) -> str:
    return f"{int(round(float(x))):,}"


def of(a, b) -> str:
    return f"{num(a)} of {num(b)}"


def bars(text: str) -> str:
    return text.replace("inf", "∞")


_SUP = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")


def sci(n: int) -> str:
    """50000000 -> 5·10⁷, 10000 -> 10⁴, 2560000 -> 2.56·10⁶."""
    digits = len(str(int(n))) - 1
    mant = f"{int(n) / 10 ** digits:g}"
    sup = str(digits).translate(_SUP)
    return f"10{sup}" if mant == "1" else f"{mant}·10{sup}"


def pow10(x: float) -> str:
    """0.001 -> 10⁻³."""
    return "10" + str(round(math.log10(x))).translate(_SUP)


# ---------------------------------------------------------------- the claims
def claims(r: Run) -> list[tuple[str, str, str, str, str]]:
    """(where, statement, paper value, value from the run, source)."""
    env = r.report["environment"]
    setup = r.section("Paper Section 7")
    deg0 = r.section("Degree 0")
    exact = r.section("Exact decisions")
    census = r.section("Degree 1, census text")
    certs = r.section("Certificates and transfers")
    ex20 = r.section("Example 20")
    thm8 = r.section("Theorem 8 (planar)")
    thm10 = r.section("Theorem 10")
    thm13 = r.section("Theorem 13")
    g15 = r.section("Proposition 15")
    mid = r.section("Middle degrees")
    g3d = r.section("3-D grids")
    scal = r.section("Scaling")
    comp = r.section("Compression")
    mem = r.rows("p2_memory_hierarchy.csv")
    t2 = r.rows("tables/table2_census.csv")
    t3 = r.rows("tables/table3_compression.csv")
    unif = r.rows("compression_uniform_baseline.csv")
    t13 = r.rows("theorem13.csv")
    thc = r.rows("theorem_c.csv")
    planar = r.rows("degree1_planar.csv")
    opt = r.rows("optimality.csv")
    g3d2 = r.rows("grid3d_degree2.csv")
    g3d1 = r.rows("grid3d_degree1_census.csv")
    units = r.rows("tables/unit_tests.csv")
    cfg = r.config
    PN, CFG, REP = "paper_numbers.json", "configs/configuration.json", "logs/reproducibility_report.json"
    out = []

    def add(where, statement, paper, value, source):
        out.append((where, statement, paper, value, source))

    # ------------------------------------------------------------ abstract and introduction
    add("Abstract, §7", "Timings on grids with up to", "5·10⁷ vertices",
        f"{sci(int(scal['sizes'].split(' to ')[1].replace(',', '')))} vertices", PN)
    add("§1", "Small random instances decided exactly", "6,800", num(census["method_instances"]), PN)
    last = max(mem, key=lambda x: int(x["n"]))
    add("§1", "Degree-0 bound per vertex at 5·10⁷ vertices", "about 1 µs",
        f"about {round(float(last['cert_ns_per_vertex']) / 1000)} µs", "p2_memory_hierarchy.csv")
    add("§1, §7", "Degree-1 bound on a terrain with 2.56·10⁶ vertices", "5.2 s",
        f"{scal['degree1_seconds_at_max']['terrain']} s" if scal["degree1_max_vertices"] == 2_560_000 else "?", PN)
    add("§1, §7", "Certified counts that were valid", "264 of 264", of(comp["valid"], comp["certificate_evaluations"]), PN)
    add("§1, §7", "Runs where counting the bars of the decompressed field overcounted", "107", num(comp["overcount_runs"]), PN)

    # ------------------------------------------------------------ examples (Section 6, Appendix B)
    b = certs["B"]
    add("§1, Ex. 18", "Image barcode; every function has a bar longer than 3", "[2,5) [7,10); gap at τ = 3",
        f"{bars(b['image'])}; gap at τ = {b['count_gap_taus'][0]:g}" if b["count_gap_taus"] else bars(b["image"]), PN)
    add("Ex. 17", "Image barcode, not attained", "[2,5) [7,∞)",
        bars(certs["A"]["image"]) if certs["A"]["attained"] is False else "attained", PN)
    add("Ex. 19", "Image barcode, not attained", "[2,3) [4,∞)",
        bars(certs["C"]["image"]) if certs["C"]["attained"] is False else "attained", PN)
    add("Ex. 20", "Image barcode, KC vertices, longest bar of every function", "[4,6) [8,11); none; ≥ 3.5",
        f"{ex20['image_barcode']}; {'none' if not ex20['kc_vertices'] else ex20['kc_vertices']}; ≥ {ex20['grid_min_longest']:g}", PN)
    add("Thm. 11, Fig. 2", "Möbius band: image barcode, not attained", "[0,2) [3,∞)",
        bars(certs["D"]["image"]) if certs["D"]["attained"] is False else "attained", PN)
    add("App. B", "Punctured torus: image barcode, not attained", "[1,∞) [2,4) [5,∞)",
        bars(certs["E"]["image"]) if certs["E"]["attained"] is False else "attained", PN)

    # ------------------------------------------------------------ Section 7: setup
    add("§7", "Length of the session", "72 minutes", f"{round(setup['session_minutes'])} minutes", PN)
    add("§7", "Machine", "x86-64, 4 logical CPUs, 33.7 GB",
        f"{setup['cpu'].replace('_', '-')}, {setup['logical_cpus']} logical CPUs, {setup['ram_gb']:.1f} GB", PN)
    threads = env["threads"]
    add("§7", "Threads", "one thread",
        "one thread" if threads["OMP_NUM_THREADS"] == "1" and threads["NUMBA_NUM_THREADS"] == "1" else str(threads), REP)

    # ------------------------------------------------------------ Section 7: degree 0
    add("§7 Degree 0", "Boxes where Bar₀(f_U) equals the image barcode", "100,000 of 100,000",
        of(deg0["barcode_equal"], deg0["boxes"]), PN)
    add("§7 Degree 0", "Largest instance", "225 vertices", f"{deg0['max_vertices']} vertices", PN)
    add("§7 Degree 0", "Persistence regions and quadrants matched", "3,000 and 4,000",
        f"{num(deg0['persistence_regions_equal'])} and {num(deg0['quadrants_equal'])}"
        if deg0["persistence_regions_equal"] == deg0["persistence_regions"] and deg0["quadrants_equal"] == deg0["quadrants"] else "mismatch", PN)
    add("§7 Degree 0", "Image bars = minimum number of local minima [Gray et al.]", "500 of 500",
        of(deg0["gkls_matches"], deg0["gkls_instances"]), PN)
    mism, total = deg0["gst14"].split("=")[1].split("/")
    add("§7 Degree 0", "Image bars = mandatory minima [Günther et al.]", "1,000 of 1,000",
        of(int(total) - int(mism), total), PN)

    # ------------------------------------------------------------ Section 7: degree 1 and Table 2
    add("§7 Degree 1", "Agreement with an independent enumeration", "60 of 60",
        of(exact["instances"] - exact["decision_mismatches"] - exact["order_mismatches"], exact["instances"]), PN)
    table2 = {                                     # the rows of Table 2 as printed in the paper
        "planar surfaces": "1,502 / 9 / 0 / 0",
        "non-planar surfaces": "2,469 / 9 / 48 / 0",
        "2-complexes with a KC vertex": "1,990 / 8 / 559 / 9",
        "non-manifold edge, no KC vertex": "588 / 8 / 0 / 0",
        "links cycles or paths, not a surface": "51 / 8 / 0 / 0",
        "pinched spheres (KC pinch vertex)": "200 / 24 / 105 / 0",
    }
    by_class = {row.get("class"): row for row in t2}
    for cls, printed in table2.items():
        row = by_class.get(cls)
        add("Table 2", cls, printed,
            f"{num(row['instances'])} / {row['max_vertices']} / {row['not_attained']} / {row['count_gaps']}"
            if row else "row missing", "tables/table2_census.csv")
    add("§7 Degree 1", "Instances left undecided", "0",
        str(sum(int(by_class[c]["undecided"]) for c in table2 if c in by_class)), "tables/table2_census.csv")
    add("§7 Degree 1", "Decided by a recomputed witness / by enumeration (unattainable) / by a sweep",
        "5,491 / 1,109 (607) / 200",
        f"{num(census['method_witness'])} / {num(census['method_exhaustive'])} "
        f"({census['method_exhaustive_not_attained']}) / {census['method_sweep']}", PN)
    npf = census["non_planar_failures"]
    add("§7 Degree 1", "Non-planar failures: projective plane, Möbius band, punctured torus, punctured Klein bottle",
        "3 of 400, 7, 22, 16",
        f"{npf['projective plane']}, {npf['Moebius band'].split()[0]}, {npf['punctured torus'].split()[0]}, "
        f"{npf['punctured Klein bottle'].split()[0]}", PN)
    add("§7 Degree 1", "Unpinched controls attained", "199 of 199", census["unpinched_controls_attained"], PN)
    shown = [certs[k]["attained"] for k in "ABCDEF"] + [v["attained"] for v in certs["transfers"].values()]
    add("§7 Degree 1", "Fig. 2, punctured torus, Exs. 17–20 and five closed surfaces unattainable", "all 11",
        f"all {len(shown)}" if not any(shown) and len(certs["transfers"]) == 5 else "no", PN)
    add("§7 Degree 1", "Count gaps confirmed", "Examples 18 and 20",
        "Examples 18 and 20" if certs["B"]["count_gap_taus"] and certs["F"]["count_gap_taus"] else "no", PN)

    # ------------------------------------------------------------ Theorems 8, 10, 13, Prop. 15, Lemma 16
    add("§7 Thm. 8", "Boxes, planar families, largest complex, failures", "1,500 / 5 / 26 / 0",
        f"{num(thm8['boxes'])} / {thm8['families']} / {thm8['max_vertices']} / {thm8['failures']}", PN)
    own = thm8["fD_on_complex_itself"]
    add("§7 Thm. 8", "f_D on the complex itself: annulus, full subcomplex, sphere with three holes", "93%, 83%, 82%",
        f"{own['annulus']:.0f}%, {own['full subcomplex of a sphere']:.0f}%, {own['sphere with 3 holes']:.0f}%", PN)
    d2 = g3d["degree2"]
    add("§7 Thm. 8", "3-D grids: boxes, with voids, failures; largest grid", "500 / 216 / 0; 5×5×5",
        f"{d2['boxes']} / {d2['boxes_with_image_bars']} / {d2['theorem_failures']}; "
        f"{'×'.join(map(str, max(cfg['g3_dual_shapes'], key=lambda s: s[0] * s[1] * s[2])))}", f"{PN}, {CFG}")
    add("§7 Thm. 10", "Boxes, families, largest surface, max b̂", "7,199 / 18 / 16 / 4",
        f"{num(thm10['boxes'])} / {thm10['families']} / {thm10['max_vertices']} / {thm10['max_bhat']}", PN)
    add("§7 Thm. 10", "Finite bars always agreed", "0 failures", f"{thm10['failures']} failures", PN)
    ok_bhat = all(int(x["max_mismatch"]) <= int(x["bhat"]) for x in thc)
    ok_planar = all(int(x["max_mismatch"]) == 0 for x in thc if int(x["bhat"]) == 0)
    add("§7 Thm. 10", "Essential births differed (all non-planar, never more than b̂ bars)", "333",
        num(thm10["essential_births_differ"]) if ok_bhat and ok_planar else "violated", f"{PN}, theorem_c.csv")
    add("§7 Thm. 10", "Corollary 14 returned the exact image barcode", "every time",
        "every time" if thm10["fast_mismatches"] == 0 else f"{thm10['fast_mismatches']} mismatches", PN)
    bfd = thm13["boundary_fD_attains"]
    add("§7 Thm. 13", "With boundary: f_D attains; proved unattainable", "393 of 400, 193 of 200; 14",
        f"{bfd['mobius (seed 11)']}, {bfd['ptorus (seed 21)']}; {thm13['boundary_proved_unattainable']}", PN)
    add("§7 Thm. 13", "Closed: f_D attains; some f_p the rest", "411 of 500; 89",
        f"{thm13['closed_fD_attains']} of {thm13['closed_boxes']}; {thm13['closed_attained_by_fp']}", PN)
    add("§7 Thm. 13", "Lemma 12 checks: boxes, functions", "420; 10,276",
        f"{thm13['boundary_max_boxes'] + thm13['closed_max_boxes']}; "
        f"{num(thm13['boundary_near_sup_representatives'] + thm13['closed_near_sup_representatives'])}", PN)
    add("§7 Thm. 13", "Repetition: boxes, exceptions", "15,200; none",
        f"{num(thm13['extended_boxes'])}; {'none' if thm13['extended_inconsistent'] == 0 else thm13['extended_inconsistent']}", PN)
    add("§7 Prop. 15", "Graphs", "600", num(g15["graphs"]) if g15["graph_failures"] == 0 else "failures", PN)
    add("§7 Lemma 16", "Functions, complexes, KC entrances that did both", "6,000 / 1,500 / 283",
        f"{num(g15['kc_functions'])} / {num(g15['kc_complexes'])} / {g15['kc_entrances_doing_both']}"
        if g15["kc_violations"] == 0 else "violations", PN)

    # ------------------------------------------------------------ Theorem 21
    rows = {x["case"]: x for x in mid["rows"]}
    m3, mb = rows["Moebius band (Thm 11) in S^3"], rows["Moebius band (Thm 11) in B^3"]
    e3 = rows["Example 18 in S^3 (counts)"]
    add("§7 Thm. 21", "Möbius band in a 3-sphere and a 3-ball: vertices, attained", "24 and 23; no",
        f"{m3['vertices']} and {mb['vertices']}; {'no' if not m3['attained'] and not mb['attained'] else 'yes'}", PN)
    add("§7 Thm. 21", "Example 18 in a 3-sphere: vertices, count gap", "31; yes",
        f"{e3['vertices']}; {'yes' if e3['count_gap_taus'] else 'no'}", PN)
    s4 = [x for x in mid["rows"] if x["d"] == 4]
    s4_ok = len(s4) == 4 and all((x.get("attained") is False) or x.get("count_gap_taus") for x in s4)
    add("§7 Thm. 21", "Both suspended into S⁴, (d, k) = (4, 2) and (4, 1)", "same failures",
        "same failures" if s4_ok else "differ", PN)
    d1 = g3d["degree1"]
    add("§7 Thm. 21", "3-D grids, degree 1: boxes, largest grid, unattained", "2,000 / 36 vertices / 0",
        f"{num(d1['boxes'])} / {max(int(x['n']) for x in g3d1)} vertices / {d1['not_attained']}", f"{PN}, grid3d_degree1_census.csv")

    # ------------------------------------------------------------ scaling
    first = min(mem, key=lambda x: int(x["n"]))
    ops = [float(x["uf_ops_per_vertex"]) for x in mem]
    add("§7 Scaling", "Grid sizes", f"10⁴ to 5·10⁷", f"{sci(int(first['n']))} to {sci(int(last['n']))}", "p2_memory_hierarchy.csv")
    add("§7 Scaling", "Union-find operations: log-log slope; per vertex", "1.007; 3.64 to 3.86",
        f"{scal['ops_loglog_slope']:.3f}; {min(ops):.2f} to {max(ops):.2f}", f"{PN}, p2_memory_hierarchy.csv")
    add("§7 Scaling", "Time per vertex of the bound", "202 to 974 ns",
        f"{float(first['cert_ns_per_vertex']):.0f} to {float(last['cert_ns_per_vertex']):.0f} ns", "p2_memory_hierarchy.csv")
    add("§7 Scaling", "Plain degree-0 persistence", "153 to 650 ns",
        f"{float(first['pers_ns_per_vertex']):.0f} to {float(last['pers_ns_per_vertex']):.0f} ns", "p2_memory_hierarchy.csv")
    add("§7 Scaling", "Random memory access", "1.3 to 11.3 ns",
        f"{float(first['gather_random_ns']):.1f} to {float(last['gather_random_ns']):.1f} ns", "p2_memory_hierarchy.csv")
    add("§7 Scaling", "Corollary 14 on terrains and tori: largest grid, time", "2.56·10⁶ vertices, 5.2 s",
        f"{sci(scal['degree1_max_vertices'])} vertices, {max(scal['degree1_seconds_at_max'].values())} s", PN)
    add("§7 Scaling", "Agreement with the rank-invariant computation", "42 of 42 grids",
        f"{of(scal['degree1_exact_agree'], scal['degree1_exact_grids'])} grids", PN)

    # ------------------------------------------------------------ compression
    sdr = cfg["compression"]["sdrbench"]
    shapes = {x["name"]: (x["n_fields"], "×".join(map(str, x["shape"]))) for x in sdr}
    add("§7 Compression", "SDRBench fields", "4 × 1800×3600 CESM-ATM, 1 × 100×500×500 Hurricane-ISABEL",
        f"{shapes['CESM-ATM'][0]} × {shapes['CESM-ATM'][1]} CESM-ATM, {shapes['Hurricane-ISABEL-Pf'][0]} × "
        f"{shapes['Hurricane-ISABEL-Pf'][1]} Hurricane-ISABEL", CFG)
    add("§7 Compression", "Synthetic Gaussian fields", "6", str(cfg["comp_synth_2d"] + cfg["comp_synth_3d"]), CFG)
    add("§7 Compression", "Error bounds (times the value range)", "10⁻⁴, 10⁻³, 10⁻²",
        ", ".join(pow10(b) for b in sorted(cfg["comp_rel_bounds"])), CFG)
    runs = comp["fields"] * len(cfg["compression"]["methods"]) * len(cfg["comp_rel_bounds"]) * len(cfg["compression"]["tau_fracs"])
    add("§7 Compression", "Runs: 11 fields × 4 modes × 3 bounds × 2 values of τ", "264",
        num(runs) if runs == comp["certificate_evaluations"] else "inconsistent", f"{PN}, {CFG}")
    add("§7 Compression", "Runs that respected their bounds", "264 of 264", of(comp["bound_respected"], comp["certificate_evaluations"]), PN)
    add("§7 Compression", "Overcounts (on SDRBench) and undercounts", "107 (72 of 120) and 36",
        f"{comp['overcount_runs']} ({comp['overcount_runs_sdrbench']} of {comp['sdrbench_evaluations']}) and {comp['undercount_runs']}", PN)
    f3c = comp["figure_3c"]
    add("§7 Compression", "True bars on average (SDRBench, τ = 0.5%)", "2,056", num(f3c["sdr_mean_true_bars"]), PN)
    cf = f3c["certified_fraction"]
    absolute = [100 * cf[f"{m}@0.001"] for m in ("SZ", "SZ3", "ZFP")]
    add("§7 Compression", "Certified at 10⁻³: absolute modes; relative mode", "73–75%; 92%",
        f"{min(absolute):.0f}–{max(absolute):.0f}%; {100 * cf['SZ3-pwrel@0.001']:.0f}%", PN)
    ex = {m: f3c["naive_excess"][f"{m}@0.01"] for m in ("SZ", "SZ3", "SZ3-pwrel", "ZFP")}
    lo_m, hi_m = min(ex, key=ex.get), max(ex, key=ex.get)
    add("§7 Compression", "Mean excess of the decompressed field's count at 10⁻²", "53 (ZFP) to 6,346 (SZ)",
        f"{num(ex[lo_m])} ({lo_m}) to {num(ex[hi_m])} ({hi_m})", PN)
    ub = comp["uniform_baseline"]
    add("§7 Compression", "Absolute runs where the certificate is the ε-smoothing count", "198 of 198",
        of(ub["absolute_identity_holds"], ub["absolute_runs"]), PN)
    u = {(float(x["rel_bound"]), float(x["tau_frac"])): x for x in unif if x["kind"] == "sdrbench"}
    a, c = u[(0.01, 0.005)], u[(0.001, 0.005)]
    add("§7 Compression", "Relative mode vs smallest uniform box, τ = 0.5% (10⁻²; 10⁻³)", "1,199 vs 406; 1,885 vs 1,546",
        f"{num(a['T'])} vs {num(a['T_uniform'])}; {num(c['T'])} vs {num(c['T_uniform'])}", "compression_uniform_baseline.csv")
    secs = comp["median_certify_seconds"]
    cesm = [v["median_certify_seconds"] for k, v in secs.items() if k.startswith("CESM")]
    isabel = [v for k, v in secs.items() if k.startswith("Hurricane")][0]
    n_cesm = {v["n"] for k, v in secs.items() if k.startswith("CESM")}
    add("§7 Compression", "Median certification time", "2.1–2.7 s at 6.48·10⁶ vertices; 10.8 s at 2.5·10⁷",
        f"{min(cesm):.1f}–{max(cesm):.1f} s at {sci(n_cesm.pop())} vertices; {isabel['median_certify_seconds']:.1f} s at {sci(isabel['n'])}", PN)

    # ------------------------------------------------------------ discussion
    small = max(int(x["max_vertices"]) for x in t2 if not x["class"].startswith("pinched"))
    pinched = max(int(x["max_vertices"]) for x in t2 if x["class"].startswith("pinched"))
    add("§8", "Largest complex in the random exact decisions (pinched spheres; 3-D grids)", "9 (24; 36)",
        f"{small} ({pinched}; {max(int(x['n']) for x in g3d1)})", "tables/table2_census.csv, grid3d_degree1_census.csv")

    # ------------------------------------------------------------ appendix D
    add("App. D", "Python, NumPy, SciPy, pandas, Numba, Matplotlib, hdf5plugin",
        "3.13, 2.1.3, 1.16.3, 2.3.3, 0.61.2, 3.10.0, 7.1.0",
        f"{'.'.join(env['python'].split('.')[:2])}, {env['numpy']}, {env['scipy']}, {env['pandas']}, {env['numba']}, "
        f"{env['matplotlib']}, {env['hdf5plugin']}", REP)
    add("App. D", "Configuration hash, base seed, minutes", "8f4b785c7a4a, 20260925, 71.7",
        f"{r.report['config_hash']}, {r.report['master_seed']}, {setup['session_minutes']}", f"{REP}, {PN}")
    add("App. D", "Unit tests passed", "33 of 33", of(sum(x["result"] == "PASS" for x in units), len(units)), "tables/unit_tests.csv")
    kinds = {}
    for x in opt:
        kinds[x["kind"]] = kinds.get(x["kind"], 0) + 1
    add("App. D", "Degree-0 boxes on paths, grids, integer graphs, real-valued graphs", "25,000 each",
        "25,000 each" if sorted(kinds) == ["graph", "graph_float", "grid", "path"] and set(kinds.values()) == {25000} else str(kinds),
        "optimality.csv")
    fam = {}
    for x in planar:
        fam[x["family"]] = fam.get(x["family"], 0) + 1
    add("App. D", "Theorem 8: boxes on each of five families", "300 each",
        "300 each" if len(fam) == 5 and set(fam.values()) == {300} else str(fam), "degree1_planar.csv")
    counts = sorted({int(x["instances"]) for x in thc})
    annulus = [int(x["instances"]) for x in thc if x["family"] == "annulus"][0]
    add("App. D, Fig. 4", "Theorem 10: boxes per family (annulus)", "400 (399)",
        f"{max(counts)} ({annulus})" if len(thc) == 18 and counts == [399, 400] else str(counts), "theorem_c.csv")
    add("App. D", "3-D grids: degree-2 boxes per grid; degree-1 boxes per combination", "100 × 5; 200 × 10",
        f"{g3d2[0]['boxes']} × {len(g3d2)}; {g3d1[0]['boxes']} × {len(g3d1)}"
        if len({x['boxes'] for x in g3d2}) == 1 and len({x['boxes'] for x in g3d1}) == 1 else "uneven", "grid3d_degree2.csv, grid3d_degree1_census.csv")
    ref = [x for x in t13 if x["run"] == "reference"]
    design = "; ".join(f"{x['check']} {x['surface']} {x['boxes']} ({x['seed']})" for x in ref)
    add("App. D", "Theorem 13 reference runs: check, surface, boxes (seed)",
        "decide mobius 400 (11); decide rp2 300 (12); decide ptorus 200 (21); decide torus 200 (22); max mobius 150 (32); "
        "max ptorus 60 (31); max_closed rp2 150 (41); max_closed torus 60 (42)", design, "theorem13.csv")
    mx = {x["surface"]: x for x in ref if x["check"] == "max"}
    add("App. D", "Maximality with boundary: functions (Möbius, punctured torus); attained boxes", "4,030 (2,745, 1,285); 148 and 59",
        f"{num(float(mx['mobius']['attaining_max_realisations']) + float(mx['ptorus']['attaining_max_realisations']))} "
        f"({num(mx['mobius']['attaining_max_realisations'])}, {num(mx['ptorus']['attaining_max_realisations'])}); "
        f"{num(mx['mobius']['attained_instances'])} and {num(mx['ptorus']['attained_instances'])}", "theorem13.csv")
    mc = {x["surface"]: x for x in ref if x["check"] == "max_closed"}
    add("App. D", "Closed maximality: attained boxes; functions; above max ℓ", "210; 3,930 and 2,316; 3,207 and 1,923",
        f"{num(float(mc['rp2']['attained_instances']) + float(mc['torus']['attained_instances']))}; "
        f"{num(mc['rp2']['attaining_max_realisations'])} and {num(mc['torus']['attaining_max_realisations'])}; "
        f"{num(mc['rp2']['max_above_Lstar'])} and {num(mc['torus']['max_above_Lstar'])}", "theorem13.csv")
    ext = [x for x in t13 if x["run"] == "extended"]
    add("App. D", "Extended runs: seeds; boxes; functions",
        "111, 112, 121, 122, 132, 131, 141, 142; 15,200; 101,558",
        f"{', '.join(x['seed'] for x in ext)}; {num(sum(int(x['boxes']) for x in ext))}; "
        f"{num(sum(float(x['attaining_max_realisations'] or 0) for x in ext))}"
        + ("" if all(x["consistent_with_theorem"] == "True" for x in ext) else " (inconsistent)"), "theorem13.csv")
    add("App. D", "Last-level cache; bytes per vertex of the bound", "40,370,176; 122",
        f"{num(scal['llc_bytes'])}; {scal['array_bytes_per_vertex']:.0f}", PN)
    add("App. D", "Fill values in ODV_sulf", "9.9%",
        f"{100 * comp['fill_fractions']['CESM-ATM:ODV_sulf_1_1800_3600.f32']:.1f}%", PN)
    paper_t3 = {
        ("0.0001", "SZ"): "0.969 / 3.6 / 2.33", ("0.0001", "SZ3"): "0.970 / 2.4 / 2.00",
        ("0.0001", "SZ3-pwrel"): "0.991 / 0.0 / 6.47", ("0.0001", "ZFP"): "0.970 / 0.2 / 6.62",
        ("0.001", "SZ"): "0.749 / 55.0 / 0.86", ("0.001", "SZ3"): "0.751 / 62.8 / 0.55",
        ("0.001", "SZ3-pwrel"): "0.924 / 11.0 / 4.18", ("0.001", "ZFP"): "0.732 / 3.4 / 3.96",
        ("0.01", "SZ"): "0.215 / 6345.8 / 0.22", ("0.01", "SZ3"): "0.203 / 2107.4 / 0.08",
        ("0.01", "SZ3-pwrel"): "0.595 / 915.4 / 2.60", ("0.01", "ZFP"): "0.177 / 53.4 / 2.31",
    }
    for x in t3:
        key = (f"{float(x['rel_bound']):g}", x["method"])
        label = {"SZ3-pwrel": "SZ3, relative"}.get(x["method"], x["method"])
        add("Table 3", f"{label}, bound {pow10(float(x['rel_bound']))}", paper_t3[key],
            f"{float(x['cf']):.3f} / {float(x['over']):.1f} / {float(x['bpv']):.2f}", "tables/table3_compression.csv")
    return out


def render_markdown(rows) -> str:
    lines = [
        "# Every number in the paper, checked",
        "",
        "Generated by `python scripts/check_claims.py --write docs/claims.md` from the archived run in `results/`.",
        "Each row pairs a value as the paper prints it with the same value recomputed from the result files.",
        "",
        "| | Paper | Statement | In the paper | From the run | Source |",
        "|---|---|---|---|---|---|",
    ]
    for where, statement, paper, value, source in rows:
        mark = "✓" if paper == value else "✗"
        lines.append(f"| {mark} | {where} | {statement} | {paper} | {value} | `{source}` |")
    ok = sum(p == v for _, _, p, v, _ in rows)
    lines += ["", f"{ok} of {len(rows)} claims agree."]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Check the numbers of the paper against results/.")
    ap.add_argument("--results", type=Path, default=ROOT / "results")
    ap.add_argument("--write", type=Path, help="write the table as Markdown to this file")
    ap.add_argument("-q", "--quiet", action="store_true", help="print only disagreements and the summary")
    args = ap.parse_args(argv)
    rows = claims(Run(args.results))
    bad = [row for row in rows if row[2] != row[3]]
    width = max(len(r[1]) for r in rows)
    for where, statement, paper, value, _ in rows:
        if args.quiet and paper == value:
            continue
        flag = "ok " if paper == value else "BAD"
        print(f"{flag}  {where:<15} {statement[:width]:<{min(width, 70)}}  {value}" + ("" if paper == value else f"   (paper: {paper})"))
    if not args.quiet:
        print()
    if bad:
        print(f"FAILED: {len(bad)} of {len(rows)} numbers quoted in the paper differ from the archived run")
    else:
        print(f"OK: all {len(rows)} numbers quoted in the paper agree with the archived run")
    if args.write:
        args.write.write_text(render_markdown(rows), encoding="utf-8")
        print(f"wrote {args.write}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
