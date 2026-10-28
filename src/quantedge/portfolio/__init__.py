"""Portfolio stage. Implemented so far: return objective and capital market assumptions (D12).

Outputs (outputs/tables/):
    cma_assets.csv              per ETF: beta, historical means, volatility, TTM yield, CAPM E[R] per ERP
    erp_estimate.csv            own-data equity risk premium with 95% CI
    required_return_grid.csv    required return for every spending / growth / cost combination
    required_vs_expected.csv    reference portfolios: expected compound return vs required (per ERP), sustainable spending
Outputs (outputs/reports/):
    return_objective_summary.md one-page summary for the team / committee (regenerated on every run)

Uses the full sample up to the as-of date: these are forward-looking assumptions for today's
decision, not inputs to the out-of-sample backtest (which must use the training window only).
"""
from __future__ import annotations

import pandas as pd

from quantedge.common import config
from quantedge.common import conventions as cv
from quantedge.portfolio import cma, return_objective, summary


def run() -> dict:
    s = config.load_settings()
    m, c = s["mandate"], s["cma"]
    simple = pd.read_csv(config.DATA_PROCESSED / "simple_returns.csv", index_col=0, parse_dates=True)
    rates = pd.read_csv(config.DATA_PROCESSED / "rates_daily.csv", index_col=0, parse_dates=True)
    yields = pd.read_csv(config.DATA_PROCESSED / "distribution_yield_ttm.csv", index_col=0, parse_dates=True)

    as_of = simple.index[-1]
    rf_now = rates.loc[as_of, "dtb3_pct"] / 100
    inflation = rates.loc[as_of, m["inflation_series"]] / 100
    yld = yields.loc[as_of]

    mex = cma.monthly_excess_returns(simple, rates["rf_daily"])
    betas = cma.capm_betas(mex, c["market"])
    erp = cma.equity_risk_premium(mex[c["market"]])
    cov = cma.annual_covariance(simple)

    assets = cma.historical_stats(simple).join(betas)
    assets["ttm_yield"] = yld
    erps = {f"{e:.0%}": e for e in c["erp_range"]} | {"own data": erp["erp_arithmetic"]}
    for label, e in erps.items():
        assets[f"capm_E[R] erp {label}"] = cma.capm_expected(rf_now, betas, e)

    grid = return_objective.required_return_grid(
        inflation, m["spending_rate"]["range"], m["real_growth"]["range"], m["extra_costs"]["range"])
    req_base = return_objective.required_return(
        inflation, m["spending_rate"]["base"], m["real_growth"]["base"], m["extra_costs"]["base"])

    rows = []
    for name, w in c["reference_portfolios"].items():
        w = cv.validate_weights(pd.Series(w), s["universe"])
        for label, e in erps.items():
            for wht in (0.0, m["withholding_tax_rate"]):
                exp = cma.portfolio_expected(w, cma.capm_expected(rf_now, betas, e), cov, yld, wht)
                rows.append({"portfolio": name, "erp": label, "withholding_tax": wht, **exp})
    vs = return_objective.feasibility(pd.DataFrame(rows), req_base)
    vs["sustainable_spending"] = vs["expected_geometric"].apply(
        lambda e: return_objective.sustainable_spending(e, inflation, m["real_growth"]["base"], m["extra_costs"]["base"]))

    out = config.OUTPUT_TABLES
    out.mkdir(parents=True, exist_ok=True)
    assets.to_csv(out / "cma_assets.csv")
    pd.Series(erp | {"rf_now": rf_now, "inflation_breakeven_10y": inflation, "as_of": as_of.date()}).to_csv(
        out / "erp_estimate.csv", header=["value"])
    grid.to_csv(out / "required_return_grid.csv", index=False)
    vs.to_csv(out / "required_vs_expected.csv", index=False)
    summary.write_return_objective_summary(
        config.OUTPUT_REPORTS / "return_objective_summary.md", as_of=as_of.date(), inflation=inflation, rf=rf_now,
        mandate=m, erp_base=c["erp_base"], erp_own=erp, grid=grid, vs=vs, assets=assets)
    print(f"[portfolio] as of {as_of.date()}: required return (base) {req_base:.2%}, "
          f"own-data ERP {erp['erp_arithmetic']:.2%}, rf {rf_now:.2%}, breakeven {inflation:.2%}")
    return {"assets": assets, "erp": erp, "grid": grid, "required_vs_expected": vs, "required_base": req_base}
