"""The forward-looking CGE (Stage 2), step 4(c) (17 Oct 2026, night): first use of the forward-looking CGE: an ANNOUNCED public-works
programme against the same programme as a SURPRISE. NOT FOR CITATION (research code).

The programme: measure C of the 2026 scenarios (17 Oct 2026): DPWH's lapsing 2025 money, ₱208.7 bn, built in 2027.
In the model's 2023-SAM units: 208.7 / 33,180 (2027 nominal GDP implied by the DBCC, scenarios/_common.py) x 26,161
(SAM GDP) = ₱164.6 bn of extra public investment in year 2 (2027), year 1 being 2026.
  ANNOUNCED: known from 2026 (households and firms plan for it from year 1).
  SURPRISE:  learned only in 2027 (2026 stays on the base path).
Model: pf_cge9.CGE9(calib="pwt", households="groups", public_capital=...) with Infinity GEM's two public-capital pairs
(infinity_gem/settings.py): low = (phi 0.083, KG/GDP 0.397), high = (0.122, 0.296) (Bom and Ligthart 2014; IMF
ICSD); efficiency e = 0.77 and depreciation 3.52% as Infinity GEM's dynamic.py. Financing: lump sum (Ricardian).
Closure: full employment every year (the forward-looking model has no Keynesian short run yet), so this measures the
supply side of the programme and crowding out; the "₱0.8 per peso" of the 2026 scenarios comes from Infinity GEM's recursive model with
a Keynesian short run and is NOT comparable one-for-one.
Checks first: (i) public capital on, no programme: the path stays on the steady state; (ii) a permanent rise in public
investment converges to its separately solved steady state; (iii) GDP identity.
Run:  py research/intertemporal/step4_announced_infrastructure.py
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import pf_cge9 as P  # noqa: E402

GDP_2027 = 33180.0           # scenarios/_common.py PSA_GDP[2027] (DBCC 193rd statement)
C_BN = 208.7                 # the 2026 scenarios of 17 Oct 2026, measure C
sys.path.insert(0, str(ROOT))
from infinity_gem.settings import PUBLIC_CAPITAL  # noqa: E402  (the sourced pairs)
PAIRS = {k: PUBLIC_CAPITAL[k] for k in ("low", "high")}
T = 200
YEARS = list(range(2026, 2026 + 15))


def run_case(m, ss, dig, announced):
    if announced:
        X = m.path(T, dIG=lambda r: r.__setitem__((0, 1), dig))
        Y, y0, yT, info = m.run(X, y_start=ss)
        acc = m.accounts(Y, y0, X)
        return Y, acc, X
    X = m.path(T, dIG=lambda r: r.__setitem__((0, 0), dig))       # starts in 2027
    Y, y0, yT, info = m.run(X, y_start=ss)
    acc = m.accounts(Y, y0, X)
    # prepend 2026 on the steady state
    Y = np.column_stack([ss, Y[:, :-1]])
    for k in ("real_gdp", "real_income"):
        acc[k] = np.concatenate([[float(m.accounts(np.repeat(ss[:, None], 2, 1), ss, np.repeat(m.x0[:, None], 3, 1))[k][0])],
                                 acc[k][:-1]])
    return Y, acc, X


def welfare_ce(m, C_path, C_base):
    """Consumption-equivalent welfare change (%): the permanent % change in base consumption that gives the same lifetime
    utility as the path C_path (detrended), with CRRA sigma and the growth-adjusted discount factor beta (1+g)^(1-sigma)."""
    s = m.sigma
    bt = m.beta * (1 + m.g) ** (1 - s)
    w = bt ** np.arange(len(C_path))
    V = (w * C_path ** (1 - s)).sum()
    V0 = (w * np.full(len(C_path), C_base) ** (1 - s)).sum()
    return ((V / V0) ** (1 / (1 - s)) - 1) * 100


def myopic_case(m, ss, dig, years=15, horizon=120):
    """Foresight OFF (step 4b): static expectations. Each year agents take this year's exogenous values as permanent,
    solve the forward-looking problem from the current state, act on its first year, and re-plan next year."""
    state, Ys, accs = ss.copy(), [], []
    for t in range(years):
        x_now = m.x0.copy()
        if t == 1:
            x_now[31] = dig                       # the programme happens in 2027 (t = 1); expected to last forever
        X = np.repeat(x_now[:, None], horizon + 1, axis=1)
        Y, y0, yT, info = m.run(X, y_start=state)
        Ys.append(Y[:, 0])
        accs.append(m.accounts(Y[:, :2], state, X[:, :3])["real_gdp"][0])
        state = Y[:, 0]
    return np.column_stack(Ys), np.array(accs)


def main():
    out = [f"# Step 4(c): an announced public-works programme in the forward-looking CGE ({datetime.now():%Y-%m-%d %H:%M})", "",
           "**NOT FOR CITATION** (research code; full employment; see the script's docstring).", ""]
    checks = {}
    for name, pc in PAIRS.items():
        m = P.CGE9(calib="pwt", households="groups", public_capital=pc)
        ss = m.steady()[0]
        base_gdp = float(m.accounts(np.repeat(ss[:, None], 2, 1), ss, np.repeat(m.x0[:, None], 3, 1))["real_gdp"][0])
        dig = C_BN / GDP_2027 * m.GDP0
        # checks
        Y0, *_ = m.run(m.path(T), y_start=ss)
        checks[f"{name}: no programme stays on the steady state"] = float(np.abs(Y0 - ss[:, None]).max() / np.abs(ss).max()) < 1e-10
        Xp = m.path(300, dIG=lambda r: r.__setitem__(0, dig))
        Yp, y0p, _, _ = m.run(Xp, y_start=ss)
        sp = m.steady(Xp[:, -1])[0]
        gap = float((np.abs(Yp[:, 249] - sp) / m.scale(sp)).max())
        checks[f"{name}: permanent programme converges to its steady state (gap {gap:.1e} after 250 years)"] = gap < 5e-3
        lr = float(m.accounts(np.repeat(sp[:, None], 2, 1), sp, np.repeat(Xp[:, -1:], 3, 1))["real_gdp"][0]) / base_gdp - 1
        rows = {}
        for lab, ann in (("announced in 2026", True), ("surprise in 2027", False)):
            Y, acc, X = run_case(m, ss, dig, ann)
            checks[f"{name}, {lab}: GDP identity (gap {acc['gap']:.1e})"] = acc["gap"] < 1e-8
            v = m.split(Y)
            gdp = acc["real_gdp"] / base_gdp - 1
            C = v["C"] / m.C0 - 1
            Ipriv = v["I"].sum(0) / ss[m.sl["I"]].sum() - 1
            b = v["b"]
            cum = float((acc["real_gdp"][:10] - base_gdp).sum())
            rows[lab] = (gdp, C, Ipriv, b, cum)
        out += [f"## Public capital '{name}' (phi {pc['phi']}, KG/GDP {pc['kg_gdp']}); programme ₱{dig:,.1f} bn (2023-SAM units) in 2027",
                "", f"Long run of a PERMANENT programme of this size: real GDP {lr * 100:+.3f}%.", "",
                "| Year | GDP announced (%) | GDP surprise (%) | Consumption ann. (%) | Consumption surp. (%) | Private investment ann. (%) | Private investment surp. (%) |",
                "|---|---|---|---|---|---|---|"]
        a, s = rows["announced in 2026"], rows["surprise in 2027"]
        for i, yr in enumerate(YEARS[:8]):
            out.append(f"| {yr} | {a[0][i] * 100:+.3f} | {s[0][i] * 100:+.3f} | {a[1][i] * 100:+.3f} | {s[1][i] * 100:+.3f} | "
                       f"{a[2][i] * 100:+.3f} | {s[2][i] * 100:+.3f} |")
        out += ["", f"Cumulative real GDP gain 2026-2035 (2023-SAM ₱ bn): announced {a[4]:,.1f} (₱{a[4] / dig:.2f} per peso), "
                f"surprise {s[4]:,.1f} (₱{s[4] / dig:.2f} per peso). The spending itself is part of GDP in 2027.", ""]
        Ym, gm = myopic_case(m, ss, dig)
        vm = m.split(Ym)
        Im = vm["I"].sum(0) / ss[m.sl["I"]].sum() - 1
        cum_m = float((gm[:10] - base_gdp).sum())
        out += ["**Foresight off (static expectations, re-planned each year; step 4b):** private investment "
                + ", ".join(f"{yr} {Im[i] * 100:+.3f}%" for i, yr in enumerate(YEARS[:4]))
                + f"; consumption 2027 {(vm['C'][1] / m.C0 - 1) * 100:+.3f}%; cumulative GDP gain 2026-2035 ₱{cum_m:,.1f} bn "
                f"(₱{cum_m / dig:.2f} per peso). In 2027 the myopic agents take the programme as permanent, so they save and "
                f"invest as for a lasting rise in public capital; in 2028 they learn it has ended.", ""]
        checks[f"{name}: foresight off shows nothing in 2026"] = abs(Im[0]) < 1e-12 and abs(gm[0] / base_gdp - 1) < 1e-12
        # welfare: full consumption paths over the horizon (myopic: 15 re-planned years, then one solve from that state)
        Ya, _, _ = run_case(m, ss, dig, True)
        Ys, _, _ = run_case(m, ss, dig, False)
        Yrest, *_ = m.run(m.path(T), y_start=Ym[:, -1])
        Cm_full = np.concatenate([vm["C"], m.split(Yrest)["C"]])[:T]
        ca = welfare_ce(m, m.split(Ya)["C"][:T], m.C0)
        cs = welfare_ce(m, m.split(Ys)["C"][:T], m.C0)
        cm = welfare_ce(m, Cm_full, m.C0)
        out += [f"**Welfare (consumption-equivalent, % of base consumption, permanent):** announced {ca:+.4f}%, surprise "
                f"{cs:+.4f}%, foresight off {cm:+.4f}%. (Financing is lump sum; consumption is net of it.) The sign is the "
                f"result: under this public-capital return the programme {'raises' if ca > 0 else 'lowers'} welfare at full "
                f"employment. The three cases differ by about {max(ca, cs, cm) - min(ca, cs, cm):.4f} point: the market economy has "
                f"distortions (sales taxes, tariffs, the debt premium agents do not internalise), so better information need not "
                f"rank first, and a little myopic over-investment can help marginally.", ""]
    out += ["## Checks", ""] + [f"- {k}: {'PASS' if v else 'FAIL'}" for k, v in checks.items()]
    out += ["", f"{sum(checks.values())} of {len(checks)} checks pass", "",
            "## Reading", "",
            "- **Anticipation:** with the programme announced, households and firms adjust in 2026 already (the rows for 2026); "
            "a recursive model shows nothing before 2027.",
            "- **Full employment:** the public works take resources from private uses in 2027 (crowding out); the gain comes "
            "afterwards from the public capital's productivity. A Keynesian short run (idle workers, as in Infinity GEM's "
            "short-run closure) is needed before these numbers can be set beside the 2026 scenarios'."]
    txt = "\n".join(out) + "\n"
    p = ROOT / "outputs" / f"dscge_step4c_announced_infrastructure_{datetime.now():%Y%m%d_%H%M}.md"
    p.write_text(txt, encoding="utf-8")
    print(txt); print(f"wrote {p}")
    return checks


if __name__ == "__main__":
    main()
