"""Shapley decomposition of a combined-shock result into the contribution of each shock (0.3.5,
15 Oct 2026).

Why: with several shocks run together, a non-linear model (a CGE, and above all a poverty count) does not give results that
add up shock by shock. The Shapley value averages each shock's marginal effect over every order in which the shocks could
be added, so the contributions add up EXACTLY to the combined result (Shorrocks 2013, Journal of Economic Inequality; to
verify). Used for waterfall charts.

    from infinity_gem.decompose import shapley
    contrib = shapley(outcome, shocks)     # outcome: frozenset of shock names -> number (0 for the empty set)

For n shocks it needs all 2^n subsets (5 shocks: 32 model runs). Checks: SH1 (additivity; symmetry on a known function).
"""
from __future__ import annotations

import itertools
from math import factorial
from typing import Callable, Iterable

import pandas as pd


def shapley(outcome: Callable[[frozenset], float], shocks: Iterable[str]) -> pd.Series:
    """Shapley contribution of each shock to outcome(all shocks) - outcome(none). outcome is evaluated once per subset."""
    shocks = list(shocks)
    n = len(shocks)
    cache = {}
    val = lambda s: cache.setdefault(s, outcome(s))
    phi = {}
    for i in shocks:
        others = [s for s in shocks if s != i]
        tot = 0.0
        for r in range(n):
            w = factorial(r) * factorial(n - r - 1) / factorial(n)
            for sub in itertools.combinations(others, r):
                S = frozenset(sub)
                tot += w * (val(S | {i}) - val(S))
        phi[i] = tot
    out = pd.Series(phi)
    out.attrs["total"] = val(frozenset(shocks)) - val(frozenset())
    out.attrs["evaluations"] = len(cache)
    return out
