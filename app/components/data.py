"""Shared, cached loaders for the Streamlit app (T14.08). The app reads saved pipeline outputs only; it never
estimates models. The only calculations here are presentation transforms that reuse the project's own functions
(portfolio return paths via common.conventions, backtest tests on a date slice via validation.coverage)."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from quantedge.common import config  # noqa: E402
from quantedge.common import conventions as cv  # noqa: E402
from quantedge.validation import coverage, limits  # noqa: E402

TABLES = config.OUTPUT_TABLES
P3 = TABLES.parent / "p3_decision"
FINAL = "d26_selected"            # the approved final portfolio (O6, D31 v2)
FINAL_LABEL = "Recommended (O6)"
NAV = 10_000_000

LABELS = {"d26_selected": FINAL_LABEL, "min_variance": "Minimum variance", "min_cvar": "Minimum CVaR",
          "risk_parity": "Risk parity", "max_sharpe": "Max Sharpe", "target_return": "Target return",
          "max_expected_return": "Max expected return"}
METHOD_LABELS = {"historical": "Historical", "normal": "Normal (parametric)", "student_t": "Student-t",
                 "monte_carlo_t_copula": "Monte Carlo (t-copula)", "monte_carlo": "Monte Carlo (t-copula)",
                 "evt": "EVT (POT-GPD)", "evt_pot": "EVT (POT-GPD)", "garch_t": "GARCH-t", "garch_evt": "GARCH-EVT"}


def label(name: str) -> str:
    return LABELS.get(name, name.replace("[benchmark] ", "Benchmark: "))


def available() -> bool:
    return (TABLES / "p1_final_weights.csv").exists() and (P3 / "p3_summary.csv").exists()


@st.cache_data
def settings() -> dict:
    return config.load_settings()


@st.cache_data
def table(name: str, **kw) -> pd.DataFrame:
    return pd.read_csv(TABLES / f"{name}.csv", **kw)


@st.cache_data
def p3(name: str) -> pd.DataFrame:
    return pd.read_csv(P3 / f"{name}.csv")


@st.cache_data
def returns() -> pd.DataFrame:
    return pd.read_csv(config.DATA_PROCESSED / "simple_returns.csv", index_col=0, parse_dates=True)


@st.cache_data
def portfolios() -> dict[str, pd.Series]:
    """Final portfolio, the other P1-final candidates and the benchmarks (weights)."""
    s = settings()
    w = pd.read_csv(TABLES / "p1_final_weights.csv", index_col=0)
    out = {label(FINAL): w.loc[FINAL]}
    out |= {label(n): w.loc[n] for n in s["risk"]["p2_portfolios"] if n in w.index and n != FINAL}
    b = s["benchmarks"]
    out[f"Benchmark: {b['primary']['name']}"] = pd.Series(b["primary"]["weights"])
    out |= {f"Benchmark: {k}": pd.Series(v) for k, v in b.get("secondary", {}).items()}
    return out


@st.cache_data
def paths(start=None, end=None) -> pd.DataFrame:
    """Quarterly-rebalanced daily returns (D11) of every portfolio over [start, end]."""
    r = returns().loc[start:end]
    out = {}
    for name, w in portfolios().items():
        w = w[w > 1e-9]
        out[name] = cv.rebalanced_returns(r, w / w.sum(), "quarterly")[0]
    return pd.DataFrame(out)


@st.cache_data
def forecasts(period: str) -> pd.DataFrame:
    return pd.read_csv(TABLES / f"backtest_forecasts_{period}.csv", parse_dates=["date"])


LADDER_ICON = {None: "🟢", "watch": "🔵", "review": "🟡", "act": "🟠", "limit": "🔴"}


@st.cache_data
def ladder_status() -> dict:
    """D23 action-ladder step of the final portfolio on the last data day. Signals: drawdown from peak (full path),
    rolling 250-day ES99 and the Basel zone of the GARCH-EVT 99% test backtest (a model check on the P1-train weights);
    step rule in validation.limits.ladder_step. GARCH-EVT VaR99 (today's volatility, risk stage) is shown, not a trigger."""
    s = settings()
    lad, steps = s["risk_limits"]["action_ladder"], list(s["risk_limits"]["action_ladder"])
    rp = paths()[label(FINAL)]
    dd = -float(cv.drawdown(rp).iloc[-1])
    es = float(limits.rolling_es(-rp, s["risk_limits"]["monitoring"]["rolling_es_window"]).iloc[-1])
    fc = forecasts("test")
    one = fc[(fc.portfolio == FINAL) & (fc.method == s["validation"]["selected_model"]) & (fc.alpha.round(2) == 0.99)].sort_values("date")
    zone = coverage.basel((one["loss"] > one["VaR"]).to_numpy())["basel_last"]
    es_step = next(k for k in steps if "rolling_es99" in lad[k])
    step = limits.ladder_step(dd, es, zone, lad)
    g = table("p2_garch_evt")
    g = g[(g.portfolio == FINAL) & (g.regime == "current") & (g.alpha.round(3) == 0.99)]
    return {"date": rp.index[-1].date(), "step": step, "action": lad[step]["action"] if step else "no action; normal monitoring",
            "drawdown": dd, "rolling_es99": es, "es_trigger": lad[es_step]["rolling_es99"], "basel": zone,
            "garch_var99": float(g["VaR"].iloc[0]) if len(g) else float("nan"), "var99_limit": s["risk_limits"]["var99_1d_max"],
            "levels": {k: lad[k]["drawdown"] for k in steps}}


def pct(x, d: int = 1) -> str:
    return "—" if pd.isna(x) else f"{x:.{d}%}"


def usd(x) -> str:
    return "—" if pd.isna(x) else f"${x:,.0f}"
