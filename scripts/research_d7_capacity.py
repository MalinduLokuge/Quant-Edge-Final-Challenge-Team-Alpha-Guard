"""Risk tolerance and risk capacity evidence for D7 (12-factor review, T3.21–T3.27).

    python scripts/research_d7_capacity.py     (needs run_all.py data + portfolio stages first)

Writes outputs/tables/research_capacity_*.csv. Paths: moving-block bootstrap (63-day blocks) of daily ETF
returns with each ETF's mean reset to its CAPM expectation (ERP 5%), as in research_d3_d7.py.
Spending is withdrawn quarterly. Inflation = 10-year breakeven on the as-of date.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from quantedge.common import config  # noqa: E402
from quantedge.common import conventions as cv  # noqa: E402
from quantedge.validation.sustainability import bootstrap, recovery_times, spending_paths  # noqa: E402,F401

ERP = 0.05
Q = 63  # trading days per quarter
PORTFOLIOS = {  # global equity mix SPY/EFA/EEM 62.5/25/12.5, GLD 10%, rest AGG (sweep A), plus references
    "Equity 20%": .20, "Equity 30%": .30, "Equity 40% (= policy benchmark)": .40, "Equity 45% (D6 max)": .45,
    "Equity 60% (~60/40 risk)": .60,
}


def weights(eq: float) -> pd.Series:
    return pd.Series({"SPY": .625 * eq, "EFA": .25 * eq, "EEM": .125 * eq, "GLD": .10, "AGG": .90 - eq})


def main() -> None:
    s = config.load_settings()
    simple = pd.read_csv(config.DATA_PROCESSED / "simple_returns.csv", index_col=0, parse_dates=True)
    rates = pd.read_csv(config.DATA_PROCESSED / "rates_daily.csv", index_col=0, parse_dates=True)
    assets = pd.read_csv(config.OUTPUT_TABLES / "cma_assets.csv", index_col=0)
    tick = list(simple.columns)
    infl = rates["breakeven_10y_pct"].iloc[-1] / 100
    s0 = s["mandate"]["spending_rate"]["base"]
    mu = assets.loc[tick, f"E[R] erp {ERP:.0%}"].to_numpy()
    R = simple.to_numpy() + (mu / cv.TRADING_DAYS - simple.mean().to_numpy())
    out = config.OUTPUT_TABLES
    idx5, idx10 = bootstrap(R, 4_000, 5 * 252, seed=21), bootstrap(R, 2_000, 10 * 252, seed=22)

    # 1. Capacity with spending (5 years, D4)
    rows = []
    for name, eq in PORTFOLIOS.items():
        P = R[idx5] @ weights(eq).reindex(tick, fill_value=0.0).to_numpy()
        for spend in (s0, 0.03):
            for rule in ("fixed_real", "pct_nav", "smoothed"):
                r = spending_paths(P, rule, spend, infl)
                rows.append({"portfolio": name, "spending": spend, "rule": rule,
                             "median_real_nav_5y": np.median(r["real_nav_end"]),
                             "P(real NAV < 90% at end)": (r["real_nav_end"] < .90).mean(),
                             "P(real NAV ever < 80%)": (r["real_nav_min"] < .80).mean(),
                             "P(real NAV ever < 75%)": (r["real_nav_min"] < .75).mean(),
                             "P(effective spending ever > 5%)": (r["max_effective_rate"] > .05).mean(),
                             "P(real spending ever cut > 10%)": (r["real_spending_min"] < .90).mean()})
    pd.DataFrame(rows).to_csv(out / "research_capacity_spending.csv", index=False)

    # 2. Analytic capacity: loss d at which fixed-dollar spending s0 becomes rate s_max: d* = 1 - s0/s_max
    pd.DataFrame([{"spending": sp, "max_rate": mx, "capacity_drawdown": 1 - sp / mx}
                  for sp in (0.03, 0.035, 0.04) for mx in (0.05, 0.055, 0.06)]).to_csv(
        out / "research_capacity_analytic.csv", index=False)

    # 3. Recovery times: forward (10-year paths, no spending) and historical
    rec = []
    for name, eq in PORTFOLIOS.items():
        P = R[idx10] @ weights(eq).reindex(tick, fill_value=0.0).to_numpy()
        for lvl, v in recovery_times(P).items():
            rec.append({"portfolio": name, "drawdown": lvl, **v})
    for name, eq in PORTFOLIOS.items():
        rp, _ = cv.rebalanced_returns(simple, weights(eq), "quarterly")
        for lvl, v in recovery_times(rp.to_numpy()[None, :]).items():
            rec.append({"portfolio": name + " [historical]", "drawdown": lvl, **v})
    pd.DataFrame(rec).to_csv(out / "research_capacity_recovery.csv", index=False)

    # 4. Liquidity: funding one year of spending from AGG in stress
    agg = simple["AGG"]
    nav0, spend = s["portfolio_value_usd"], s0 * s["portfolio_value_usd"]
    liq = {"annual_spending_usd": spend,
           "AGG_holding_policy_usd": 0.50 * nav0, "years_of_spending_in_AGG": 0.50 / s0,
           "AGG_worst_day": agg.min(), "AGG_worst_day_date": agg.idxmin().date(),
           "cost_if_full_year_sold_on_worst_day_usd": spend * -agg.min(),
           "AGG_return_GFC_window": (1 + agg.loc["2007-10-09":"2009-03-09"]).prod() - 1,
           "AGG_max_drawdown": cv.drawdown(agg).min()}
    pd.Series(liq).to_csv(out / "research_capacity_liquidity.csv", header=["value"])

    # 5. Losses beyond history: crisis replays scaled by severity
    crises = {"GFC": ("2007-10-09", "2009-03-09"), "COVID": ("2020-02-19", "2020-03-23"), "2022": ("2022-01-03", "2022-10-12")}
    sev = []
    for name, eq in PORTFOLIOS.items():
        w = weights(eq)
        for c, (a, b) in crises.items():
            base = float((1 + (simple.loc[a:b, w.index] * w).sum(axis=1)).prod() - 1)
            for k in (1.0, 1.25, 1.5):
                scaled = float((1 + k * (simple.loc[a:b, w.index] * w).sum(axis=1)).prod() - 1)
                sev.append({"portfolio": name, "crisis": c, "severity": k, "loss": scaled, "loss_1x": base})
    pd.DataFrame(sev).to_csv(out / "research_capacity_severe.csv", index=False)
    print("capacity research written")


if __name__ == "__main__":
    main()
