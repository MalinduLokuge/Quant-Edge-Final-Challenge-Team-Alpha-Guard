"""Out-of-sample check of the D7 risk limits (T10.12, research gap G8).

The limits constrain portfolios built on train data (P1-train, weights from data ≤ 2014). This module asks
whether those portfolios still respect the same limits in the later, unseen periods. Per period, on the
quarterly-rebalanced return path (D11) sliced from the full-sample path:
    max drawdown (from the period's own start), 1-day historical VaR/ES at 95 and 99%, and the worst rolling
    250-day ES99 with its share of days above the D23 watch (2.0%) and act (2.5%) levels.
A period passes a limit when its realised value is within it. Rolling ES is a monitoring signal (D23), not a
construction limit: the D7 ES limit is defined on full-cycle history.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from quantedge.common import conventions as cv


def rolling_es(loss: pd.Series, window: int = 250, alpha: float = 0.99) -> pd.Series:
    """Historical ES over trailing windows of daily losses."""
    def es(x):
        v = np.quantile(x, alpha)
        return x[x >= v].mean()
    return loss.rolling(window).apply(es, raw=True)


def ladder_step(drawdown: float, rolling_es99: float, basel_zone: str | None, ladder: dict) -> str | None:
    """Highest D23 step that fires (None = normal). drawdown is a positive fraction. A step fires on its drawdown or
    Basel zone; rolling ES fires only the first step that uses it (watch and act share 2.5%, so act needs the drawdown)."""
    steps = list(ladder)
    fired = {k for k in steps if drawdown >= ladder[k].get("drawdown", np.inf)
             or (basel_zone and basel_zone == ladder[k].get("basel_zone"))}
    es_step = next((k for k in steps if "rolling_es99" in ladder[k]), None)
    if es_step and rolling_es99 > ladder[es_step]["rolling_es99"]:
        fired.add(es_step)
    return max(fired, key=steps.index) if fired else None


def period_metrics(rp: pd.Series, watch: float, act: float, window: int = 250) -> dict:
    loss = -rp.to_numpy()
    out = {"days": len(rp), "max_drawdown": float(cv.drawdown(rp).min())}
    for a in (0.95, 0.99):
        v = float(np.quantile(loss, a))
        out[f"VaR{int(a * 100)}_1d"], out[f"ES{int(a * 100)}_1d"] = v, float(loss[loss >= v].mean())
    r = rolling_es(-rp, window).dropna()
    out["rolling_ES99_max"] = float(r.max()) if len(r) else np.nan
    out["share_days_rolling_ES99_above_watch"] = float((r > watch).mean()) if len(r) else np.nan
    out["share_days_rolling_ES99_above_act"] = float((r > act).mean()) if len(r) else np.nan
    return out


def limit_table(simple: pd.DataFrame, ports: dict[str, pd.Series], periods: dict[str, tuple], limits: dict,
                rebalance: str = "quarterly") -> pd.DataFrame:
    lad = limits["action_ladder"]
    rows = []
    for name, w in ports.items():
        w = w[w.abs() > 1e-9]
        rp, _ = cv.rebalanced_returns(simple, w / w.sum(), rebalance)
        for p, (a, b) in periods.items():
            m = period_metrics(rp.loc[a:b], lad["watch"]["rolling_es99"], lad["act"]["rolling_es99"])
            m["pass_drawdown"] = m["max_drawdown"] >= -limits["max_drawdown"]
            m["pass_ES99"] = m["ES99_1d"] <= limits["es99_1d_max"]
            m["pass_VaR99"] = m["VaR99_1d"] <= limits["var99_1d_max"]
            m["pass_ES95"] = m["ES95_1d"] <= limits["es95_1d_max"]
            m["pass_VaR95"] = m["VaR95_1d"] <= limits["var95_1d_max"]
            m["pass_all"] = all(m[k] for k in m if k.startswith("pass_"))
            rows.append({"portfolio": name, "period": p, "start": a, "end": b, **m})
    return pd.DataFrame(rows)
