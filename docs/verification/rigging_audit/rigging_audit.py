"""Infinity GEM rigging audit (9 Oct 2026). A repeatable test a skeptic can rerun.

The question: could the model's results have been "rigged", i.e. written in, forced or patched instead of computed?
This script looks for the usual ways that happens and prints what it finds. It does not change Infinity GEM.

  A  Result numbers written into model code. Every number the checks expect (and the 21 frozen results of check R0)
     is searched for among the numbers written in the model's code. A match is allowed only for a declared INPUT
     (a shock size, an official statistic), listed below with its source; anything else is reported as UNEXPLAINED.
  B  Error handlers. Every `except` in the model code, and what it does: re-raise, report a failure, or carry on.
  C  Plugs and slack terms. Names that suggest a plug; then, by running the model, the Walras slack and every
     safety clamp (prices kept above zero, saving rates kept within -1..1) in a set of shocked solutions.
  D  Test strength. Every tolerance in the checks; checks that report PASS without testing anything.
  E  Solver convergence. Every place that solves the model and whether it looks at the convergence flag.
  F  Numbers written into report text. Numbers inside the text of reports and screens, which should come from the
     run, not be typed in.
  G  Fitting and randomness. Every optimiser or root-finder (what it fits, and to what) and every random draw.
  H  Tamper tests. The model is copied to a temporary folder, deliberately broken in seven ways (some of them the
     kind of rigging a skeptic fears), and the checks are run on the broken copy. Each must FAIL. An unbroken copy
     must PASS. The original folder is never touched.

Run:   py rigging_audit.py                 (audits the Infinity GEM folder this file is in)
       py rigging_audit.py --root "<folder>"   (any copy, e.g. Infinity GEM 0.3)
       py rigging_audit.py --quick         (skips part H, which takes about two minutes)
Report: RIGGING_AUDIT_RUN_<date>.md next to this file, or in Documents\\Infinity GEM - my runs\\rigging_audit if this
folder is read-only.
"""
from __future__ import annotations

import argparse
import ast
import csv
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODEL_DIRS = ("infinity_gem", "app", "scenarios")              # code that produces results
CHECKS = "checks/run_all_checks.py"

# Numbers that may appear both in model code and among the checks' expected values, because they are INPUTS (what is
# put into the model), not outputs. Each with its source. Matching is on the number as written in the code.
DECLARED_INPUTS = {
    238.3: "construction investment cut, ₱ bn (September 2026 infrastructure scenario input; DBM/September 2026)",
    242.93: "infrastructure shock used by an earlier fixed-price estimate, ₱ bn (an earlier workbook input)",
    90.21: "Ayuda cut, ₱ bn (September 2026 scenario input)",
    28009.93: "PSA nominal GDP 2025, ₱ bn (PSA National Accounts; used to scale shocks)",
    28060.0: "2025 GDP used by an earlier fixed-price estimate, ₱ bn (an earlier workbook input)",
    26160.604: "GDP in the 2023 SAM, ₱ bn (IFPRI SAM, value-added total)",
    17540000.0: "PSA official number of poor persons, 2023 (PSA Full-Year 2023 Official Poverty Statistics)",
    0.0154: "oil-price pass-through used by the price-only method (an earlier input)",
    0.0164: "food-price change used by the price-only method (an earlier input)",
    5.71: "PSA real GDP growth 2024, % (OpenSTAT 0052B5BPRA1)",
    4.40: "PSA real GDP growth 2025, % (OpenSTAT 0052B5BPRA1)",
    10.0: "a round default shock size (10%) in input boxes and test shocks",
    20.0: "a round test shock size (world oil price +20%) in the Simulator's presets, the settings comparison and check X1's "
          "fixed path; in infinity_gem/demand.py the search bound (-20) of the Frisch fit (added 14 Oct 2026)",
    58.0: "an assumed exchange rate (₱58 per US$) for converting US$ amounts: check M2's test input and the default of "
          "infinity_gem/stochastic.py (scenario scripts pass the observed rate) (added 14 Oct 2026)",
    100.0: "a round test input: check VN1's release elasticity e = 100 (large enough for the vintage model to reproduce mobile "
           "capital; 0.3.12, 20 Oct 2026); in model and scenario code 100.0 is the percent scale (x / 100.0, 100.0 * x) "
           "(added 20 Oct 2026, evening)",
}
# Matches read by a person (9 Oct 2026; re-read whenever they change): {(file, number): note}.
REVIEWED = {
    ("app/simulator.py", 0.683): "help text quoting an earlier workbook (outside reference) so users can compare; the "
                                 "Simulator's own result is computed and shown separately",
    ("app/simulator.py", 156329.0): "help text quoting an earlier published figure, as an example to compare",
    ("app/simulator.py", 835400.0): "help text quoting an earlier published figure, as an example to compare",
    ("scenarios/four_shock_scenario.py", 0.06): "a coefficient of an earlier VAR estimate used as an INPUT; check V1 re-estimates "
                                               "it from the data with infinity_gem/var.py",
}


# ----------------------------------------------------------------------------------------------------------- helpers
def py_files(root: Path, dirs=MODEL_DIRS):
    for d in dirs:
        for p in sorted((root / d).rglob("*.py")):
            if "__pycache__" not in p.parts:
                yield p


def rel(root: Path, p: Path) -> str:
    return p.relative_to(root).as_posix()


def parse(p: Path):
    return ast.parse(p.read_text(encoding="utf-8-sig"), filename=str(p))


def docstring_nodes(tree):
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.body:
            b = n.body[0]
            if isinstance(b, ast.Expr) and isinstance(b.value, ast.Constant) and isinstance(b.value.value, str):
                out.add(id(b.value))
    return out


def enclosing_functions(tree):
    """Map id(node) -> name of the innermost function containing it."""
    owner = {}

    def visit(node, fn):
        for ch in ast.iter_child_nodes(node):
            f = ch.name if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef)) else fn
            owner[id(ch)] = f
            visit(ch, f)
    visit(tree, "<module>")
    return owner


def literal_text(src_lines, node) -> str:
    try:
        if node.lineno != node.end_lineno:
            return ""
        b = src_lines[node.lineno - 1].encode("utf-8")              # ast offsets count UTF-8 bytes
        return b[node.col_offset:node.end_col_offset].decode("utf-8")
    except Exception:
        return ""


def decimals_of(text: str) -> int | None:
    t = text.replace("_", "").lower()
    if "e" in t or "x" in t:
        return None
    return len(t.split(".")[1]) if "." in t else 0


def sig_digits(text: str) -> int:
    t = text.replace("_", "").lower().split("e")[0].lstrip("-+")
    digits = t.replace(".", "").lstrip("0")
    return len(digits.rstrip("0")) if "." not in t else len(digits)


def is_year(text: str) -> bool:
    t = text.replace("_", "").rstrip(".")
    return t.isdigit() and 1990 <= int(t) <= 2060


def flatten(v):
    if isinstance(v, (list, tuple)):
        for x in v:
            yield from flatten(x)
    elif isinstance(v, (int, float)):
        yield float(v)


# ---------------------------------------------------------------------------------------- A: results written in code
def expected_numbers(root: Path):
    """Numbers the checks expect: constants in comparisons/lists inside check functions (not tolerances), and the
    frozen R0 results. Returns {value: where}."""
    out = {}
    p = root / CHECKS
    src = p.read_text(encoding="utf-8-sig").splitlines()
    tree = parse(p)
    own = enclosing_functions(tree)
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool):
            txt = literal_text(src, n)
            v = abs(float(n.value))
            if v < 1e-3 or v in (0.0, 1.0, 2.0) or sig_digits(txt) < 3 or is_year(txt):
                continue
            fn = own.get(id(n), "")
            if fn in ("<module>", "check", "deco", "run"):
                continue
            out.setdefault(v, f"check {fn} ({CHECKS}:{n.lineno})")
    ref = root / "checks" / "reference_live.json"
    if ref.exists():
        for k, v in json.loads(ref.read_text(encoding="utf-8")).items():
            for x in flatten(v):
                if abs(x) not in (0.0, 1.0):
                    out.setdefault(abs(x), f"R0 frozen result '{k}'")
    return out


def part_a(root: Path):
    targets = expected_numbers(root)
    hits, n_const = [], 0
    for p in py_files(root):
        src = p.read_text(encoding="utf-8-sig").splitlines()
        tree = parse(p)
        docs = docstring_nodes(tree)
        cands = []
        for n in ast.walk(tree):
            if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool):
                cands.append((n.lineno, literal_text(src, n), float(n.value)))
            elif isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docs:
                for m in re.finditer(r"(?<![\w.])-?\d[\d,_]*\.?\d*(?!\w)", n.value):    # numbers inside strings; not digit runs glued to letters (PSA table codes such as 0161B3FADB2 were read as numbers: fixed 20 Oct 2026)
                    t = m.group(0).replace(",", "")
                    try:
                        cands.append((n.lineno, m.group(0), float(t.replace("_", ""))))
                    except ValueError:
                        pass
        for line, txt, val in cands:
            if sig_digits(txt) < 3 or abs(val) < 1e-3 or is_year(txt):
                continue
            n_const += 1
            d = decimals_of(txt.replace(",", ""))
            for t, where in targets.items():
                # as written, or as a percentage / share; a rescaled match needs 4+ significant digits (fewer would match
                # by chance among this many numbers)
                for scale in ((1.0, 100.0, 0.01) if sig_digits(txt) >= 4 else (1.0,)):
                    tt = t * scale
                    tol = 0.5 * 10 ** (-d) if d is not None else 1e-9 * max(abs(tt), 1)
                    if abs(abs(val) - tt) <= tol * (1 + 1e-9) and abs(tt) >= 1e-3:
                        dec = next((s for k, s in DECLARED_INPUTS.items() if abs(abs(val) - k) <= 1e-9 * max(k, 1)), None)
                        rev = next((s for (f_, k), s in REVIEWED.items()
                                    if f_ == rel(root, p) and abs(abs(val) - k) <= 1e-9 * max(k, 1)), None)
                        hits.append(dict(file=rel(root, p), line=line, text=txt, expected=where,
                                         status=("declared input: " + dec) if dec else ("reviewed: " + rev) if rev
                                         else "UNEXPLAINED"))
                        break
                else:
                    continue
                break
    return dict(targets=len(targets), constants=n_const, hits=hits)


# ------------------------------------------------------------------------------------------ B: error handlers
def handler_kind(h: ast.ExceptHandler) -> str:
    body = h.body
    if any(isinstance(n, ast.Raise) for b in body for n in ast.walk(b)):
        return "re-raises or raises a clearer error"
    txt = ast.unparse(ast.Module(body=body, type_ignores=[]))
    if re.search(r"ok\s*=\s*False|['\"]ok['\"]\s*:\s*False|dict\(ok=False", txt):
        return "reports a failure (ok=False)"
    if all(isinstance(b, (ast.Pass, ast.Continue)) for b in body):
        return "CARRIES ON SILENTLY (pass/continue)"
    for b in body:
        if isinstance(b, ast.Return):
            v = b.value
            if v is None or (isinstance(v, ast.Constant) and v.value in (None, False)):
                return "returns None/False"
            if isinstance(v, ast.Constant) or (isinstance(v, ast.UnaryOp) and isinstance(v.operand, ast.Constant)):
                return f"RETURNS A FIXED VALUE ({ast.unparse(v)})"
    return "other: " + txt.splitlines()[0][:80]


def part_b(root: Path):
    rows = []
    for p in py_files(root):
        tree = parse(p)
        own = enclosing_functions(tree)
        for n in ast.walk(tree):
            if isinstance(n, ast.Try):
                for h in n.handlers:
                    rows.append(dict(file=rel(root, p), line=h.lineno, function=own.get(id(n), ""),
                                     catches=ast.unparse(h.type) if h.type else "EVERYTHING (bare except)",
                                     does=handler_kind(h)))
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and ast.unparse(n.func).endswith("filterwarnings") and n.args \
                    and isinstance(n.args[0], ast.Constant) and n.args[0].value == "ignore":
                rows.append(dict(file=rel(root, p), line=n.lineno, function=own.get(id(n), ""),
                                 catches="warnings", does="warnings switched off"))
    return rows


# ----------------------------------------------------------------------------------- C: plugs, slack and clamps
PLUG_WORDS = r"walras|slack|plug|fudge|dummy|missing|residual|discrep|statistical|balanc|adjust|fix_?up|force"


def part_c_static(root: Path):
    rows = []
    for p in py_files(root, ("infinity_gem",)):
        tree = parse(p)
        seen = set()
        for n in ast.walk(tree):
            name = n.id if isinstance(n, ast.Name) else n.attr if isinstance(n, ast.Attribute) else \
                n.arg if isinstance(n, ast.arg) else n.name if isinstance(n, (ast.FunctionDef, ast.ClassDef)) else None
            if name and re.search(PLUG_WORDS, name, re.I) and (name, p) not in seen:
                seen.add((name, p))
                rows.append(dict(file=rel(root, p), line=getattr(n, "lineno", 0), name=name))
    return rows


def part_c_runtime(root: Path):
    """Solve a set of shocks in every closure and report the Walras slack and whether any safety clamp is binding."""
    sys.path[:0] = [str(root), str(root / "scenarios")]
    import numpy as np
    import warnings
    warnings.filterwarnings("ignore")
    from infinity_gem.cge import CGE
    closures = {"long run": {}, "savings": {"closure": "savings"},
                "short run": {"closure": "keynesian", "unemployed": ("flab-n", "flab-p"), "capital": "fixed"}}
    shocks = {"construction -10%": {"qinv_scale": {"ccons": 0.9}},
              "world chemical/petroleum prices +30%": {"pwm_scale": {"cchem": 1.3}},
              "remittances -20%": {"remit_scale": 0.8},
              "tariffs abolished": {"tm_scale": 0.0},
              "mixed (check C4)": {"pwm_scale": {"cchem": 1.3}, "remit_scale": 0.8, "qinv_scale": {"ccons": 0.8}},
              "capital stock +5%, productivity +2%": {"qfs_scale": {"fcap": 1.05}, "tfp_scale": 1.02}}
    rows = []
    for cn, kw in closures.items():
        m = CGE.from_sam(**kw)
        b = m.solve()
        for sn, spec in shocks.items():
            if cn == "short run" and "capital stock" in sn:
                spec = {"tfp_scale": 1.02}
            s = m.solve(spec)
            v = s.v
            prices = np.concatenate([v["PQ"], v["PDS"], v["PX"], v["PA"], v["PVA"], np.ravel(v["W"][m.use])])
            mps = m.mps * (1 + v["MPSADJ"])
            g = m.gdp(s)
            rows.append(dict(closure=cn, shock=sn, solved=s.ok, residual=s.residual_max,
                             walras=abs(v["WALRAS"]) / m.qinv.sum(),
                             gdp_gap=abs(g["nominal_expenditure"] - g["nominal_income"]),
                             min_price=float(prices.min()), clamp_price=bool(prices.min() <= 1e-9),
                             clamp_mps=bool(np.abs(mps).max() >= 1),
                             negative_qty=bool(min(v["QD"].min(), v["QM"].min(), v["QE"].min(), v["QA"].min()) < -1e-9),
                             real_gdp_pct=(g["real"] / m.gdp(b)["real"] - 1) * 100))
    # data treatments that could act as plugs: re-exports, missing accounts, the 2018 balancing, LES defaults
    m = CGE.from_sam()
    from infinity_gem import paths
    from infinity_gem.sam import SAM
    raw18 = SAM.load(paths.SAM_2018).table
    bal18 = SAM.load_for_model(paths.SAM_2018).table
    adj = (bal18 - raw18.loc[bal18.index, bal18.columns]).abs()
    treat = dict(reexports_bn=float(m.rex.sum()), reexport_goods=[c for c, x in zip(m.C, m.rex) if x > 0],
                 balancing_2018_max_cell=float(adj.values.max()), balancing_2018_total=float(adj.values.sum()) / 2,
                 sam_2018_total=float(raw18.values.sum()))
    from infinity_gem.microsim import Microsim
    ms = Microsim()
    raw = __import__("pandas").read_csv(paths.FIES_POVLINES)
    treat["fies_rows_dropped"] = int(len(raw) - len(ms.f))
    treat["fies_unmapped_groups"] = int((~ms.f["grp"].isin(m.H)).sum())
    return rows, treat


# ---------------------------------------------------------------------------------------- D: test strength
def part_d(root: Path):
    p = root / CHECKS
    src = p.read_text(encoding="utf-8-sig").splitlines()
    tree = parse(p)
    tols, always = [], []
    for fn in [n for n in tree.body if isinstance(n, ast.FunctionDef)]:
        code = next((ast.literal_eval(d.args[0]) for d in fn.decorator_list
                     if isinstance(d, ast.Call) and ast.unparse(d.func) == "check"), None)
        if not code:
            continue
        for n in ast.walk(fn):
            if isinstance(n, ast.Compare):
                for op, right in zip(n.ops, n.comparators):
                    if isinstance(op, (ast.Lt, ast.LtE)) and isinstance(right, ast.Constant) \
                            and isinstance(right.value, (int, float)):
                        left = ast.unparse(n.left if len(n.ops) == 1 else n)
                        tols.append(dict(check=code, line=n.lineno, tolerance=float(right.value),
                                         test=src[n.lineno - 1].strip()[:110] if len(left) > 110 else left))
            if isinstance(n, ast.Return) and isinstance(n.value, ast.Tuple) and n.value.elts \
                    and isinstance(n.value.elts[0], ast.Constant) and n.value.elts[0].value is True:
                always.append(dict(check=code, line=n.lineno, text=src[n.lineno - 1].strip()[:120]))
    return tols, always


# --------------------------------------------------------------------------------- E: solver convergence
def part_e(root: Path):
    rows = []
    for p in py_files(root):
        tree = parse(p)
        funcs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        scopes = funcs + [tree]
        for sc in scopes:
            body_nodes = list(ast.walk(sc)) if sc is not tree else \
                [n for b in tree.body if not isinstance(b, (ast.FunctionDef, ast.ClassDef)) for n in ast.walk(b)]
            if sc is not tree:
                inner = {id(x) for f in ast.walk(sc) if f is not sc and isinstance(f, ast.FunctionDef) for x in ast.walk(f)}
                body_nodes = [n for n in body_nodes if id(n) not in inner]
            calls = [n for n in body_nodes if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                     and n.func.attr in ("solve", "scenario", "baseline") and "st." not in ast.unparse(n.func)]
            calls = [c for c in calls if not ast.unparse(c.func).startswith(("np.", "la.", "linalg", "self.io"))]
            if not calls:
                continue
            text = ast.unparse(sc) if sc is not tree else "\n".join(ast.unparse(b) for b in tree.body
                                                                       if not isinstance(b, (ast.FunctionDef, ast.ClassDef)))
            # acting on the flag (assert or if on .ok / ["ok"], or raising an error); printing it is not enough
            looks = bool(re.search(r"(assert|if)\b[^\n]*(\.ok\b|\[['\"]ok['\"]\]|get\(['\"]ok['\"]\))|raise RuntimeError", text))
            solve_calls = [c for c in calls if c.func.attr == "solve"]
            if not solve_calls:
                continue                       # scenario()/baseline() raise RuntimeError themselves on failure
            name = getattr(sc, "name", "<script body>")
            rows.append(dict(file=rel(root, p), line=solve_calls[0].lineno, function=name, solves=len(solve_calls),
                             checks_flag=looks))
    return rows


# ------------------------------------------------------------------------------- F: numbers typed into report text
def part_f(root: Path):
    rows = []
    pat = re.compile(r"(?<![\w.%])[-+−]?(?:₱\s?)?\d{1,3}(?:,\d{3})+(?:\.\d+)?|(?<![\w.])[-+−]?\d+\.\d+\s?(?:%|pp|bn)?")
    for p in py_files(root, ("app", "scenarios")):
        tree = parse(p)
        docs = docstring_nodes(tree)
        for n in ast.walk(tree):
            if isinstance(n, ast.JoinedStr):
                parts = [v.value for v in n.values if isinstance(v, ast.Constant)]
            elif isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docs:
                parts = [n.value]
            else:
                continue
            for s in parts:
                for m in pat.finditer(s):
                    if m.group(0).strip() in ("0.2", "0.3"):        # Infinity GEM version numbers
                        continue
                    ctx = s[max(0, m.start() - 40): m.end() + 30].replace("\n", " ")
                    rows.append(dict(file=rel(root, p), line=n.lineno, number=m.group(0).strip(), context=ctx))
    # de-duplicate (an f-string's constant parts are also visited as constants)
    uniq = {(r["file"], r["line"], r["number"]): r for r in rows}
    return list(uniq.values())


# ------------------------------------------------------------------------------- G: fitting and randomness
def part_g(root: Path):
    rows = []
    for p in py_files(root):
        tree = parse(p)
        own = enclosing_functions(tree)
        for n in ast.walk(tree):
            if isinstance(n, ast.Call):
                f = ast.unparse(n.func)
                last = f.split(".")[-1]
                if last in ("root", "brentq", "minimize", "minimize_scalar", "least_squares", "fsolve", "newton",
                            "bisect", "curve_fit"):
                    rows.append(dict(file=rel(root, p), line=n.lineno, function=own.get(id(n), ""), call=f, kind="fit/solve"))
                if re.search(r"random|default_rng|seed", f):
                    rows.append(dict(file=rel(root, p), line=n.lineno, function=own.get(id(n), ""), call=f, kind="random"))
    return rows


# ---------------------------------------------------------------------------------------- H: tamper tests
TAMPERS = [
    dict(name="Tariff revenue left out of government income",
         why="an accounting error: money disappears from the accounts",
         file="infinity_gem/cge.py", old="+ MTAX.sum() + STAX.sum() + ATAX.sum()", new="+ STAX.sum() + ATAX.sum()",
         expect=["C1"]),
    dict(name="A leak that shows only after a shock (import bill at pre-shock world prices)",
         why="an error invisible in the base year: the base-year SAM is still reproduced",
         file="infinity_gem/cge.py", old="fcu_out = (pwm * (QM + self.rex)).sum()",
         new="fcu_out = (self.pwm * (QM + self.rex)).sum()", expect=["C4"]),
    dict(name="A hidden plug: 0.1% extra demand in every factor market",
         why="a plug term, like the archived R scripts' Missing_Demand_0",
         file="infinity_gem/cge.py", old="- self.QFS0[k] * sh[\"qfs_scale\"][k]) / self.QFS0[k])",
         new="- self.QFS0[k] * sh[\"qfs_scale\"][k]) / self.QFS0[k] + 0.001)", expect=["C1"]),
    dict(name="Solver stopped early but reports success",
         why="a result used without convergence",
         file="infinity_gem/cge.py", old="ok = bool(np.abs(R).max() < 1e-7)", new="ok = True",
         extra=[("\"maxfev\": 200 * (self.n + 1)", "\"maxfev\": 3"),
                ("if not out.success or np.abs(out.fun).max() > 1e-7:", "if False:")],
         expect=["C3", "C4"]),
    dict(name="Headline result rigged: Simulator's real GDP effect scaled by 0.9",
         why="a hard-coded adjustment to an answer",
         file="app/engines.py", old="\"Real GDP (%)\": pct(gs[\"real\"], gb[\"real\"]),",
         new="\"Real GDP (%)\": pct(gs[\"real\"], gb[\"real\"]) * 0.9,", expect=["A1", "R0"]),
    dict(name="A parameter quietly changed: Armington elasticity 2.0 -> 2.2",
         why="a parameter changed to move results; the model is still internally consistent",
         file="infinity_gem/cge.py", old="\"sigma_q\": 2.0,", new="\"sigma_q\": 2.2,", expect=["R0"]),
    dict(name="One number in the data changed (2023 SAM, one cell +₱1 bn)",
         why="the data edited to move results",
         data_cell=True, expect=["D1", "D2"]),
]
RUN_ORDER = ["d1", "d2", "c1", "c3", "c4", "c5", "a1", "r0"]

RUNNER = r'''
import json, sys, io, contextlib, warnings
warnings.filterwarnings("ignore")
root = sys.argv[1]
sys.path[:0] = [root + "/checks", root, root + "/scenarios"]
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    import run_all_checks as R
    for n in sys.argv[2].split(","):
        getattr(R, n)()
print(json.dumps([[c, bool(ok), ((d or "").splitlines() or ["(no detail)"])[0][:160]] for c, _, ok, d in R.results]))
'''


def copy_for_tamper(root: Path, dst: Path):
    for d in ("infinity_gem", "app", "scenarios", "checks", "validation", "data", "tools"):
        if (root / d).exists():
            shutil.copytree(root / d, dst / d, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.xlsx~"))
    for f in ("requirements.txt",):
        if (root / f).exists():
            shutil.copy2(root / f, dst / f)
    # a 0.2 backup next to the copy is not needed: R0 compares with the frozen checks/reference_live.json


def edit_sam_cell(dst: Path):
    p = dst / "data" / "raw" / "sam" / "002_IFPRI_SAM_PHL_2023_SAM.csv"
    raw = p.read_text(encoding="utf-8-sig")
    rows = list(csv.reader(raw.splitlines()))
    for i, r in enumerate(rows[1:], start=1):
        for j in range(2, len(r)):
            try:
                v = float(r[j].replace(",", ""))
            except ValueError:
                continue
            if v > 10:
                r[j] = repr(v + 1.0)
                with open(p, "w", encoding="utf-8-sig", newline="") as fh:
                    csv.writer(fh).writerows(rows)
                return f"row '{r[1]}', column {rows[0][j]}: {v} -> {v + 1.0}"
    raise RuntimeError("no SAM cell found to edit")


def run_checks(copy: Path, names):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    env.pop("INFINITY_GEM_MY_RUNS", None)
    r = subprocess.run([sys.executable, "-c", RUNNER, str(copy), ",".join(names)], capture_output=True, text=True,
                       encoding="utf-8", env=env, timeout=900)
    if r.returncode != 0 or not r.stdout.strip():
        return None, (r.stderr or r.stdout)[-600:]
    return {c: (ok, d) for c, ok, d in json.loads(r.stdout.strip().splitlines()[-1])}, ""


def part_h(root: Path):
    out = []
    base = Path(tempfile.mkdtemp(prefix="infinity_gem_tamper_"))
    try:
        ctrl = base / "control"
        copy_for_tamper(root, ctrl)
        res, err = run_checks(ctrl, RUN_ORDER)
        out.append(dict(name="Control: unbroken copy", expect=[], result=res, error=err, edit="none"))
        for t in TAMPERS:
            dst = base / re.sub(r"\W+", "_", t["name"])[:40]
            shutil.copytree(ctrl, dst, ignore=shutil.ignore_patterns("__pycache__"))
            if t.get("data_cell"):
                edit = edit_sam_cell(dst)
            else:
                f = dst / t["file"]
                s = f.read_text(encoding="utf-8")
                for old, new in [(t["old"], t["new"])] + t.get("extra", []):
                    if s.count(old) != 1:
                        raise RuntimeError(f"tamper '{t['name']}': the code to break was not found exactly once in "
                                           f"{t['file']} ({old!r}); the code has changed, so update this audit")
                    s = s.replace(old, new)
                f.write_text(s, encoding="utf-8")
                edit = f"{t['file']}: `{t['old']}` -> `{t['new']}`"
            res, err = run_checks(dst, RUN_ORDER)
            out.append(dict(name=t["name"], why=t["why"], expect=t["expect"], result=res, error=err, edit=edit))
            shutil.rmtree(dst, ignore_errors=True)
    finally:
        shutil.rmtree(base, ignore_errors=True)
    return out


# ------------------------------------------------------------------------------------------------ report
def md_table(rows, cols):
    if not rows:
        return "_none_\n"
    s = "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n"
    for r in rows:
        s += "| " + " | ".join(str(r.get(c, "")).replace("|", "\\|").replace("\n", " ") for c in cols) + " |\n"
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(HERE.parent.parent.parent))
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    root = Path(a.root).resolve()
    stamp = dt.datetime.now()
    version = next((ln for ln in (root / "README.md").read_text(encoding="utf-8").splitlines() if "**Version" in ln), "")[:60] \
        if (root / "README.md").exists() else ""
    L = [f"# Infinity GEM rigging audit: run of {stamp:%d %B %Y, %H:%M}", "",
         f"Folder audited: `{root}`  ", f"{version}  ",
         f"Script: `docs/verification/rigging_audit/rigging_audit.py` (what each part does: the script's first lines).", ""]
    summary = []

    print("A: result numbers in model code ...", flush=True)
    A = part_a(root)
    unexpl = [h for h in A["hits"] if h["status"] == "UNEXPLAINED"]
    summary.append(("A", "Result numbers written into model code", f"{A['targets']} expected numbers searched among "
                    f"{A['constants']} numbers written in the model code: {len(A['hits'])} matches, "
                    f"{len(unexpl)} unexplained"))
    L += ["## A. Result numbers written into model code", "",
          f"{A['targets']} numbers the checks expect (including the 21 frozen R0 results, every element) were searched for "
          f"among the {A['constants']} numbers with 3 or more significant digits written in `infinity_gem/`, `app/` and "
          "`scenarios/` (also inside text, and as %, thousands or millions). A match is fine only if the number is an "
          "INPUT (declared in the script with its source).", "", md_table(A["hits"], ["file", "line", "text", "expected", "status"])]

    print("B: error handlers ...", flush=True)
    B = part_b(root)
    summary.append(("B", "Error handlers", f"{len(B)} handlers; carry on silently: "
                    f"{sum('SILENTLY' in r['does'] for r in B)}; return a fixed value: {sum('FIXED' in r['does'] for r in B)}"))
    L += ["## B. Error handlers", "", "Every `except` in the model code and what it does when something goes wrong.", "",
          md_table(B, ["file", "line", "function", "catches", "does"])]

    print("C: plugs, slack, clamps (runs the model) ...", flush=True)
    Cs = part_c_static(root)
    Cr, treat = part_c_runtime(root)
    import math
    worst_w = max(r["walras"] for r in Cr)
    bad = [r for r in Cr if not r["solved"] or r["clamp_price"] or r["clamp_mps"] or r["negative_qty"] or r["walras"] > 1e-9]
    summary.append(("C", "Plugs, slack and clamps", f"{len(Cr)} shocked solutions: largest Walras slack "
                    f"{worst_w:.1e} of investment; solutions with a binding clamp, a negative quantity or no "
                    f"convergence: {len(bad)}"))
    for r in Cr:
        for k in ("residual", "walras", "gdp_gap", "min_price"):
            r[k] = f"{r[k]:.1e}"
        r["real_gdp_pct"] = f"{r['real_gdp_pct']:+.3f}"
    L += ["## C. Plugs, slack terms and clamps", "",
          "**Names in `infinity_gem/` that suggest a plug** (each is explained in the written report):", "",
          md_table(Cs, ["file", "line", "name"]),
          "**Shocked solutions.** The only slack variable is WALRAS (savings minus investment); it must be zero. "
          "`_pos()` keeps prices above 1e-12 and `np.clip` keeps saving rates within -1..1: a clamp that binds would "
          "mean the solution is not a real equilibrium.", "",
          md_table(Cr, ["closure", "shock", "solved", "residual", "walras", "gdp_gap", "min_price", "clamp_price",
                        "clamp_mps", "negative_qty", "real_gdp_pct"]),
          "**Data treatments that could act as plugs:**", "",
          f"- Re-exports (exports above domestic output, treated as imports re-exported at fixed quantities): "
          f"₱{treat['reexports_bn']:,.1f} bn, goods {treat['reexport_goods']}.",
          f"- Balancing of the 2018 SAM (published in whole billions): largest cell change ₱{treat['balancing_2018_max_cell']:,.2f} bn; "
          f"total change ₱{treat['balancing_2018_total']:,.1f} bn (the SAM's total is ₱{treat['sam_2018_total']:,.0f} bn). "
          "The 2023 SAM is used as published.",
          f"- FIES households dropped for missing values: {treat['fies_rows_dropped']}; households in no SAM group "
          f"(would get no change): {treat['fies_unmapped_groups']}.", ""]

    print("D: test strength ...", flush=True)
    tols, always = part_d(root)
    wide = [t for t in tols if t["tolerance"] >= 1e-3]
    summary.append(("D", "Test strength", f"{len(tols)} tolerances, {len(wide)} of 0.001 or more (each explained); "
                    f"checks that can PASS without testing: {len(always)}"))
    L += ["## D. Test strength", "", "**Checks that return PASS without testing** (a skipped test must not count as passed):", "",
          md_table(always, ["check", "line", "text"]),
          "**Tolerances of 0.001 or more** (smaller ones are listed below):", "", md_table(wide, ["check", "line", "tolerance", "test"]),
          "<details><summary>All tolerances</summary>", "", md_table(tols, ["check", "line", "tolerance", "test"]), "</details>", ""]

    print("E: solver convergence ...", flush=True)
    E = part_e(root)
    summary.append(("E", "Solver convergence", f"{len(E)} places solve the model; without a look at the convergence flag: "
                    f"{sum(not r['checks_flag'] for r in E)}"))
    L += ["## E. Solver convergence", "",
          "Each function or script that calls `.solve()` and whether it looks at the result's convergence flag (`ok`) or "
          "residual. The dynamic model's `baseline()`/`scenario()` stop with an error by themselves if a year does not solve.", "",
          md_table(E, ["file", "line", "function", "solves", "checks_flag"])]

    print("F: numbers typed into report text ...", flush=True)
    F = part_f(root)
    summary.append(("F", "Numbers typed into report text", f"{len(F)} numbers written inside report or screen text in "
                    "`app/` and `scenarios/` (each to be read: input, source or label?)"))
    L += ["## F. Numbers typed into report text", "",
          "Numbers written inside text in `app/` and `scenarios/` (computed numbers enter text through `{...}` and do not "
          "appear here). Each should be an input, a source or a label, not a result.", "",
          md_table(F, ["file", "line", "number", "context"])]

    print("G: fitting and randomness ...", flush=True)
    G = part_g(root)
    summary.append(("G", "Fitting and randomness", f"{sum(r['kind'] == 'fit/solve' for r in G)} optimiser/root-finder calls, "
                    f"{sum(r['kind'] == 'random' for r in G)} random draws"))
    L += ["## G. Fitting and randomness", "", md_table(G, ["file", "line", "function", "call", "kind"])]

    if not a.quick:
        print("H: tamper tests (about two minutes) ...", flush=True)
        H = part_h(root)
        rows = []
        for h in H:
            res = h["result"] or {}
            if h["name"].startswith("Control"):
                ok = bool(res) and all(v[0] for v in res.values())
                verdict = "all PASS (as it should)" if ok else "**PROBLEM: the unbroken copy does not pass**"
            else:
                caught = [c for c in h["expect"] if c in res and not res[c][0]]
                failed = [c for c, v in res.items() if not v[0]]
                ok = bool(caught)
                verdict = (f"caught by {', '.join(failed)}" if ok else "**NOT CAUGHT**")
            rows.append(dict(tamper=h["name"], why=h.get("why", ""), edit=h["edit"], expected=", ".join(h["expect"]),
                             result=verdict + (f" (error: {h['error'][:200]})" if h["error"] else "")))
            h["ok"] = ok
        summary.append(("H", "Tamper tests", f"{sum(h['ok'] for h in H[1:])} of {len(H) - 1} deliberate breaks caught; "
                        f"control copy passes: {H[0]['ok']}"))
        L += ["## H. Tamper tests", "",
              f"A copy of the model (in a temporary folder, deleted afterwards) is broken on purpose and checks "
              f"{', '.join(c.upper() for c in RUN_ORDER)} are run on it. Each break must make at least one check FAIL.", "",
              md_table(rows, ["tamper", "why", "edit", "expected", "result"])]
        for h in H:
            if h["result"]:
                L += [f"<details><summary>{h['name']}: every check</summary>", "",
                      md_table([dict(check=c, result="PASS" if v[0] else "FAIL", detail=v[1]) for c, v in h["result"].items()],
                               ["check", "result", "detail"]), "</details>", ""]

    head = ["## Summary", "", md_table([dict(part=p, what=w, result=r) for p, w, r in summary], ["part", "what", "result"])]
    L = L[:6] + head + L[6:]
    text = "\n".join(L) + "\n"
    name = f"RIGGING_AUDIT_RUN_{stamp:%Y%m%d_%H%M}.md"
    try:
        out = HERE / name
        out.write_text(text, encoding="utf-8")
    except OSError:
        my = Path(os.environ.get("INFINITY_GEM_MY_RUNS", str(Path.home() / "Documents" / "Infinity GEM - my runs"))) / "rigging_audit"
        my.mkdir(parents=True, exist_ok=True)
        out = my / name
        out.write_text(text, encoding="utf-8")
    print()
    for p, w, r in summary:
        print(f"{p}  {w}: {r}")
    print(f"\nReport: {out}")


if __name__ == "__main__":
    main()
