"""Joint ranges, figure (20 Oct 2026, about 00:35): the distribution of the 2026 results (20 Oct 2026) across the Latin-hypercube
draws of scenarios/lhs_2026_ranges.py, with the central case and the range stated with the 2026 scenarios (new poor 3.1-3.4 M).
Research output, NOT FOR CITATION.
Run:  INFINITY_GEM_SCENARIO_SAM=own  py scenarios/lhs_2026_ranges_figure.py      (writes outputs/lhs_2026_ranges_figure_<stamp>_own.png)
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt   # noqa: E402
import numpy as np                # noqa: E402
import pandas as pd               # noqa: E402

import _common                    # noqa: E402
from infinity_gem import paths        # noqa: E402

PANELS = (("new poor 2026 (M, own baskets)", "New poor, 2026 (million)", (3.1, 3.4)),
          ("GDP gap 2026 (%)", "GDP, 2026 (% against the no-shock path)", None),
          ("cumulative GDP loss 2025-2030 (₱ bn)", "Output lost 2025-2030 (₱ billion)", None))


def main():
    t = pd.read_csv(paths.output_dir() / f"lhs_2026_ranges_draws{_common.sam_tag()}.csv", index_col=0).sort_index()
    c, s = t.iloc[0], t.iloc[1:].dropna(subset=[p[0] for p in PANELS])
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.6))
    for ax, (col, title, stated) in zip(axes, PANELS):
        ax.hist(s[col], bins=15, color="#9fb7d9", edgecolor="white")
        lo, hi = np.percentile(s[col], [5, 95])
        ax.axvspan(lo, hi, color="#2a78d6", alpha=0.12, label=f"90% of draws: {lo:,.2f} to {hi:,.2f}")
        ax.axvline(c[col], color="#e34948", lw=2, label=f"central case: {c[col]:,.2f}")
        if stated:
            ax.axvline(stated[0], color="#555", ls="--", lw=1)
            ax.axvline(stated[1], color="#555", ls="--", lw=1, label=f"stated range: {stated[0]}-{stated[1]}")
        ax.set_title(title, fontsize=10)
        ax.legend(fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=1, frameon=False)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle(f"The central 2026 setting (20 Oct 2026) under joint parameter uncertainty: {len(s)} Latin-hypercube draws (research, not for citation)",
                 fontsize=11)
    fig.tight_layout()
    f = paths.output_dir() / f"lhs_2026_ranges_figure_{pd.Timestamp.today():%Y%m%d_%H%M}{_common.sam_tag()}.png"
    fig.savefig(f, dpi=150)
    print("saved", f)


if __name__ == "__main__":
    main()
