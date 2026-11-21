"""Check ACC1 (Infinity GEM 0.4.2, 14 Nov 2026): the opt-in short-run private-investment accelerator
(infinity_gem/dynamic.py: DynamicCGE(sr_accelerator={"a", "lag", "driver", "public", "tol", "max_iter"});
estimates: preshock/accelerator_estimate.py). The small case: Infinity GEM's own SAM v1.0 rice-split, "0.3 recommended", short-run years 2026
and 2027, construction investment -10% in 2026 and -5% in 2027; with and without MP1's BSP rule (theta 2).
  T1  off = the engine before the option, to the bit: checks/reference_dynamic_pre_acc_042.py (dynamic.py as it was before the
      accelerator, SHA-256 checked) and today's engine, the option absent, give EXACTLY the same numbers (real GDP, CPI, peso,
      investment and consumption by year; the shock years' QINV, QH, EMP; the rule's rate path), without and with the BSP rule;
  T2  a = 0 is off, to the bit (without and with the rule);
  T3  a zero shock (qinv_scale 1.0 in both years) with the accelerator on (a 3, lag 0.25, GDP driver) reproduces the baseline (1e-9);
  T4  the fixed point, recomputed by hand from the solutions: the driver's gaps (final demand other than investment: QH + QHA + QG
      + QE against the baseline's) give z = a [(1 - lag) ln r_t + lag ln r_t-1] equal to the z the path was run with (within the
      accelerator's tol), and every investment commodity's QINV / baseline QINV = x_c m_t + (1 - s_c)(exp(z_t) - 1) m_t (1e-9; x_c the
      scenario's own factor, m_t the rule's investment scale, s_c the public share: construction at PSA's 2023 share); Walras and the
      GDP identity (expenditure = income) in the shock years (1e-8); converged; the slump deepens; without and with the rule;
  T5  homogeneity: the 2026 baseline solution replaced by the same equilibrium at twice the numeraire (CPI 2): the accelerator's path
      has the same quantities in every year and twice the 2026 prices (1e-9);
  T6  tampers that must be caught: the public share ignored in the factor (T4's investment test), and the lag weight dropped (T4's z
      test);
  T7  guards: bad settings refused at construction and before a path (set afterwards).
Run: py -I -X utf8 checks/test_accelerator.py   (a few minutes; the suite runs it as check ACC1)
"""
import copy
import hashlib
import importlib.util
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import numpy as np                                               # noqa: E402

from infinity_gem import dynamic as DY                               # noqa: E402
from infinity_gem.dynamic import DynamicCGE                          # noqa: E402

PRE = HERE / "reference_dynamic_pre_acc_042.py"
# public version: the SHA-256 of this repository's copy (its comments reworded, its code unchanged; the development copy's
# file: d0882655ee421fbd39d2d49f26c9d5b17d8550b4b59756f81158cc3fa338360b)
PRE_SHA256 = "5314cb78c9d021dd4fa0b2ce7efae5315cd532caeae4e06960296913f0016af6"
RULE = {"rho": 0.7, "phi_pi": 1.5, "phi_x": 0.5, "phi_e": 0.0}        # MP1's coefficients (test only)
CUT = {2026: {"qinv_scale": {"ccons": 0.9}}, 2027: {"qinv_scale": {"ccons": 0.95}}}
SR = (2026, 2027)
ACC = {"a": 1.5, "lag": 0.25, "driver": "demand"}


def report(res, name, ok, msg):
    res.append(bool(ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {msg}", flush=True)


def pre_module():
    """dynamic.py as it was before the accelerator (0.4.2.dev0, 13 Nov 2026, 3:02 PM), loaded as infinity_gem._dynamic_pre_acc_042 so its
    relative imports find today's infinity_gem.cge; the file's SHA-256 is compared first."""
    data = PRE.read_bytes()
    if hashlib.sha256(data).hexdigest() != PRE_SHA256:
        raise SystemExit(f"{PRE.name} is not the pre-accelerator dynamic.py (SHA-256 differs)")
    name = "infinity_gem._dynamic_pre_acc_042"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, PRE)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    if "sr_accelerator" in mod.DEFAULT_ASSUMPTIONS:
        raise SystemExit(f"{PRE.name} has the sr_accelerator option: it is not the pre-accelerator engine")
    return mod


def kwargs():
    from infinity_gem.settings import dynamic_kwargs
    kw = dynamic_kwargs("0.3 recommended", rice=True)
    kw["short_run_years"] = SR
    return kw


def record(p):
    t = p.table
    out = {k: np.asarray(t[k], float) for k in ("real_gdp", "cpi", "exr", "real_investment", "real_consumption")}
    for y in SR:
        for k in ("QINV", "QH", "EMP"):
            out[f"{y}:{k}"] = np.asarray(p.solutions[y][k], float).ravel()
    if p.monetary is not None:
        out["rate"] = np.asarray(p.monetary["policy_rate_gap_pp"], float)
    return out


def exact(a, b):
    """The largest absolute difference (0.0 = identical numbers) and whether every array is identical."""
    worst = max(float(np.max(np.abs(a[k] - b[k]))) if a[k].size else 0.0 for k in a)
    return worst, set(a) == set(b) and all(np.array_equal(a[k], b[k]) for k in a)


def run(d, shocks, acc=None, rule=False):
    d.a["sr_accelerator"] = acc
    try:
        return d.monetary_scenario(shocks, rule=RULE, theta=2.0) if rule else d.scenario(shocks)
    finally:
        d.a["sr_accelerator"] = None


def demand(sol):
    return float(np.sum(sol["QH"]) + np.sum(sol["QHA"]) + np.sum(sol["QG"]) + np.sum(sol["QE"]))


def by_hand(d, p, acc, shocks):
    """T4's recomputation from the path's solutions: (largest |z by hand - z used| in % of private investment, largest relative gap
    of QINV by commodity against the formula, Walras, GDP identity)."""
    b = d.base
    pub = {"ccons": DY.psa_public_construction_share(2023)} if acc.get("public", "psa") == "psa" else acc["public"]
    lag = acc.get("lag", 0.0)
    r = lambda t: np.log(demand(p.solutions[t]) / demand(b.solutions[t]))
    zu = p.accelerator["accelerator_z"]
    ez = max(abs(acc["a"] * ((1 - lag) * r(t) + lag * r(t - 1)) - float(zu[t])) * 100 for t in zu.index)
    m = d.m
    inv = [i for i in range(len(m.C)) if m.qinv[i] > 0]
    eq = 0.0
    for t in zu.index:
        mt = float(p.monetary.loc[t, "investment_scale"]) if p.monetary is not None else 1.0
        own = shocks[t].get("qinv_scale", {})
        e = float(np.exp(float(zu[t]))) - 1.0
        for i in inv:
            c = m.C[i]
            want = float(own.get(c, 1.0)) * mt + (1 - pub.get(c, 0.0)) * e * mt
            got = float(p.solutions[t]["QINV"][i]) / float(b.solutions[t]["QINV"][i])
            eq = max(eq, abs(got / want - 1))
    wal = max(abs(float(p.table.loc[t, "walras"])) for t in SR)
    gid = 0.0
    for t in SR:
        mdl = d.ms if p.table.loc[t, "closure"] == "short run" else d.m
        g = mdl.gdp(p.solutions[t])
        gid = max(gid, abs(g["nominal_expenditure"] / g["nominal_income"] - 1))
    return ez, eq, wal, gid


def main():
    t0 = time.time()
    res = []
    kw = kwargs()
    d = DynamicCGE(**kw)
    d.baseline()
    gap = lambda p, y: float(p.table.real_gdp[y] / d.base.table.real_gdp[y] - 1) * 100
    # T1: off = the engine before the option, to the bit
    try:
        old = pre_module()
        d0 = old.DynamicCGE(**kwargs())
        d0.baseline()
        e1, s1 = exact(record(d0.scenario(CUT)), record(d.scenario(CUT)))
        e2, s2 = exact(record(d0.monetary_scenario(CUT, rule=RULE, theta=2.0)), record(d.monetary_scenario(CUT, rule=RULE, theta=2.0)))
        report(res, "T1 off = the engine before the option (bit for bit)", s1 and s2,
               f"without the rule: identical {s1} (largest difference {e1:.1e}); with the rule: identical {s2} ({e2:.1e}); "
               f"baselines identical {exact({'g': np.asarray(d0.base.table.real_gdp)}, {'g': np.asarray(d.base.table.real_gdp)})[1]}")
        del d0
    except Exception as e:                                       # a test that errors fails; it is never skipped
        report(res, "T1", False, f"error {e!r}"[:300])
    # T2: a = 0 is off, to the bit
    try:
        p0, p0r = d.scenario(CUT), d.monetary_scenario(CUT, rule=RULE, theta=2.0)
        z0, z0r = run(d, CUT, {"a": 0.0, "lag": 0.25}), run(d, CUT, {"a": 0.0, "driver": "demand"}, rule=True)
        e1, s1 = exact(record(p0), record(z0))
        e2, s2 = exact(record(p0r), record(z0r))
        report(res, "T2 a = 0 is off (bit for bit)", s1 and s2, f"without the rule: identical {s1} ({e1:.1e}); with the rule: identical "
               f"{s2} ({e2:.1e}); iterations {z0r.monetary.attrs['iterations']} vs {p0r.monetary.attrs['iterations']}")
    except Exception as e:
        report(res, "T2", False, f"error {e!r}"[:300])
    # T3: zero shock with the accelerator on = baseline
    try:
        zs = {2026: {"qinv_scale": {"ccons": 1.0}}, 2027: {"qinv_scale": {"ccons": 1.0}}}
        z = run(d, zs, {"a": 3.0, "lag": 0.25})
        zr = run(d, zs, {"a": 3.0, "lag": 0.25}, rule=True)
        dev = max(float((p.table[k] / d.base.table[k] - 1).abs().max()) for p in (z, zr) for k in ("real_gdp", "cpi", "real_investment"))
        report(res, "T3 zero shock with the accelerator on = baseline", dev < 1e-9 and bool(z.accelerator.attrs["converged"]),
               f"largest relative deviation {dev:.1e}; z {[f'{v:.1e}' for v in z.accelerator['accelerator_z']]}; converged "
               f"{z.accelerator.attrs['converged']} in {z.accelerator.attrs['iterations']}")
    except Exception as e:
        report(res, "T3", False, f"error {e!r}"[:300])
    # T4: the fixed point by hand; accounts close; the slump deepens
    p_acc = None
    try:
        out, ok = [], True
        for rule in (False, True):
            p = run(d, CUT, dict(ACC), rule=rule)
            off = d.monetary_scenario(CUT, rule=RULE, theta=2.0) if rule else d.scenario(CUT)
            ez, eq, wal, gid = by_hand(d, p, ACC, CUT)
            conv = bool(p.accelerator.attrs["converged"]) and (not rule or bool(p.monetary.attrs["converged"]))
            deeper = gap(p, 2026) < gap(off, 2026) - 1e-3
            ok &= ez < 0.01 and eq < 1e-9 and wal < 1e-8 and gid < 1e-8 and conv and deeper
            out.append(f"{'with' if rule else 'without'} the rule: z by hand {ez:.1e} (% of private investment; tol 0.01), QINV by "
                       f"hand {eq:.1e}, Walras {wal:.1e}, GDP identity {gid:.1e}, converged {conv} in {p.accelerator.attrs['iterations']}; "
                       f"GDP 2026 {gap(p, 2026):+.3f}% vs {gap(off, 2026):+.3f}% off; scale 2026 "
                       f"{float(p.accelerator.loc[2026, 'accelerator_scale']):.4f}")
            if not rule:
                p_acc = p
        report(res, "T4 the fixed point recomputed by hand; accounts close; the slump deepens", ok, "; ".join(out))
    except Exception as e:
        report(res, "T4", False, f"error {e!r}"[:300])
    # T5: homogeneity (the 2026 baseline at twice the numeraire)
    try:
        t, bs = 2026, d.base.solutions[2026]
        x2 = bs.x.copy()
        for k_ in ("PDS", "PQ", "WF", "RK", "RL", "RN", "EXR"):
            if k_ in d.m.slices:
                x2[d.m.slices[k_]] *= 2.0
        b2 = d.m.solve({**bs.shocks, "cpi": 2.0}, x_start=x2)
        try:
            d.base.solutions[t] = b2
            ph = run(d, CUT, dict(ACC))
        finally:
            d.base.solutions[t] = bs
        def rd(a_, b_):                                          # relative difference; entries that are zero in both count 0
            a_, b_ = np.atleast_1d(np.asarray(a_, float)), np.atleast_1d(np.asarray(b_, float))
            r = np.abs(a_ - b_) / np.maximum(np.abs(b_), 1e-300)
            r[(a_ == 0) & (b_ == 0)] = 0.0
            if not np.all(np.isfinite(r)):
                return float("inf")
            return float(r.max())
        lab = [k for k, f in enumerate(d.m.F) if f.startswith("flab")]
        hq = max(rd(ph.solutions[y][k], p_acc.solutions[y][k]) for y in SR for k in ("QA", "QH", "QE", "QM", "QINV", "QG", "EMP"))
        hp = max(rd(np.asarray(ph.solutions[t][k], float)[idx] / 2.0, np.asarray(p_acc.solutions[t][k], float)[idx])
                 for k, idx in (("PQ", d.ms.iQ), ("PDS", d.ms.iD), ("WF", lab)))
        hp = max(hp, rd(float(ph.solutions[t]["CPI"]) / 2.0, float(p_acc.solutions[t]["CPI"])))
        hl = max(rd(ph.solutions[2027][k], p_acc.solutions[2027][k]) for k in ("PQ", "WF", "CPI"))
        hz = float((ph.accelerator["accelerator_z"] - p_acc.accelerator["accelerator_z"]).abs().max())
        report(res, "T5 homogeneity (the 2026 baseline at twice the numeraire)", b2.ok and max(hq, hp, hl) < 1e-9 and hz < 1e-9,
               f"baseline at CPI 2 solved {b2.ok}; quantities {hq:.1e}; 2026 prices / 2 {hp:.1e}; 2027 prices {hl:.1e}; z {hz:.1e}")
    except Exception as e:
        report(res, "T5", False, f"error {e!r}"[:300])
    # T6: tampers that T4's recomputation must catch
    try:
        orig_apply, orig_targets = d._acc_apply, d._acc_targets

        def bad_apply(sh, shocks, z, cfg):
            return orig_apply(sh, shocks, z, dict(cfg, public={}))

        def bad_targets(sim, reference, years, cfg):
            return orig_targets(sim, reference, years, dict(cfg, lag=0.0))
        d._acc_apply = bad_apply
        try:
            pt = run(d, CUT, dict(ACC))
        finally:
            del d._acc_apply
        ez1, eq1, _, _ = by_hand(d, pt, ACC, CUT)
        d._acc_targets = bad_targets
        try:
            pt2 = run(d, CUT, dict(ACC))
        finally:
            del d._acc_targets
        ez2, eq2, _, _ = by_hand(d, pt2, ACC, CUT)
        report(res, "T6 tampers caught", eq1 > 1e-4 and ez2 > 0.01,
               f"public share ignored: QINV by hand {eq1:.1e} (caught: {eq1 > 1e-4}); lag dropped: z by hand {ez2:.2e} % (caught: "
               f"{ez2 > 0.01})")
    except Exception as e:
        report(res, "T6", False, f"error {e!r}"[:300])
    # T7: guards
    try:
        bad = [{"a": -1.0}, {"a": float("nan")}, {"a": True}, {"a": 11.0}, {"lag": 1.5}, {"a": 1.0, "lag": -0.1},
               {"a": 1.0, "driver": "output"}, {"a": 1.0, "public": {"cfoo": 0.3}}, {"a": 1.0, "public": {"ccons": 1.0}},
               {"a": 1.0, "public": "imf"}, {"a": 1.0, "tol": 0.0}, {"a": 1.0, "max_iter": 0}, {"a": 1.0, "beta": 2},
               [1.0], {"a": "1"}]
        refused = 0
        for b_ in bad:
            try:
                DynamicCGE(**dict(kw, sr_accelerator=b_))
            except ValueError:
                refused += 1
        try:
            DynamicCGE(**dict(kw, hybrid=False, short_run_years=None, sr_accelerator={"a": 1.0}))
        except ValueError:
            refused += 1
        d.a["sr_accelerator"] = {"a": 1.0, "lag": 2.0}           # set after construction: refused before the path
        try:
            d.scenario(CUT)
        except ValueError:
            refused += 1
        finally:
            d.a["sr_accelerator"] = None
        n = len(bad) + 2
        report(res, "T7 guards", refused == n, f"{refused} of {n} bad settings refused")
    except Exception as e:
        report(res, "T7", False, f"error {e!r}"[:300])
    print(f"ACC1: {sum(res)} of {len(res)} pass; {time.time() - t0:.0f} s", flush=True)
    return all(res) and len(res) == 7


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(0 if main() else 1)
