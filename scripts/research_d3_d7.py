"""Evidence for D3 (benchmarks) and D7 (risk limits). In-sample historical analysis, 2004-11 to 2026-10.

    python scripts/research_d3_d7.py      (needs `python run_all.py --only data` and `--only portfolio` first)

Writes outputs/tables/research_d3d7_*.csv. Historical figures describe what DID happen; they are not
forecasts or guarantees, and the full sample includes the 2008 crisis (in-sample for any portfolio).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from quantedge.common import config  # noqa: E402
from quantedge.common import conventions as cv  # noqa: E402
from quantedge.portfolio import cma  # noqa: E402

ERP = 0.05
REQUIRED = {"minimum": 0.0666, "target": 0.0719}
CRISES = {"GFC 2007-10-09..2009-03-09": ("2007-10-09", "2009-03-09"),
          "COVID 2020-02-19..2020-03-23": ("2020-02-19", "2020-03-23"),
          "Rates 2022-01-03..2022-10-12": ("2022-01-03", "2022-10-12"),
          "FY2009 (NACUBO year) 2008-07-01..2009-06-30": ("2008-07-01", "2009-06-30")}
BENCHMARKS = {
    "60/40 SPY/AGG": {"SPY": 0.60, "AGG": 0.40},
    "40/60 SPY/AGG": {"SPY": 0.40, "AGG": 0.60},
    "Global 60/40 (SPY/EFA/EEM + AGG)": {"SPY": 0.37, "EFA": 0.16, "EEM": 0.07, "AGG": 0.40},
    "Global 40/60": {"SPY": 0.25, "EFA": 0.11, "EEM": 0.04, "AGG": 0.60},
    "Policy 40/50/10 (global eq/AGG/GLD)": {"SPY": 0.25, "EFA": 0.10, "EEM": 0.05, "AGG": 0.50, "GLD": 0.10},
    "Equal weight 7": {t: 1 / 7 for t in ["SPY", "EFA", "EEM", "AGG", "GLD", "XLE", "XLK"]},
    "SPY (CAPM market)": {"SPY": 1.0},
}


def rebalanced(simple: pd.DataFrame, w: pd.Series) -> tuple[pd.Series, float]:
    """Quarterly-rebalanced returns and turnover, via the shared convention (D11, T2.17)."""
    return cv.rebalanced_returns(simple, w, "quarterly")


def capped_samples(rng: np.random.Generator, tick: list[str], n: int) -> np.ndarray:
    """Random weights inside the draft D6 caps: each ETF <= 40%, AGG+GLD >= 40%, EEM/XLE/XLK each <= 10%
    and together <= 25%. Uniform-ish sampling per block (unconstrained Dirichlet rarely lands here)."""
    i = {t: tick.index(t) for t in tick}
    out = []
    while len(out) < n:
        d = rng.uniform(0.40, 0.80)
        a = rng.uniform(max(0, d - 0.4), min(0.4, d))
        sat = rng.uniform(0, min(0.25, 1 - d)) * rng.dirichlet(np.ones(3))
        rem = 1 - d - sat.sum()
        if rem > 0.8 or sat.max() > 0.10:
            continue
        spy = rng.uniform(max(0, rem - 0.4), min(0.4, rem))
        w = np.zeros(len(tick))
        w[[i["AGG"], i["GLD"], i["SPY"], i["EFA"]]] = a, d - a, spy, rem - spy
        w[[i["EEM"], i["XLE"], i["XLK"]]] = sat
        out.append(w)
    return np.array(out)


def es(x: np.ndarray, a: float = 0.99) -> float:
    loss = -x
    var = np.quantile(loss, a)
    return float(loss[loss >= var].mean())


def kpis(rp: pd.Series, rf: pd.Series, spy: pd.Series, ref: pd.Series) -> dict:
    ex = rp - rf
    downside = np.sqrt((np.minimum(ex, 0) ** 2).mean() * cv.TRADING_DAYS)
    dd = cv.drawdown(rp)
    trough = dd.idxmin()
    peak = cv.wealth_index(rp).loc[:trough].idxmax()
    after = dd.loc[trough:]
    rec = after[after >= 0]
    m = (1 + rp).resample(cv.MONTH_END).prod() - 1
    ms = (1 + spy).resample(cv.MONTH_END).prod() - 1
    roll12 = (1 + rp).rolling(252).apply(np.prod, raw=True) - 1
    cagr = cv.annualised_return(rp)
    return {
        "CAGR": cagr, "volatility": cv.annualised_volatility(rp),
        "Sharpe": ex.mean() * 252 / (rp.std() * np.sqrt(252)), "Sortino": ex.mean() * 252 / downside,
        "max_drawdown": dd.min(), "dd_peak": peak.date(), "dd_trough": trough.date(),
        "recovery_days": (rec.index[0] - trough).days if len(rec) else None,
        "Calmar": cagr / abs(dd.min()),
        "VaR99_1d": -np.quantile(rp, 0.01), "ES99_1d": es(rp.to_numpy()), "ES975_1d": es(rp.to_numpy(), 0.975),
        "worst_month": m.min(), "worst_12m": roll12.min(), "share_12m_below_-10%": (roll12 < -0.10).mean(),
        "beta_monthly_vs_SPY": m.cov(ms) / ms.var(),
        "tracking_error_vs_60/40": (rp - ref).std() * np.sqrt(252),
    }


def main() -> None:
    s = config.load_settings()
    simple = pd.read_csv(config.DATA_PROCESSED / "simple_returns.csv", index_col=0, parse_dates=True)
    rates = pd.read_csv(config.DATA_PROCESSED / "rates_daily.csv", index_col=0, parse_dates=True)
    rf = rates["rf_daily"].reindex(simple.index)
    assets = pd.read_csv(config.OUTPUT_TABLES / "cma_assets.csv", index_col=0)
    capm = assets[f"capm_E[R] erp {ERP:.0%}"]
    cov = cma.annual_covariance(simple)
    yld = assets["ttm_yield"]
    ref, _ = rebalanced(simple, pd.Series(BENCHMARKS["60/40 SPY/AGG"]))
    out = config.OUTPUT_TABLES

    # 1. Benchmark comparison (quarterly rebalanced)
    rows, crisis, rolling = {}, {}, {}
    for name, w in BENCHMARKS.items():
        w = cv.validate_weights(pd.Series(w), s["universe"])
        w = w[w > 0]
        rp, turn = rebalanced(simple, w)
        k = kpis(rp, rf, simple["SPY"], ref)
        k["turnover_pa"] = turn
        k["expected_geo_capm_erp5"] = cma.portfolio_expected(w, capm, cov, yld)["expected_geometric"]
        rows[name] = k
        crisis[name] = {c: float((1 + rp.loc[a:b]).prod() - 1) for c, (a, b) in CRISES.items()}
        r_es = rp.rolling(250).apply(lambda x: es(x), raw=True).dropna()
        rolling[name] = {"min": r_es.min(), "median": r_es.median(), "max": r_es.max(),
                         "share_days_above_2.5%": (r_es > 0.025).mean(), "share_days_above_2.0%": (r_es > 0.02).mean()}
    pd.DataFrame(rows).T.to_csv(out / "research_d3d7_benchmarks.csv")
    pd.DataFrame(crisis).T.to_csv(out / "research_d3d7_crisis_losses.csv")
    pd.DataFrame(rolling).T.to_csv(out / "research_d3d7_rolling_es99_250d.csv")

    # 2. Feasibility: random long-only portfolios (daily rebalanced), historical MDD / ES99 vs CAPM expected return
    rng = np.random.default_rng(42)
    tick = list(simple.columns)
    W = np.vstack([rng.dirichlet(np.full(len(tick), a), size=10_000) for a in (0.3, 1.0, 3.0)]
                  + [np.eye(len(tick)), capped_samples(rng, tick, 20_000)])
    R = simple[tick].to_numpy()
    mdd, es99 = np.empty(len(W)), np.empty(len(W))
    for i in range(0, len(W), 2_000):
        P = R @ W[i:i + 2_000].T
        nav = np.cumprod(1 + P, axis=0)
        mdd[i:i + 2_000] = (nav / np.maximum.accumulate(nav, axis=0) - 1).min(axis=0)
        q = np.quantile(-P, 0.99, axis=0)
        es99[i:i + 2_000] = np.array([(-P[:, j])[-P[:, j] >= q[j]].mean() for j in range(P.shape[1])])
    mu, C = capm[tick].to_numpy(), cov.loc[tick, tick].to_numpy()
    exp_geo = W @ mu - 0.5 * np.einsum("ij,jk,ik->i", W, C, W)
    df = pd.DataFrame(W, columns=tick).assign(max_drawdown=mdd, ES99_1d=es99, expected_geo=exp_geo)
    ix = {t: tick.index(t) for t in tick}
    df["meets_D6_draft"] = ((W.max(axis=1) <= 0.40) & (W[:, ix["AGG"]] + W[:, ix["GLD"]] >= 0.40)
                            & (W[:, [ix["EEM"], ix["XLE"], ix["XLK"]]].max(axis=1) <= 0.10)
                            & (W[:, [ix["EEM"], ix["XLE"], ix["XLK"]]].sum(axis=1) <= 0.25))
    df.to_csv(out / "research_d3d7_random_portfolios.csv", index=False)

    grid = []
    for caps in (False, True):
        sub = df[df["meets_D6_draft"]] if caps else df
        for m_lim in (0.15, 0.20, 0.25, 0.30, 0.35):
            for e_lim in (0.020, 0.025, 0.030, 0.035, 0.040):
                f = sub[(sub.max_drawdown >= -m_lim) & (sub.ES99_1d <= e_lim)]
                best = f.loc[f.expected_geo.idxmax()] if len(f) else None
                grid.append({"D6_caps": caps, "MDD_limit": m_lim, "ES99_limit": e_lim, "n_feasible": len(f),
                             "max_expected_geo": best.expected_geo if best is not None else np.nan,
                             "meets_minimum_6.66%": bool(best is not None and best.expected_geo >= REQUIRED["minimum"]),
                             "meets_target_7.19%": bool(best is not None and best.expected_geo >= REQUIRED["target"]),
                             "best_weights": "" if best is None else
                             ", ".join(f"{t} {best[t]:.0%}" for t in tick if best[t] >= 0.005)})
    pd.DataFrame(grid).to_csv(out / "research_d3d7_feasibility.csv", index=False)

    need = []
    for lvl, req in REQUIRED.items():
        for caps in (False, True):
            sub = df[(df.expected_geo >= req) & (df["meets_D6_draft"] if caps else True)]
            need.append({"requirement": f"{lvl} {req:.2%}", "D6_caps": caps, "n": len(sub),
                         "lowest_MDD_needed": sub.max_drawdown.max() if len(sub) else np.nan,
                         "lowest_ES99_needed": sub.ES99_1d.min() if len(sub) else np.nan})
    pd.DataFrame(need).to_csv(out / "research_d3d7_risk_needed.csv", index=False)
    print("done:", len(df), "random portfolios;", int(df["meets_D6_draft"].sum()), "meet draft D6 caps")


def forward_drawdowns(n_paths: int = 5_000, years: int = 5, block: int = 63, seed: int = 7) -> None:
    """Gap G1: probability of drawdowns over the next `years`, by moving-block bootstrap of daily ETF returns.

    Each ETF's daily returns are shifted so their mean equals its CAPM expectation (ERP 5%) instead of the
    unusually strong 2004-2026 average. Blocks of `block` days keep volatility clustering and crisis
    sequences (incl. 2008) together. Portfolios are daily-rebalanced to fixed weights.
    """
    s = config.load_settings()
    simple = pd.read_csv(config.DATA_PROCESSED / "simple_returns.csv", index_col=0, parse_dates=True)
    assets = pd.read_csv(config.OUTPUT_TABLES / "cma_assets.csv", index_col=0)
    feas = pd.read_csv(config.OUTPUT_TABLES / "research_d3d7_feasibility.csv")
    tick = list(simple.columns)
    shift = assets.loc[tick, f"capm_E[R] erp {ERP:.0%}"].to_numpy() / cv.TRADING_DAYS - simple.mean().to_numpy()
    R = simple.to_numpy() + shift

    ports = {name: BENCHMARKS[name] for name in ("40/60 SPY/AGG", "Policy 40/50/10 (global eq/AGG/GLD)", "60/40 SPY/AGG")}
    for lim in (0.20, 0.25, 0.30):
        row = feas[(feas.D6_caps) & (feas.MDD_limit == lim) & (feas.ES99_limit == 0.025)].iloc[0]
        ports[f"Best within {lim:.0%} DD (caps, ES 2.5%)"] = {
            t.split(" ")[0]: float(t.split(" ")[1].rstrip("%")) / 100 for t in row.best_weights.split(", ")}

    rng = np.random.default_rng(seed)
    T, n_blocks = len(R), int(np.ceil(years * cv.TRADING_DAYS / block))
    starts = rng.integers(0, T - block, size=(n_paths, n_blocks))
    idx = (starts[:, :, None] + np.arange(block)).reshape(n_paths, -1)[:, : years * cv.TRADING_DAYS]
    rows = {}
    for name, w in ports.items():
        wv = pd.Series(w).reindex(tick, fill_value=0.0)
        wv = (wv / wv.sum()).to_numpy()  # weights from the table are rounded to 1%
        P = R[idx] @ wv                   # paths x days
        nav = np.cumprod(1 + P, axis=1)
        dd = (nav / np.maximum.accumulate(nav, axis=1) - 1).min(axis=1)
        end = nav[:, -1] ** (1 / years) - 1
        rows[name] = {"median_max_dd": np.median(dd), "p95_max_dd": np.quantile(dd, 0.05),
                      "P(DD>15%)": (dd < -0.15).mean(), "P(DD>20%)": (dd < -0.20).mean(),
                      "P(DD>25%)": (dd < -0.25).mean(), "P(DD>30%)": (dd < -0.30).mean(),
                      "median_annual_return": np.median(end), "P(5y real loss, CPI 2.35%)": (end < 0.0235).mean()}
    pd.DataFrame(rows).T.to_csv(config.OUTPUT_TABLES / "research_d7_forward_drawdowns.csv")
    print(f"forward drawdowns: {n_paths} paths x {years}y, block {block}d")


CAP_DESIGNS = {
    # name: (per-ETF max, group rules [(tickers, min, max)])
    "Draft D6 (each <=40%, AGG+GLD >=40%, sats <=10% each / 25% total)":
        ({"SPY": .4, "EFA": .4, "EEM": .1, "AGG": .4, "GLD": .4, "XLE": .1, "XLK": .1},
         [(("AGG", "GLD"), .40, 1.0), (("EEM", "XLE", "XLK"), 0, .25)]),
    "Policy ranges (equity 25-55%, AGG 30-60%, GLD <=20%, sats <=10% each / 20% total)":
        ({"SPY": .4, "EFA": .2, "EEM": .1, "AGG": .6, "GLD": .2, "XLE": .1, "XLK": .1},
         [(("SPY", "EFA", "EEM", "XLE", "XLK"), .25, .55), (("AGG",), .30, .60), (("EEM", "XLE", "XLK"), 0, .20)]),
    "Policy ranges, sector tilts <=15%":
        ({"SPY": .4, "EFA": .2, "EEM": .1, "AGG": .6, "GLD": .2, "XLE": .15, "XLK": .15},
         [(("SPY", "EFA", "EEM", "XLE", "XLK"), .25, .55), (("AGG",), .30, .60), (("EEM", "XLE", "XLK"), 0, .25)]),
    "D6 v2: equity 20-45%, GLD <=20%, each <= 2x benchmark, XLE/XLK <=10% each / 15% together":
        ({"SPY": .45, "EFA": .2, "EEM": .1, "AGG": 1.0, "GLD": .2, "XLE": .1, "XLK": .1},
         [(("SPY", "EFA", "EEM", "XLE", "XLK"), .20, .45), (("XLE", "XLK"), 0, .15)]),
    "Long-only, AGG >= 8% only": ({t: 1.0 for t in ["SPY", "EFA", "EEM", "AGG", "GLD", "XLE", "XLK"]},
                                  [(("AGG",), .08, 1.0)]),
}


def cap_designs(n: int = 40_000, seed: int = 11) -> None:
    """D6: best CAPM expected return per cap design under the approved D7 limits (hist DD <= 25%, ES99 <= 2.5%)."""
    s = config.load_settings()
    lim = s["risk_limits"]
    simple = pd.read_csv(config.DATA_PROCESSED / "simple_returns.csv", index_col=0, parse_dates=True)
    assets = pd.read_csv(config.OUTPUT_TABLES / "cma_assets.csv", index_col=0)
    tick = list(simple.columns)
    mu = assets.loc[tick, f"capm_E[R] erp {ERP:.0%}"].to_numpy()
    C = cma.annual_covariance(simple).loc[tick, tick].to_numpy()
    R = simple.to_numpy()
    rng = np.random.default_rng(seed)
    rows = []
    for name, (caps, groups) in CAP_DESIGNS.items():
        cap = np.array([caps[t] for t in tick])
        W = rng.dirichlet(np.full(len(tick), 0.6), size=n * 20) * 1.0
        ok = (W <= cap + 1e-12).all(axis=1)
        for g, lo, hi in groups:
            tot = W[:, [tick.index(t) for t in g]].sum(axis=1)
            ok &= (tot >= lo) & (tot <= hi)
        W = W[ok][:n]
        P = R @ W.T
        nav = np.cumprod(1 + P, axis=0)
        mdd = (nav / np.maximum.accumulate(nav, axis=0) - 1).min(axis=0)
        q = np.quantile(-P, 0.99, axis=0)
        es99 = np.array([(-P[:, j])[-P[:, j] >= q[j]].mean() for j in range(P.shape[1])])
        geo = W @ mu - 0.5 * np.einsum("ij,jk,ik->i", W, C, W)
        feas = (mdd >= -lim["max_drawdown"]) & (es99 <= lim["es99_1d_max"])
        b = int(np.argmax(np.where(feas, geo, -np.inf)))
        top = np.argsort(np.where(feas, geo, -np.inf))[-50:]  # 50 best feasible: how concentrated are they?
        rows.append({"design": name, "samples": len(W), "feasible_share": feas.mean(),
                     "max_expected_geo": geo[b], "best_weights": ", ".join(f"{t} {W[b, i]:.0%}" for i, t in enumerate(tick) if W[b, i] >= .005),
                     "best_max_dd": mdd[b], "best_ES99": es99[b],
                     "top50_avg_max_single_weight": W[top].max(axis=1).mean(),
                     "top50_avg_GLD": W[top, tick.index("GLD")].mean(), "top50_avg_XLK": W[top, tick.index("XLK")].mean()})
    pd.DataFrame(rows).to_csv(config.OUTPUT_TABLES / "research_d6_cap_designs.csv", index=False)
    print("cap designs written")


def allocation_sweeps(n_paths: int = 4_000, years: int = 5, block: int = 63, seed: int = 5) -> None:
    """D6 calibration from the client's two risks, not from 'best backtest':
      (1) large-loss risk:        historical max DD (full sample and train-only), ES99, P(DD > 25% in 5y)
      (2) purchasing-power risk:  P(5-year compound return < expected inflation), CAPM expected return
    Sweep A: equity share 10-70% (global equity mix SPY/EFA/EEM = 62.5/25/12.5, GLD 10%, rest AGG).
    Sweep B: gold share 0-30% at 40% equity (rest AGG).
    Bootstrap means are reset to CAPM expectations (ERP 5%), as in forward_drawdowns().
    """
    s = config.load_settings()
    simple = pd.read_csv(config.DATA_PROCESSED / "simple_returns.csv", index_col=0, parse_dates=True)
    rates = pd.read_csv(config.DATA_PROCESSED / "rates_daily.csv", index_col=0, parse_dates=True)
    assets = pd.read_csv(config.OUTPUT_TABLES / "cma_assets.csv", index_col=0)
    tick = list(simple.columns)
    infl = rates["breakeven_10y_pct"].iloc[-1] / 100
    mu = assets.loc[tick, f"capm_E[R] erp {ERP:.0%}"]
    cov = cma.annual_covariance(simple)
    R = simple.to_numpy() + (mu.to_numpy() / cv.TRADING_DAYS - simple.mean().to_numpy())
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, len(R) - block, size=(n_paths, int(np.ceil(years * 252 / block))))
    idx = (starts[:, :, None] + np.arange(block)).reshape(n_paths, -1)[:, : years * 252]
    train = simple.loc[: s["split"]["train_end"]]

    def stats(w: dict) -> dict:
        wv = pd.Series(w).reindex(tick, fill_value=0.0)
        hist = simple @ wv
        nav = np.cumprod(1 + R[idx] @ wv.to_numpy(), axis=1)
        dd = (nav / np.maximum.accumulate(nav, axis=1) - 1).min(axis=1)
        ann = nav[:, -1] ** (1 / years) - 1
        return {"hist_max_dd": cv.drawdown(hist).min(), "train_max_dd": cv.drawdown(train @ wv).min(),
                "ES99_1d": es(hist.to_numpy()), "capm_expected_geo": cma.portfolio_expected(wv, mu, cov, assets["ttm_yield"])["expected_geometric"],
                "P(DD>25% 5y)": (dd < -0.25).mean(), "P(5y return < inflation)": (ann < infl).mean(),
                "P(5y return < 0)": (ann < 0).mean()}

    rows = []
    for e in np.arange(0.10, 0.701, 0.05):
        w = {"SPY": .625 * e, "EFA": .25 * e, "EEM": .125 * e, "GLD": 0.10, "AGG": 0.90 - e}
        rows.append({"sweep": "A equity", "equity": e, "gold": 0.10, **stats(w)})
    for g in np.arange(0.0, 0.301, 0.05):
        w = {"SPY": .25, "EFA": .10, "EEM": .05, "GLD": g, "AGG": 0.60 - g}
        rows.append({"sweep": "B gold", "equity": 0.40, "gold": g, **stats(w)})
    pd.DataFrame(rows).to_csv(config.OUTPUT_TABLES / "research_d6_allocation_sweeps.csv", index=False)
    print("allocation sweeps written")


def gold_assessment() -> None:
    """Warning 2: judge gold on what CAPM ignores (crisis behaviour, inflation, stock-bond regimes)."""
    simple = pd.read_csv(config.DATA_PROCESSED / "simple_returns.csv", index_col=0, parse_dates=True)
    cpi = pd.read_csv(config.DATA_PROCESSED / "cpi_monthly.csv", index_col=0, parse_dates=True)
    m = (1 + simple).resample(cv.MONTH_END).prod() - 1
    infl = cpi["inflation_yoy"].shift(1)  # 1-month release lag
    infl.index = infl.index + pd.offsets.MonthEnd(0)
    infl = infl.reindex(m.index)
    rows = []
    for c, (a, b) in CRISES.items():
        rows.append({"test": f"Crisis: {c}", "GLD": (1 + simple.GLD.loc[a:b]).prod() - 1,
                     "SPY": (1 + simple.SPY.loc[a:b]).prod() - 1, "AGG": (1 + simple.AGG.loc[a:b]).prod() - 1})
    down = m.SPY < -0.05
    rows.append({"test": f"Avg month when SPY < -5% ({int(down.sum())} months)", "GLD": m.GLD[down].mean(),
                 "SPY": m.SPY[down].mean(), "AGG": m.AGG[down].mean()})
    rows.append({"test": "Correlation with SPY: all months / SPY < -5% months",
                 "GLD": f"{m.GLD.corr(m.SPY):.2f} / {m.GLD[down].corr(m.SPY[down]):.2f}",
                 "SPY": None, "AGG": f"{m.AGG.corr(m.SPY):.2f} / {m.AGG[down].corr(m.SPY[down]):.2f}"})
    for label, mask in (("CPI YoY > 4%", infl > 0.04), ("CPI YoY <= 2.5%", infl <= 0.025)):
        rows.append({"test": f"Avg month, {label} ({int(mask.sum())} months)", "GLD": m.GLD[mask].mean(),
                     "SPY": m.SPY[mask].mean(), "AGG": m.AGG[mask].mean()})
    sb = m.SPY.rolling(12).corr(m.AGG) > 0  # stocks and bonds moving together (2022-type regime)
    rows.append({"test": f"Avg month, stock-bond corr > 0 ({int(sb.sum())} months)", "GLD": m.GLD[sb].mean(),
                 "SPY": m.SPY[sb].mean(), "AGG": m.AGG[sb].mean()})
    policy = {"SPY": .25, "EFA": .10, "EEM": .05, "AGG": .50, "GLD": .10}
    no_gold = policy | {"AGG": .60, "GLD": 0.0}
    for c, (a, b) in CRISES.items():
        pr = lambda w: (1 + (simple.loc[a:b, list(w)] * pd.Series(w)).sum(axis=1)).prod() - 1  # noqa: E731
        rows.append({"test": f"Policy 40/50/10 vs gold→AGG: {c}", "GLD": f"{pr(policy):.1%} vs {pr(no_gold):.1%}",
                     "SPY": None, "AGG": None})
    pd.DataFrame(rows).to_csv(config.OUTPUT_TABLES / "research_gold_assessment.csv", index=False)
    print("gold assessment written")


if __name__ == "__main__":
    if "--gold" in sys.argv:
        gold_assessment()
    elif "--g1" in sys.argv:
        forward_drawdowns()
    elif "--d6" in sys.argv:
        cap_designs()
    elif "--d6b" in sys.argv:
        allocation_sweeps()
    else:
        main()
