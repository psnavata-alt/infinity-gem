"""Milestone 30 prep (12 Nov 2026): the long-sample local-projection oil-supply responses (2002Q1-2025Q4, COVID dropped), year-1
and year-2 averages per 10% impact rise in Dubai, point and s.e., to full precision, for the opt-in oil system prior in
estimate_rot.py (oilprior=lp). Same computation as compare_oil_lp.py's data side. NOT FOR CITATION.
Run (research/dsge):  py -I -X utf8 milestone28_scratch/oil_lp_targets.py
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import oil_supply_lp as LP  # noqa: E402

OBJ = ["real GDP", "real exports", "CPI", "PHP per USD", "policy rate"]


def targets():
    df = LP.data()
    shk = LP.shock_q("Monthly")
    res = {v: LP.lp(df, shk, v, "2002Q1", "2025Q4", LP.ph_data.COVID) for v in OBJ + ["Dubai crude (USD)"]}
    sc = 10.0 / res["Dubai crude (USD)"][0, 0]
    return {(o, y + 1): (float(sc * res[o][4 * y:4 * y + 4, 0].mean()), float(sc * res[o][4 * y:4 * y + 4, 1].mean()))
            for o in OBJ for y in (0, 1)}


if __name__ == "__main__":
    for k, (m, s) in targets().items():
        print(f"    {k!r}: ({m:.6f}, {s:.6f}),")
