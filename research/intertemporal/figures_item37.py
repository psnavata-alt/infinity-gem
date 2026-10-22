"""Figures for the forward-looking CGE (18 Oct 2026, about 2:40 AM; the documentation gap "outputs are tables only"). NOT FOR CITATION.

Figure 1: measure C announced in 2026 vs a surprise in 2027, Keynesian short run (beta 7.14) with idle workers in 2026-27:
          real GDP against the shortfall path, low and high public capital (small multiples).
Figure 2: the foreign-saving bridge base path: (a) the model's balance-of-payments current account against the IMF's path; (b) foreign
          assets (the deviation from the stable-NIIP path) over 50 years.
Colours: the reference categorical palette, slots 1-2 (validated: CVD dE 24.7, contrast >= 3:1 on the light surface).
Run:  py research/intertemporal/figures_item37.py      Output: outputs/figures_item37_<date>/*.png
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))
import pf_cge9 as P                                   # noqa: E402
import build2_keynesian_short_run as B                # noqa: E402
from infinity_gem.settings import PUBLIC_CAPITAL          # noqa: E402

SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"
S1, S2 = "#2a78d6", "#eb6834"                          # categorical slots 1 and 2


def measure_c_paths(name, beta=7.14, years=10):
    from scipy.optimize import brentq
    mk = P.CGE9(calib="pwt", households="groups", labour="wage_curve", public_capital=PUBLIC_CAPITAL[name], beta_w=beta)
    s0 = mk.steady()[0]

    def emp26(size):
        _, a, _ = B.run(mk, s0, dIG=lambda r: r.__setitem__((0, 0), -size * mk.GDP0))
        return float(np.average(a["employment"][:, 0] - 1, weights=mk.L0.sum(1))) * 100 - B.LABOUR_2026
    size = brentq(emp26, 0.0, 0.25, xtol=1e-6)
    dig = B.C_BN / B.GDP_2027 * mk.GDP0
    short = lambda r: r.__setitem__((0, 0), -size * mk.GDP0)
    Yb, base, _ = B.run(mk, s0, dIG=short)
    _, ann, _ = B.run(mk, s0, dIG=lambda r: (short(r), r.__setitem__((0, 1), r[0, 1] + dig)))
    X2 = mk.path(B.T, sr=lambda r: r.__setitem__((0, slice(0, 1)), 1.0), dIG=lambda r: r.__setitem__((0, 0), dig))
    Y2, y02, _, _ = mk.run(X2, y_start=Yb[:, 0])
    a2 = mk.accounts(Y2, Yb[:, 0], X2)
    sur = np.concatenate([[base["real_gdp"][0]], a2["real_gdp"][:-1]])
    pa = (ann["real_gdp"][:years] / base["real_gdp"][:years] - 1) * 100
    ps = (sur[:years] / base["real_gdp"][:years] - 1) * 100
    return pa, ps


def style(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=9)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    out = ROOT / "outputs" / f"figures_item37_{datetime.now():%Y%m%d_%H%M}"
    out.mkdir(parents=True, exist_ok=True)
    years = np.arange(2026, 2036)
    # ---- figure 1
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), sharey=True, facecolor=SURFACE)
    paths = {name: measure_c_paths(name) for name in ("low", "high")}
    every = np.concatenate([p for pair in paths.values() for p in pair])
    gap = 0.07 * (every.max() - min(every.min(), 0.0))     # keep the end labels apart (the panels share one y-axis)
    for ax, name in zip(axes, ("low", "high")):
        pa, ps = paths[name]
        style(ax)
        ax.axhline(0, color=INK2, linewidth=0.8)
        ax.plot(years, pa, color=S1, linewidth=2, label="announced in 2026")
        ax.plot(years, ps, color=S2, linewidth=2, label="surprise in 2027")
        top, bot = max(pa[-1], ps[-1]), min(pa[-1], ps[-1])
        mid = (top + bot) / 2
        top, bot = max(top, mid + gap / 2), min(bot, mid - gap / 2)
        ya, ys = (top, bot) if pa[-1] >= ps[-1] else (bot, top)
        ax.text(years[-1] + 0.15, ya, "announced", color=INK, fontsize=9, va="center")
        ax.text(years[-1] + 0.15, ys, "surprise", color=INK, fontsize=9, va="center")
        ax.set_xlim(2025.6, 2037.6)
        ax.set_xticks(years[::2])
        ax.set_title(f"Public capital '{name}'", color=INK, fontsize=11, loc="left")
        print(name, "announced", np.round(pa, 3), "surprise", np.round(ps, 3))
    axes[0].set_ylabel("Real GDP vs the 2026-27 shortfall path (%)", color=INK2, fontsize=9)
    axes[0].legend(frameon=False, fontsize=9, labelcolor=INK, loc="upper left")
    fig.suptitle("Measure C (₱208.7 bn of public works in 2027): announced vs surprise, Keynesian short run", color=INK, fontsize=12, x=0.01, ha="left")
    fig.text(0.01, 0.01, "Forward-looking CGE, research code, not for citation. Source: Infinity GEM 0.3, research/intertemporal (Build 2).",
             color=INK2, fontsize=8)
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    f1 = out / "fig1_measure_C_announced_vs_surprise.png"
    fig.savefig(f1, dpi=150, facecolor=SURFACE)
    plt.close(fig)
    # ---- figure 2
    m = P.CGE9(calib="pwt", households="groups")
    X, Y, y0, info = m.bridge_baseline(200)
    b = m.split(Y)["b"]
    g0 = m.GDP0
    lag = np.concatenate([[0.0], b[:-1]])
    bop = info["sustainable"] / g0 * 100 + (lag / (1 + m.g) - b) / g0 * 100
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4.2), facecolor=SURFACE)
    style(a1)
    yy = np.arange(2023, 2033)
    imf_y = sorted(P.IMF_CA)
    a1.plot(yy, bop[:10], color=S1, linewidth=2, label="model")
    a1.plot(imf_y, [-P.IMF_CA[k] for k in imf_y], color=S2, linewidth=2, marker="o", markersize=8,
            markeredgecolor=SURFACE, markeredgewidth=2, label="IMF CR 25/333")
    a1.set_ylim(0, max(bop[:10].max(), 4.2) * 1.15)
    a1.set_title("Current-account deficit (% of GDP)", color=INK, fontsize=11, loc="left")
    a1.legend(frameon=False, fontsize=9, labelcolor=INK)
    style(a2)
    yl = np.arange(2023, 2073)
    a2.axhline(0, color=INK2, linewidth=0.8)
    a2.plot(yl, b[:50] / g0 * 100, color=S1, linewidth=2)
    k = int(np.argmin(b[:50]))
    a2.annotate(f"lowest {b[k] / g0 * 100:.1f}% ({2023 + k})", xy=(2023 + k, b[k] / g0 * 100), xytext=(2023 + k + 6, b[k] / g0 * 100 - 0.5),
                color=INK, fontsize=9, arrowprops=dict(arrowstyle="-", color=INK2, linewidth=0.8))
    a2.set_title("Foreign assets beyond the stable-NIIP path (% of GDP)", color=INK, fontsize=11, loc="left")
    fig.suptitle("Foreign-saving bridge: the SAM's ₱516 bn excess of foreign saving, borrowed in 2023 and repaid", color=INK, fontsize=12, x=0.01, ha="left")
    fig.text(0.01, 0.01, "Forward-looking CGE, research code, not for citation. Source: Infinity GEM 0.3, research/intertemporal (Build 1); IMF Country Report 25/333, Table 5.",
             color=INK2, fontsize=8)
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    f2 = out / "fig2_item74_bridge_base_path.png"
    fig.savefig(f2, dpi=150, facecolor=SURFACE)
    plt.close(fig)
    print("wrote", f1, "and", f2)


if __name__ == "__main__":
    main()
