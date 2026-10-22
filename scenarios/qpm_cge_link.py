"""DSGE research, milestone 9 (19 Oct 2026, about 3:10 AM): a monetary scenario through the QPM block into Infinity GEM's CGE.

Top-down link: research/dsge/qpm.py (calibrated to the BSP's PAMPh) gives the paths of a BSP tightening of 100 bp in 2026Q1
(the rate then follows the QPM's rule). Its annual averages enter the CGE (the central 2026 setting, Infinity GEM's own SAM) in 2026-2027:
- the peso: 'exr_scale' = 1 + the real-exchange-rate gap (%) / 100;
- the interest-rate channel, which the CGE lacks: a common scale on real investment demand, solved year by year (secant) so that
  the CGE's GDP gap against the no-shock path equals the QPM's output gap.
The CGE then gives prices, industries and the new poor. A zero scenario gives no shock (checked in the run).
Run (Git Bash):  export INFINITY_GEM_SCENARIO_SAM=own; py scenarios/qpm_cge_link.py [bp=100] [mode=match|rate] [h=0.85]

19 Oct 2026, about 8:30 AM, two opt-in options (the default, mode=match h=0, reproduces the 3:13/3:19 AM runs):
- mode=rate: match only the impact year (2026) and read off the implied semi-elasticity of real investment to the QPM's real
  interest-rate gap; 2027 then gets 1 - theta x (2027 real-rate gap), with no matching. Why: matching 2027 is ill-posed, because
  the CGE carries 2026's lower investment into 2027's capital stock (a supply effect the QPM, a demand-gap model, leaves out),
  so the CGE's 2027 gap differs from the QPM's by that capital legacy, which is reported instead of forced away.
- h=: paid labour hoarding in the CGE's short run (PSA's data support about 0.85). With h = 0 the CGE's demand
  multiplier is about 0.2, so an implausibly large investment cut (8%) is needed to reproduce PAMPh's output response.
- mode=elastic [theta=0.55] (20 Oct 2026): no matching at all; real investment moves by theta % per pp of the real-rate gap in
  every year. For scenarios whose output gap is near zero, where matching fails (see the comment in main()).
- source=dsge (milestone 14, 19 Oct 2026, about 11 AM): the annual output gap, real exchange rate and real-rate gap come from
  the estimated DSGE (research/dsge/soe_htm.py at the posterior mean of milestone 13, the system prior on transmission
  strength; outputs/dsge_ph_htm_draws_*_w1_ratio.npy) instead of the QPM. Default source=qpm.
- path=hold4|pamph (milestone 19c, 20 Oct 2026, about 9:05 AM), for source=qpm and source=dsge: instead of the model's own
  response to a policy shock of +bp on impact (path=own, the default, unchanged), the policy rate is made to follow a defined
  path by a sequence of surprises (research/dsge/rate_path_review.py): hold4 = +bp for four quarters, then the baseline; pamph
  = PAMPh's path scaled to +bp on impact. Why: the models' own rules differ (the DSGE's tightening keeps rising for two
  quarters, PAMPh's reverses within three), so "100 bp" otherwise means different amounts of tightening.
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "research" / "dsge"))

import _common                                                       # noqa: E402
import combined_revised as CR                                        # noqa: E402
import qpm                                                           # noqa: E402
from infinity_gem import paths                                           # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
YEARS = (2026, 2027)


def annual_from_paths(ser):
    """Milestone 19c: annual averages of quarterly paths from rate_path_review.conditional_paths (rate and inflation in pp a
    year, output and real exchange rate in %); the real-rate gap uses next quarter's realized inflation."""
    out = {}
    for n, y in enumerate(YEARS):
        sl = slice(4 * n, 4 * n + 4)
        out[y] = {"output_gap_pct": float(np.mean(ser["y"][sl])), "real_fx_gap_pct": float(np.mean(ser["q"][sl])),
                  "policy_rate_pp": float(np.mean(ser["i"][sl])), "inflation_pp": float(np.mean(ser["pi"][sl])),
                  "real_rate_gap_pp": float(np.mean(ser["i"][sl] - ser["pi"][1:][sl]))}
    return out


def qpm_annual(bp, path="own"):
    if path != "own":                                           # milestone 19c: a defined rate path
        import rate_path_review as RP
        return annual_from_paths(RP.conditional_paths(RP.qpm_unit(), (bp / 100.0) * RP.PATHS[path]))
    p, *_ = qpm.match_pamph()
    r = qpm.irf(p, "e_i", 1.0, T=12)
    s = (bp / 100.0) / r["i"][0]
    out = {}
    for n, y in enumerate(YEARS):
        sl = slice(4 * n, 4 * n + 4)
        out[y] = {"output_gap_pct": s * float(np.mean(r["ygap"][sl])), "real_fx_gap_pct": s * float(np.mean(r["z"][sl])),
                  "policy_rate_pp": s * float(np.mean(r["i"][sl])), "inflation_pp": s * float(np.mean(r["pi"][sl])),
                  "real_rate_gap_pp": s * float(np.mean(r["rrgap"][sl]))}
    return out


def dsge_annual(bp, spec="", path="own"):
    """Annual averages from the project's DSGE (milestone 13) after a policy shock scaled to +bp on impact in 2026Q1.
    spec (20 Oct 2026, about 03:05): "" = milestone 13's chain (soe_htm, 2002-2019), as before; "htmu_long_stl" = the converged
    candidate of milestone 19 (soe_htmu with the cost-push shock, 2002-2026 with the COVID quarters missing, STL-adjusted GDP;
    the posterior mean pooled over its seed chains)."""
    from transmission_benchmarks import HTM_NAMES
    out_dir = HERE.parent / "outputs"
    if spec == "htmu_long_stl":
        import soe_htmu as M
        names = HTM_NAMES[:HTM_NAMES.index("rho_z") + 1] + ["rho_u"] + HTM_NAMES[HTM_NAMES.index("rho_z") + 1:] + ["sd_u"]
        files = sorted(out_dir.glob("dsge_ph_htmu_draws_*_w1_ratio_long_stl_seed*.npy"))
        kw = {k: v for k, v in zip(names, np.vstack([np.load(f) for f in files]).mean(0)) if not k.startswith("sd_")}
        src = f"{len(files)} chains pooled ({', '.join(f.name for f in files)})"
    elif spec:
        raise ValueError("dsge= must be empty or htmu_long_stl")
    else:
        import soe_htm as M
        f = sorted(out_dir.glob("dsge_ph_htm_draws_*_w1_ratio.npy"))[-1]
        kw = {k: v for k, v in zip(HTM_NAMES, np.load(f).mean(0)) if not k.startswith("sd_")}
        src = f.name
    if path != "own":                                           # milestone 19c: a defined rate path
        import rate_path_review as RP
        return annual_from_paths(RP.conditional_paths(RP.dsge_unit(M, kw), (bp / 100.0) * RP.PATHS[path])), src
    r = M.irf(M.Params(rule="output", **kw), "v", 0.001, T=4 * len(YEARS) + 2)
    s = (bp / 100.0) / (400 * r["i"][0])                       # i: quarterly rate (decimal); 400 i = pp a year
    pi_next = r["pi"][1:]                                       # E_t pi_{t+1} = pi_{t+1} along the response
    out = {}
    for n, y in enumerate(YEARS):
        sl = slice(4 * n, 4 * n + 4)
        out[y] = {"output_gap_pct": s * 100 * float(np.mean(r["y"][sl])), "real_fx_gap_pct": s * 100 * float(np.mean(r["q"][sl])),
                  "policy_rate_pp": s * 400 * float(np.mean(r["i"][sl])), "inflation_pp": s * 400 * float(np.mean(r["pi"][sl])),
                  "real_rate_gap_pp": s * 400 * float(np.mean(r["i"][sl] - pi_next[sl]))}
    return out, src


def dsge_oil_annual(oil_pct, spec=""):
    """Milestone 17 (19 Oct 2026, about 3:05 PM): the BSP's response to an oil-price rise of oil_pct % (log) in the project's DSGE
    (research/dsge/oil_policy.py, milestone 16 posterior mean): the estimated rule MINUS the rate held at baseline for four
    quarters, by year. The CGE then gives what the BSP's tightening alone does to industries and the poor (the oil shock itself
    is in the 2026 scenarios' CGE runs already). spec (20 Oct 2026): which chains, as oil_policy.py's spec= ("" = milestone 16's;
    "_long_stl" = 2002-2026 with STL-adjusted GDP, milestone 18b)."""
    import oil_policy as OP                                     # its model follows model= on this command line (default oil)
    kw, src = OP.posterior_mean_params(spec)
    a = OP.paths(OP.Oil.Params(rule="output", **kw), oil_pct / 100)
    b = OP.paths(OP.Oil.Params(rule="output", **kw), oil_pct / 100, hold=4)
    diff = lambda k, sl: float(np.nanmean(a[k][sl] - b[k][sl]))
    out = {}
    for n, y in enumerate(YEARS):
        sl = slice(4 * n, 4 * n + 4)
        out[y] = {"output_gap_pct": diff("output (%)", sl), "real_fx_gap_pct": diff("real exchange rate (%)", sl),
                  "policy_rate_pp": diff("policy rate (pp a year)", sl), "inflation_pp": diff("headline inflation (pp a year)", sl),
                  "real_rate_gap_pp": diff("real-rate gap (pp a year)", sl)}
    return out, src


def arg(name, default, cast=float):
    return next((cast(a.split("=", 1)[1]) for a in sys.argv[1:] if a.startswith(f"{name}=")), default)


def main():
    bp = arg("bp", 100.0)
    mode = arg("mode", "match", str)
    h = arg("h", 0.0)
    source = arg("source", "qpm", str)
    rpath = arg("path", "own", str)
    if rpath not in ("own", "hold4", "pamph") or (rpath != "own" and source == "dsge_oil"):
        raise SystemExit("path must be own, hold4 or pamph (not with source=dsge_oil)")
    if source == "dsge":
        tgt, src_file = dsge_annual(bp, arg("dsge", "", str), rpath)
    elif source == "dsge_oil":                                  # milestone 17: the BSP's response to an oil shock
        tgt, src_file = dsge_oil_annual(arg("oil", 36.0), arg("spec", "", str))
    else:
        tgt, src_file = qpm_annual(bp, rpath), None
    beta = float(pd.read_csv(_common.calibration_file(), index_col=0).loc["central (e)", "beta"])
    R = CR.Runs("low", wage_curve=beta, **({"hoarding": h} if h else {}))
    piece, _ = R.pieces()
    m = R.m
    inv = [c for i, c in enumerate(m.C) if m.qinv[i] > 0]
    clean = R.run(set(), piece=piece)
    scale = {}

    def run_with(sc):
        piece["qpm"] = {y: {"exr_scale": 1 + tgt[y]["real_fx_gap_pct"] / 100, "qinv_scale": {c: sc.get(y, 1.0) for c in inv}} for y in YEARS}
        sim = R.run({"qpm"}, piece=piece)
        return sim, R.measures(clean, sim)[0]

    theta = None
    if mode == "elastic":            # 20 Oct 2026, about 02:35: a FIXED semi-elasticity in every year, no matching. Why: with an
        # output gap near zero (the BSP's oil response on the cleaned DSGE, -0.02%) matching is dominated by the exchange-rate
        # channel and returned a wrong-signed (rising) investment. Default 0.55% of real investment per pp of real-rate gap:
        # milestone 14's implied value (the project's DSGE matched to the CGE); theta=3.0 is milestone 9's (the QPM), an upper case.
        theta = arg("theta", 0.55) / 100
    for y in YEARS:                                                 # bisection on the investment scale, year by year
        if mode in ("rate", "elastic") and theta is not None:       # later years (all years with elastic): from the real rate
            scale[y] = 1.0 - theta * tgt[y]["real_rate_gap_pp"]
            print(f"{y}: scale from the real rate gap {tgt[y]['real_rate_gap_pp']:+.3f} pp -> {scale[y]:.5f}", flush=True)
            continue

        def g(f):
            try:
                return run_with({**scale, y: f})[1][f"GDP gap {y} (%)"] - tgt[y]["output_gap_pct"]
            except RuntimeError:                                    # a scale the model cannot solve: treat as too far
                return -1e3
        lo, hi = 0.85, 1.15                                         # 2026 needs < 1; later years may need > 1 (the CGE carries 2026 forward)
        glo, ghi = g(lo), g(hi)
        print(f"{y}: bracket g({lo})={glo:.4f}, g({hi})={ghi:.4f}", flush=True)
        for _ in range(12):
            mid = 0.5 * (lo + hi)
            gm = g(mid)
            print(f"{y}: f={mid:.5f} gap error {gm:+.4f}", flush=True)
            if abs(gm) < 2e-3:
                break
            lo, hi = (mid, hi) if gm < 0 else (lo, mid)
        scale[y] = mid
        if mode == "rate":
            theta = (1.0 - mid) / tgt[y]["real_rate_gap_pp"]           # share of real investment per pp of real rate gap
    sim, M = run_with(scale)
    cpi = (sim.table.cpi / clean.table.cpi - 1) * 100
    inv_real = {y: float(sum(sim.solutions[y]["QINV"][m.C.index(c)] for c in inv) / sum(clean.solutions[y]["QINV"][m.C.index(c)] for c in inv) - 1) * 100
                for y in YEARS} if "QINV" in clean.solutions[YEARS[0]] else {}
    S = "DSGE" if source.startswith("dsge") else "QPM"
    rows = {y: {f"{S} output gap (%)": tgt[y]["output_gap_pct"], "CGE GDP gap (%)": M[f"GDP gap {y} (%)"],
                f"{S} policy rate (pp)": tgt[y]["policy_rate_pp"], f"{S} real rate gap (pp)": tgt[y]["real_rate_gap_pp"],
                f"{S} inflation (pp a year)": tgt[y]["inflation_pp"],
                f"{S} real exchange rate (%)": tgt[y]["real_fx_gap_pct"], "CGE investment scale": scale[y],
                "CGE real investment (%)": inv_real.get(y, float("nan")),
                "CGE consumer prices (%)": float(cpi[y]),
                "CGE new poor (M)": M.get(f"new poor {y} (M, own baskets)", float("nan"))} for y in YEARS}
    t = pd.DataFrame(rows)
    tag = ("" if (mode == "match" and not h) else f"_{mode}{f'{100 * theta:g}' if mode == 'elastic' else ''}_h{h:g}") + {"dsge": "_dsge" + (f"_{arg('dsge', '', str)}" if arg("dsge", "", str) else ""), "dsge_oil": f"_dsge_oil{arg('oil', 36.0):g}{arg('spec', '', str)}"}.get(source, "") + (f"_path{rpath}" if rpath != "own" else "")
    out = paths.output_dir() / f"qpm_cge_link_{dt.datetime.now():%Y%m%d_%H%M}{_common.out_tag()}_{bp:g}bp{tag}.md"
    how = ("the CGE's GDP gap is matched to the QPM's output gap in every year with a common scale on real investment demand"
           if mode == "match" else
           f"no matching: real investment demand moves by {100 * theta:.2f}% per pp of the QPM's real-rate gap in every year (a fixed "
           "semi-elasticity), so the CGE's GDP gap is a result, not a target"
           if mode == "elastic" else
           f"the CGE's 2026 GDP gap is matched to the QPM's with a common scale on real investment demand; the implied "
           f"semi-elasticity, {100 * theta:.2f}% of real investment per pp of real-rate gap, sets later years from the QPM's "
           "real-rate gap (no matching): the CGE's later gaps include the capital legacy of 2026's lower investment")
    block = {"dsge": (f"the candidate DSGE `research/dsge/soe_htmu.py` (cost-push shock; 2002-2026, COVID quarters missing, STL GDP; "
                      f"posterior mean, milestone 19; `{src_file}`)" if arg("dsge", "", str) else
                      f"the project's DSGE `research/dsge/soe_htm.py` (posterior mean, milestone 13: system prior on transmission strength; `{src_file}`)"),
             "dsge_oil": f"the project's DSGE `research/dsge/soe_{getattr(sys.modules.get('oil_policy'), '_M', 'oil')}.py` (posterior mean; "
                         f"`{src_file}`): the BSP's response to a "
                         f"{arg('oil', 36.0):g}% oil-price rise = the estimated rule minus the rate held for a year (`research/dsge/oil_policy.py`)"
             }.get(source, "QPM `research/dsge/qpm.py` (calibrated to PAMPh)")
    title = (f"Milestone 17: the BSP's response to a {arg('oil', 36.0):g}% oil-price rise, through the DSGE into the CGE" if source == "dsge_oil"
             else f"Milestone {14 if source == 'dsge' else 9}: a BSP tightening of {bp:g} bp through the {S} into the CGE"
             + {"own": "", "hold4": " (rate held for four quarters, milestone 19c)",
                "pamph": " (PAMPh's rate path, milestone 19c)"}[rpath])
    L = [f"# {title} ({dt.datetime.now():%d %B %Y, %H:%M})", "",
         f"**NOT FOR CITATION** (Infinity GEM 0.3.11; research). {block}; CGE: the 2026 scenarios of 18 Oct 2026 "
         f"central setting, SAM `{CR.SAM_VARIANT}`, wage-curve beta {beta:.3f}, labour hoarding h = {h:g}; {how.replace('QPM', S)}; "
         f"the peso moves with the {S}'s real exchange rate.", "",
         t.to_markdown(floatfmt=".3f")]
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L)); print("saved", out)


if __name__ == "__main__":
    main()
