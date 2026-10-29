"""Portfolio stage. Implemented so far: return objective and capital market assumptions (D12).

Outputs (outputs/tables/):
    cma_assets.csv              per ETF: beta, historical means, volatility, TTM yield, CAPM E[R] per ERP
    erp_estimate.csv            own-data equity risk premium with 95% CI
    required_return_grid.csv    required return for every spending / growth / cost combination
    required_vs_expected.csv    reference portfolios: expected compound return vs required (per ERP), sustainable spending
    p1_train_weights.csv / p1_final_weights.csv (+ _diagnostics)  P1 candidates: min-variance, risk parity,
                                max-Sharpe, min-CVaR, target-return, + max-expected-return frontier end
    frontier_full.csv           9-point frontier within D6 + D7: return, drawdown, ES, P(DD>25%), spending (T4.11)
    ../figures/frontier_full.png
    cma_train.csv / cma_full.csv (+ _cov, _cov_shrunk)  optimiser inputs as of the D5 train end / last date
                                (T4.18); _cov_shrunk = Ledoit–Wolf on correlations (T4.08), used by the optimiser
Outputs (outputs/reports/):
    return_objective_summary.md one-page summary for the team / committee (regenerated on every run)

Uses the full sample up to the as-of date: these are forward-looking assumptions for today's
decision, not inputs to the out-of-sample backtest (which must use the training window only).
"""
from __future__ import annotations

import pandas as pd

from quantedge.common import config
from quantedge.common import conventions as cv
from quantedge.portfolio import candidates, cma, frontier, return_objective, summary


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
    assets["volatility_monthly"] = cma.annual_covariance(simple, "monthly").pipe(lambda m_: pd.Series(
        m_.values.diagonal() ** 0.5, index=m_.index))  # reported only; models use daily (warning 5)
    erps = {f"{e:.0%}": e for e in c["erp_range"]} | {"own data": erp["erp_arithmetic"]}
    bonds = tuple(c.get("bond_assets", ()))
    for label, e in erps.items():
        assets[f"capm_E[R] erp {label}"] = cma.capm_expected(rf_now, betas, e)                      # pure CAPM (reference)
        assets[f"E[R] erp {label}"] = cma.expected_returns(assets[f"capm_E[R] erp {label}"], yld, bonds)  # D25, used

    grid = return_objective.required_return_grid(
        inflation, m["spending_rate"]["range"], m["real_growth"]["range"], m["extra_costs"]["range"])
    req_base = return_objective.required_return(
        inflation, m["spending_rate"]["base"], m["real_growth"]["base"], m["extra_costs"]["base"])

    rf_scen = {k: (rf_now if v == "as_of" else float(v)) for k, v in c["rf_scenarios"].items()}
    tax_cases = {"tax-exempt (base)": 0.0} | {k: pd.Series(v) for k, v in m["withholding_tax"]["cases"].items()}
    rows = []
    for name, w in c["reference_portfolios"].items():
        w = cv.validate_weights(pd.Series(w), s["universe"])
        for rf_label, rf in rf_scen.items():
            for label, e in erps.items():
                for tax_label, tax in tax_cases.items():
                    exp_r = cma.expected_returns(cma.capm_expected(rf, betas, e), yld, bonds)  # AGG yield is locked in
                    exp = cma.portfolio_expected(w, exp_r, cov, yld, tax)
                    rows.append({"portfolio": name, "rf_scenario": rf_label, "rf": rf, "erp": label,
                                 "tax_case": tax_label, **exp})
    vs = return_objective.feasibility(pd.DataFrame(rows), req_base)
    vs["sustainable_spending"] = vs["expected_geometric"].apply(
        lambda e: return_objective.sustainable_spending(e, inflation, m["real_growth"]["base"], m["extra_costs"]["base"]))

    out = config.OUTPUT_TABLES
    out.mkdir(parents=True, exist_ok=True)
    assets.to_csv(out / "cma_assets.csv")

    # T4.18: two CMA sets for the optimiser. "train" sees only data up to the D5 train end (P1-train,
    # out-of-sample tests); "full" sees everything (P1-final). Same method and ERP for both.
    cma_sets = {}
    for label, as_of_date in (("train", s["split"]["train_end"]), ("full", as_of)):
        est = cma.estimate_as_of(simple, rates, yields, as_of_date, c["market"], c["erp_base"], bond_assets=bonds)
        est["hurdle"] = return_objective.required_return_as_of(rates, as_of_date, m)  # T4.23: same-date inflation
        est["assets"].to_csv(out / f"cma_{label}.csv")
        est["cov"].to_csv(out / f"cma_{label}_cov.csv")
        est["cov_shrunk"].to_csv(out / f"cma_{label}_cov_shrunk.csv")  # T4.08: optimiser input
        cma_sets[label] = est
    pd.DataFrame({k: {"as_of": v["as_of"].date(), "rf": v["rf"], "erp_assumed": v["erp"],
                      "erp_own_data_window": v["erp_own_data"], "observations": v["observations"],
                      "covariance_shrinkage": v["shrinkage"],
                      "inflation_breakeven": v["hurdle"]["inflation"], "required_target": v["hurdle"]["required_gross"],
                      "required_minimum": v["hurdle"]["required_minimum"]}
                  for k, v in cma_sets.items()}).to_csv(out / "cma_sets_summary.csv")
    pd.Series(erp | {"rf_now": rf_now, "inflation_breakeven_10y": inflation, "as_of": as_of.date()}).to_csv(
        out / "erp_estimate.csv", header=["value"])
    grid.to_csv(out / "required_return_grid.csv", index=False)
    vs.to_csv(out / "required_vs_expected.csv", index=False)
    p1 = candidates.run(simple, s)  # T4.02–T4.10, T4.16, T4.19: P1-train and P1-final (D6 v2 + D7, D22)
    front = frontier.build(simple, s, "full")  # T4.11: trade-off table for D26 and the memo
    front.to_csv(out / "frontier_full.csv")
    fig_dir = config.ROOT / "outputs" / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    frontier.plot(front, p1["full"][1], fig_dir / "frontier_full.png")

    summary.write_return_objective_summary(
        config.OUTPUT_REPORTS / "return_objective_summary.md", as_of=as_of.date(), inflation=inflation, rf=rf_now,
        mandate=m, erp_base=c["erp_base"], erp_own=erp, grid=grid, vs=vs, assets=assets)
    print(f"[portfolio] as of {as_of.date()}: required return (base) {req_base:.2%}, "
          f"own-data ERP {erp['erp_arithmetic']:.2%}, rf {rf_now:.2%}, breakeven {inflation:.2%}")
    return {"assets": assets, "erp": erp, "grid": grid, "required_vs_expected": vs, "required_base": req_base,
            "cma_sets": cma_sets, "p1": p1, "frontier": front}
