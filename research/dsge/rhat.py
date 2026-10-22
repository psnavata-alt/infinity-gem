"""DSGE research (Stage 3), convergence check for the candidate DSGE (milestone 13; 19 Oct 2026, about 11:10 AM).

Gelman-Rubin potential scale reduction (R-hat, on split chains: each chain cut in two halves, Gelman et al. 2013, ch. 11) and an
effective sample size (initial-positive-sequence autocorrelation estimate, Geyer 1992) for each parameter, across the saved
chains of one specification (default: soe_htm with the system prior on transmission strength: outputs/dsge_ph_htm_draws_*_w1_ratio*.npy).
R-hat below about 1.1 is the usual threshold (1.01 for final work). Also: each chain's posterior mean of the key structural
parameters and of transmission strength, to see whether the chains agree on what matters for the CGE link.
Run:  py rhat.py [pattern=dsge_ph_htm_draws_*_w1_ratio*.npy]     (writes outputs/dsge_rhat_<stamp>.md)
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.argv = [a for a in sys.argv]
OUT = HERE.parents[1] / "outputs"
from transmission_benchmarks import HTM_NAMES   # noqa: E402


def split_rhat(chains):
    """chains: list of 1-d arrays (equal length after trimming). Split-R-hat."""
    n = min(len(c) for c in chains) // 2 * 2
    halves = []
    for c in chains:
        c = c[-n:]
        halves += [c[: n // 2], c[n // 2:]]
    X = np.array(halves)
    m, L = X.shape
    B = L * X.mean(1).var(ddof=1)
    W = X.var(1, ddof=1).mean()
    var_hat = (L - 1) / L * W + B / L
    return float(np.sqrt(var_hat / W))


def ess(x):
    x = x - x.mean()
    n = len(x)
    f = np.fft.rfft(x, 2 * n)
    ac = np.fft.irfft(f * np.conj(f))[:n] / (x.var() * n)
    s, k = 0.0, 1
    while k + 1 < n:
        pair = ac[k] + ac[k + 1]
        if pair < 0:
            break
        s += pair
        k += 2
    return n / (1 + 2 * s)


def main():
    pattern = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("pattern=")), "dsge_ph_htm_draws_*_w1_ratio*.npy")
    files = [f for f in sorted(OUT.glob(pattern))      # milestone 18/18b: samples and GDP treatments kept apart
             if all(tag in pattern or f"_{tag}" not in f.stem for tag in ("long", "stl"))]
    chains = [np.load(f) for f in files]
    oil_names = HTM_NAMES[:HTM_NAMES.index("rho_z") + 1] + ["rho_o"] + HTM_NAMES[HTM_NAMES.index("rho_z") + 1:] + ["sd_o"]
    if "htmu" in pattern:                              # milestone 19: the same layout, with the cost-push shock u for oil's o
        oil_names = [n.replace("_o", "_u") if n in ("rho_o", "sd_o") else n for n in oil_names]
    jz = HTM_NAMES.index("rho_z") + 1                  # 20 Oct 2026: soe_oilu (oil + cost push), 26 parameters
    oilu_names = HTM_NAMES[:jz] + ["rho_o", "rho_u"] + HTM_NAMES[jz:] + ["sd_u", "sd_o"]
    # 20 Oct 2026, about 10:00 AM (milestone 21): soe_oilw adds chi_o after rho_o, 27 parameters
    oilw_names = HTM_NAMES[:jz] + ["rho_o", "chi_o", "rho_u"] + HTM_NAMES[jz:] + ["sd_u", "sd_o"]
    if "thfix" in pattern or "thhi" in pattern:         # 20 Oct 2026, 6 PM (milestone 21b): theta calibrated, not estimated: 26 names
        oilu_names = [n for n in oilw_names if n != "theta"]
    names = {len(HTM_NAMES): HTM_NAMES, len(oil_names): oil_names, len(oilu_names): oilu_names,
             len(oilw_names): oilw_names}.get(
        chains[0].shape[1], [f"p{k}" for k in range(chains[0].shape[1])])
    # 21 Oct 2026: with model= (and the other estimate_rot arguments) on the command line, the names come from estimate_rot itself,
    # which is exact for every model (soe_htmk's 26 parameters would otherwise be mislabelled as soe_oilu's)
    if any(a.startswith("model=") for a in sys.argv[1:]):
        import estimate_rot as ER
        if len(ER.NAMES) == chains[0].shape[1]:
            names = list(ER.NAMES)
    rows = {}
    for j, nm in enumerate(names):
        rows[nm] = {"R-hat (split)": split_rhat([c[:, j] for c in chains]),
                    "ESS (sum of chains)": sum(ess(c[:, j]) for c in chains),
                    **{f"mean, {f.stem.split('draws_')[1]}": float(c[:, j].mean()) for f, c in zip(files, chains)}}
    tab = pd.DataFrame(rows).T
    worst = tab["R-hat (split)"].max()
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M")
    L = [f"# Convergence of the candidate DSGE's posterior ({dt.datetime.now():%d %B %Y, %H:%M})", "",
         f"**NOT FOR CITATION** (research code, `research/dsge/rhat.py`). {len(files)} chains ({', '.join(f.name for f in files)}); "
         f"{chains[0].shape[0]:,} retained draws each. Split R-hat below 1.1 = converged for practical purposes (1.01 for final "
         f"work). Largest R-hat: **{worst:.3f}** ({tab['R-hat (split)'].idxmax()}); parameters above 1.1: "
         f"{', '.join(tab.index[tab['R-hat (split)'] > 1.1]) or 'none'}.", "", tab.to_markdown(floatfmt=".3f")]
    path = OUT / f"dsge_rhat_{stamp}.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L)); print("saved", path)


if __name__ == "__main__":
    main()
