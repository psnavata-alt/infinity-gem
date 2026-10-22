"""DSGE research, milestone 18 (19 Oct 2026, about 11:35 PM): the candidate DSGE's posterior on 2002Q1-2019Q4 against
2002Q1-2026Q2 with the COVID quarters missing.

Reads the saved chains (soe_htm, system prior on transmission strength): the short sample's final chains (default
outputs/dsge_ph_htm_draws_*_w1_ratio_seed[456].npy) and the long sample's (outputs/dsge_ph_htm_draws_*_w1_ratio_long*.npy).
For each parameter: posterior mean and 5-95% band in each sample, and the shift in units of the short sample's posterior s.d.
Parameters whose mean sits within 2% of a bound of the prior range are flagged (the productivity-shock check: sd_a's mode sat
at its upper bound on 2002-2019).
Run:  py compare_samples.py [short=pattern] [long=pattern]   (writes outputs/dsge_compare_samples_<stamp>.md)
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.argv = [a for a in sys.argv if not a.startswith("model=")] + ["model=htm"]
import estimate_rot as ER                       # noqa: E402  (model=htm: the prior table EST)
from transmission_benchmarks import HTM_NAMES   # noqa: E402

OUT = HERE.parents[1] / "outputs"


def load(pattern, long_ok):
    files = [f for f in sorted(OUT.glob(pattern))      # the sample and the GDP treatment (milestone 18b: "_stl") kept apart
             if long_ok == ("_long" in f.stem) and ("stl" in pattern) == ("_stl" in f.stem)]
    if not files:
        raise FileNotFoundError(pattern)
    return np.vstack([np.load(f) for f in files]), files


def main():
    arg = lambda k, d: next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith(k + "=")), d)
    S, fs = load(arg("short", "dsge_ph_htm_draws_*_w1_ratio_seed[456].npy"), False)
    L, fl = load(arg("long", "dsge_ph_htm_draws_*_w1_ratio_long*.npy"), True)
    lo = {e[0]: e[4] for e in ER.EST}
    hi = {e[0]: e[5] for e in ER.EST}
    rows = {}
    for j, n in enumerate(HTM_NAMES):
        s, l_ = S[:, j], L[:, j]
        near = lambda m: (abs(m - lo[n]) < 0.02 * (hi[n] - lo[n]) or abs(m - hi[n]) < 0.02 * (hi[n] - lo[n])) if n in lo else False
        rows[n] = {"2002-2019 mean": s.mean(), "5%": np.percentile(s, 5), "95%": np.percentile(s, 95),
                   "2002-2026 mean": l_.mean(), "5% ": np.percentile(l_, 5), "95% ": np.percentile(l_, 95),
                   "shift (short-sample s.d.)": (l_.mean() - s.mean()) / s.std() if s.std() > 0 else np.nan,
                   "at a bound": ("short " if near(s.mean()) else "") + ("long" if near(l_.mean()) else "")}
    t = pd.DataFrame(rows).T
    stamp = dt.datetime.now()
    big = t.index[np.abs(t["shift (short-sample s.d.)"].astype(float)) > 2].tolist()
    lines = [f"# The candidate DSGE on two samples ({stamp:%d %B %Y, %H:%M})", "",
             "**NOT FOR CITATION** (research code, `research/dsge/compare_samples.py`; milestone 18). soe_htm with the system prior "
             "on transmission strength. Short: 2002Q1-2019Q4 (" + ", ".join(f.name for f in fs) + f"; {len(S):,} draws). Long: "
             "2002Q1-2026Q2 with 2020Q1-2021Q4 missing (" + ", ".join(f.name for f in fl) + f"; {len(L):,} draws).", "",
             f"- Parameters that move by more than 2 short-sample standard deviations: {', '.join(big) or 'none'}.",
             f"- Means within 2% of a bound of the prior range: "
             f"{', '.join(f'{k} ({v.strip()})' for k, v in t['at a bound'].items() if v.strip()) or 'none'}.", "",
             t.to_markdown(floatfmt=".3f")]
    f = OUT / f"dsge_compare_samples_{stamp:%Y%m%d_%H%M}.md"
    f.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:6]))
    print("saved", f)


if __name__ == "__main__":
    main()
