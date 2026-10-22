"""DSGE research, milestone 18b diagnostic (20 Oct 2026, about 01:40): which posterior mode do the data favour?

Chains of one specification can settle in different regions (2002-2026, STL GDP: seeds 2-3 with a productivity shock of
s.d. about 2-3, seed 4 with about 7.7 and stickier domestic prices). For a random subsample of each chain's draws this script
evaluates the pieces of the log posterior that estimate_rot.py samples from: log prior, log likelihood, the system-prior
penalty on transmission strength, and their total. A mode whose draws have a clearly lower total holds little posterior mass;
similar totals mean a genuinely bimodal posterior.
Run:  py chain_logpost.py model=htm sample=long gdp=stl pattern=dsge_ph_htm_draws_*_w1_ratio_long_stl*.npy [n=150]
(the model, sample and gdp arguments are read by estimate_rot.py; writes outputs/dsge_chain_logpost_<stamp>.md)
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import estimate_rot as ER   # noqa: E402  (reads model=, sample=, gdp=, prior= from the command line)

OUT = HERE.parents[1] / "outputs"


def main():
    pattern = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("pattern=")), None)
    n = int(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("n=")), 150))
    w = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("w=")), 1.0))
    files = sorted(OUT.glob(pattern))
    Z = ER.observables()
    rng = np.random.default_rng(0)
    rows = {}
    j_sda = ER.NAMES.index("sd_a")
    for f in files:
        D = np.load(f)
        idx = rng.choice(len(D), size=min(n, len(D)), replace=False)
        vals = []
        for i in idx:
            p = ER.pieces(D[i], Z)
            if p is None:
                continue
            pen = -0.5 * w * (p[3] if ER.PRIOR in getattr(ER, "RATIO_PRIORS", ("ratio",)) else p[2])   # 21 Oct: ratio_cpi, ratio2 too
            vals.append((p[0], p[1], pen, p[0] + p[1] + pen, D[i, j_sda]))
        v = np.array(vals)
        rows[f.name] = {"draws evaluated": len(v), "sd_a (mean)": v[:, 4].mean(), "log prior": v[:, 0].mean(),
                        "log likelihood": v[:, 1].mean(), "system-prior penalty": v[:, 2].mean(),
                        "log posterior (mean)": v[:, 3].mean(), "log posterior (max)": v[:, 3].max()}
        print(f.name, {k: round(x, 2) for k, x in rows[f.name].items()}, flush=True)
    t = pd.DataFrame(rows).T
    stamp = dt.datetime.now()
    path = OUT / f"dsge_chain_logpost_{stamp:%Y%m%d_%H%M}.md"
    path.write_text("\n".join([f"# Log posterior by chain ({stamp:%d %B %Y, %H:%M})", "",
                               f"**NOT FOR CITATION** (research code, `research/dsge/chain_logpost.py`). Model {ER.MODEL}, sample "
                               f"{ER.SAMPLE}, GDP {ER.GDP_SA}; {n} random draws per chain; pattern `{pattern}`.", "",
                               t.to_markdown(floatfmt=".2f")]) + "\n", encoding="utf-8")
    print("saved", path)


if __name__ == "__main__":
    main()
