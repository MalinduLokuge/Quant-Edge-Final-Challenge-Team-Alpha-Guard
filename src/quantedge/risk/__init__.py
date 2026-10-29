"""Risk stage (brief Layers 2–4, §8.6): P2 risk evidence for every P1 candidate and the policy benchmark.

Implemented: VaR and ES by historical, normal, Student-t and Monte Carlo (t-copula) at 90/95/99% with
uncertainty bands (T6, T7), and model-assumption diagnostics (T6.08). Window: full sample (full-cycle history,
D7). Outputs (outputs/tables/): p2_var_es.csv, p2_diagnostics.csv.
"""
from __future__ import annotations

import pandas as pd

from quantedge.common import config
from quantedge.risk import var_es


def portfolios(settings: dict) -> dict[str, pd.Series]:
    w = pd.read_csv(config.OUTPUT_TABLES / "p1_final_weights.csv", index_col=0)
    out = {name: w.loc[name] for name in settings["risk"]["p2_portfolios"] if name in w.index}
    b = settings["benchmarks"]["primary"]
    out[f"[benchmark] {b['name']}"] = pd.Series(b["weights"])
    return out


def run() -> dict:
    s = config.load_settings()
    r = s["risk"]
    simple = pd.read_csv(config.DATA_PROCESSED / "simple_returns.csv", index_col=0, parse_dates=True)
    nav = s["portfolio_value_usd"]
    tables, diags = [], {}
    for name, w in portfolios(s).items():
        t = var_es.var_es_table(simple, w, nav, tuple(r["confidence_levels"]), r["mc_simulations"],
                                r["bootstrap_reps"], r["bootstrap_reps_t"], r["random_seed"])
        tables.append(t.assign(portfolio=name))
        loss = -(simple.to_numpy() @ w.reindex(simple.columns, fill_value=0.0).to_numpy())
        diags[name] = var_es.assumption_diagnostics(loss) | {"mc_copula_dof": t.attrs["mc_dof"]}
    out = config.OUTPUT_TABLES
    pd.concat(tables).to_csv(out / "p2_var_es.csv", index=False)
    pd.DataFrame(diags).T.to_csv(out / "p2_diagnostics.csv")
    print(f"[risk] VaR/ES for {len(diags)} portfolios x {len(r['confidence_levels'])} levels x 4 methods")
    return {"var_es": pd.concat(tables), "diagnostics": pd.DataFrame(diags).T}
