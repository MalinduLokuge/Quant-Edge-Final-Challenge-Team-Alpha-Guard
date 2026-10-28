"""Required return for the endowment (decision D12).

(1 + R_req) = (1 + I)(1 + S)(1 + G)(1 + C)
    I = expected inflation (FRED breakeven), S = spending rate, G = real growth target,
    C = investment costs NOT already inside ETF prices (expense ratios are already deducted).
Multiplicative (CFA convention); the additive sum I + S + G + C slightly understates it.
"""
from __future__ import annotations

import itertools

import pandas as pd


def required_return(inflation: float, spending: float, real_growth: float, costs: float = 0.0) -> float:
    return (1 + inflation) * (1 + spending) * (1 + real_growth) * (1 + costs) - 1


def required_return_grid(inflation: float, spending: list[float], real_growth: list[float], costs: list[float]) -> pd.DataFrame:
    """Required gross return for every combination of the uncertain inputs."""
    rows = [{"inflation": inflation, "spending": s, "real_growth": g, "costs": c,
             "required_net_of_costs": required_return(inflation, s, g),
             "required_gross": required_return(inflation, s, g, c),
             "additive_approx": inflation + s + g + c}
            for s, g, c in itertools.product(spending, real_growth, costs)]
    return pd.DataFrame(rows)


def sustainable_spending(expected_return: float, inflation: float, real_growth: float, costs: float) -> float:
    """Highest spending rate the portfolio can support while still meeting inflation, real growth and costs.

    Solves (1 + E) = (1 + I)(1 + S)(1 + G)(1 + C) for S. Negative means even zero spending falls short.
    """
    return (1 + expected_return) / ((1 + inflation) * (1 + real_growth) * (1 + costs)) - 1


def feasibility(expected: pd.DataFrame, required_gross: float) -> pd.DataFrame:
    """Compare expected compound (geometric) return with the required gross return.

    `expected` needs a column 'expected_geometric'. Gap > 0 means the portfolio is expected to fall short.
    """
    out = expected.copy()
    out["required_gross"] = required_gross
    out["gap"] = required_gross - out["expected_geometric"]
    out["meets_requirement"] = out["gap"] <= 0
    return out


def required_return_as_of(rates: pd.DataFrame, as_of, mandate: dict) -> dict:
    """Required return using the inflation expectation known on `as_of` (T4.23).

    Spending, real growth and costs are the approved D12 policy values (they are client policy, not market
    data); only expected inflation is taken from the market on that date. Train set: as_of = D5 train end.
    """
    r = rates.loc[:pd.Timestamp(as_of), mandate["inflation_series"]].dropna()
    if r.empty:
        raise ValueError(f"No inflation data on or before {pd.Timestamp(as_of).date()}")
    inflation = float(r.iloc[-1]) / 100
    s, g, c = (mandate[k]["base"] for k in ("spending_rate", "real_growth", "extra_costs"))
    return {"as_of": r.index[-1], "inflation": inflation,
            "required_gross": required_return(inflation, s, g, c),
            "required_minimum": required_return(inflation, s, 0.0, c)}
