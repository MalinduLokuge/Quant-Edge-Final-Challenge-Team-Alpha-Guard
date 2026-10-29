"""T4.25 evidence: final-selection robustness options for the decision gate (T20).

Options (each built by the same rules on the 2026 inputs = P1-final, and on the 2014 inputs = P1-train for an
honest out-of-sample check):
    O1  D26 + D27 cap (current recommendation)
    O2  D26 with a margin on the 5-year drawdown test: P(DD > 25% in 5y) ≤ 4% instead of 5%
    O3  50/50 blend of D26 and Risk Parity (Risk Parity did best in 2020–26)
    O4  D26 with a gold floor of 5% (inflation hedge; stress tests show bonds fail in inflationary shocks)
    O5  Risk Parity alone
Scores: expected return and spending, D7 metrics, D27 max ES share, historical and hypothetical stress losses,
out-of-sample KPIs of the 2014-built version (validation 2015–19, test 2020–26).

    python scripts/research_t425_options.py      → outputs/tables/research_t425_options.csv, research_t425_option_weights.csv
"""
from __future__ import annotations

import copy
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from quantedge.common import config  # noqa: E402
from quantedge.common import conventions as cv  # noqa: E402
from quantedge.portfolio import frontier as fr  # noqa: E402
from quantedge.portfolio import kpis as K  # noqa: E402
from quantedge.portfolio import optimise as op  # noqa: E402
from quantedge.portfolio import return_objective as ro  # noqa: E402
from quantedge.validation import hypothetical as H  # noqa: E402
from quantedge.validation import stress as S  # noqa: E402


def inputs(label, simple, s):
    out = config.OUTPUT_TABLES
    a = pd.read_csv(out / f"cma_{label}.csv", index_col=0)
    c = pd.read_csv(out / f"cma_{label}_cov_shrunk.csv", index_col=0)
    summ = pd.read_csv(out / "cma_sets_summary.csv", index_col=0)
    t = list(simple.columns)
    scen = simple if label == "full" else simple.loc[: s["split"]["train_end"]]
    inp = op.Inputs(t, a.loc[t, "expected_arithmetic"].to_numpy(), c.loc[t, t].to_numpy(), scen,
                    float(summ.loc["rf", label]), float(summ.loc["required_target", label]), s["constraints"], s["risk_limits"])
    inp.es_cap = s["constraints"]["component_es_max"]
    return inp, float(summ.loc["inflation_breakeven", label])


def select(inp, s):
    lo = op.solve_with_postcheck(op.with_es_cap(op.min_variance), inp)
    hi = op.solve_with_postcheck(op.with_es_cap(op.max_expected_return), inp)
    if lo[0] is None or hi[0] is None:
        return None
    sel = fr.select_highest_compliant(inp, s, lo[2]["expected_geo"], hi[2]["expected_geo"])
    return None if sel is None else sel[0]


def build(option, label, simple, s):
    """Weights of an option on one input set."""
    w_saved = pd.read_csv(config.OUTPUT_TABLES / f"p1_{'final' if label == 'full' else 'train'}_weights.csv", index_col=0)
    if option == "O1 D26 + D27 (current)":
        return w_saved.loc["d26_selected"]
    if option == "O3 50/50 D26 + Risk Parity":
        return 0.5 * w_saved.loc["d26_selected"] + 0.5 * w_saved.loc["risk_parity"]
    if option == "O5 Risk Parity":
        return w_saved.loc["risk_parity"]
    s2 = copy.deepcopy(s)
    if option == "O2 D26, 5-year test margin (4%)":
        s2["risk_limits"]["max_prob_drawdown_breach_5y"] = 0.04
    if option == "O4 D26 + gold floor 5%":
        s2["constraints"]["groups"]["gold"]["min"] = 0.05
    inp, _ = inputs(label, simple, s2)
    w = select(inp, s2)
    return None if w is None else pd.Series(w, index=simple.columns)


def main():
    s = config.load_settings()
    simple = pd.read_csv(config.DATA_PROCESSED / "simple_returns.csv", index_col=0, parse_dates=True)
    rates = pd.read_csv(config.DATA_PROCESSED / "rates_daily.csv", index_col=0, parse_dates=True)
    beta = pd.read_csv(config.OUTPUT_TABLES / "stress_hyp_betas.csv", index_col=0)
    beta = beta[beta["sample"] == "full"][s["stress"]["hypothetical"]["factors"]]
    hyp = s["stress"]["hypothetical"]
    m, lim = s["mandate"], s["risk_limits"]
    options = ["O1 D26 + D27 (current)", "O2 D26, 5-year test margin (4%)", "O3 50/50 D26 + Risk Parity",
               "O4 D26 + gold floor 5%", "O5 Risk Parity"]
    rows, saved = [], []
    for o in options:
        row = {"option": o}
        for label in ("full", "train"):
            t0 = time.time()
            w = build(o, label, simple, s)
            if w is None:
                row[f"{label}_status"] = "infeasible"
                continue
            w = w.reindex(simple.columns, fill_value=0.0)
            w = w / w.sum()
            saved.append(w.rename(f"{o} | {label}"))
            inp, infl = inputs(label, simple, s)
            d = op.diagnostics(w.to_numpy(), inp)
            p = fr.forward_drawdown_prob(w.to_numpy(), inp.scenarios[inp.tickers].to_numpy(), inp.mu, lim["max_drawdown"], **fr.dd_test_kwargs(s))
            row |= {f"{label}_{k}": v for k, v in {
                "weights": ", ".join(f"{k} {v:.1%}" for k, v in w.items() if v > 0.004),
                "expected": d["expected_geo"], "max_drawdown": d["max_drawdown"], "ES99": d["ES99_1d"], "VaR99": d["VaR99_1d"],
                "P_DD25_5y": p, "max_ES_share": d["max_ES99_share"], "max_ES_etf": d["max_ES99_share_etf"],
                "pass_D7": bool(d["pass_D7"] and p <= lim["max_prob_drawdown_breach_5y"]),
                "pass_D27": d["max_ES99_share"] <= s["constraints"]["component_es_max"] + 1e-3}.items()}
            if label == "full":
                row["full_spending"] = ro.sustainable_spending(d["expected_geo"], infl, m["real_growth"]["base"], m["extra_costs"]["base"])
                for scen, (a, b) in s["stress"]["windows"].items():
                    row[f"stress_{scen}"] = S.replay(simple, w, a, b)["max_drawdown_in_window"]
                for scen, spec in hyp["scenarios"].items():
                    for sev in ("central", "severe"):
                        if sev in spec:
                            row[f"hyp_{scen.split()[0]}_{sev}"] = H.instant(w, beta, H.factor_vector(spec[sev], beta.columns))[0]
            else:
                sp, day = s["split"], pd.Timedelta(days=1)
                t_end, v_end = pd.Timestamp(sp["train_end"]), pd.Timestamp(sp["validation_end"])
                for period, (a, b) in {"val": (t_end + day, v_end), "test": (v_end + day, None)}.items():
                    k = K.kpi_table(simple, rates["rf_daily"], {"x": w}, s, a, b).loc["x"]
                    for key in ("CAGR", "Sharpe", "Calmar", "max_drawdown", "Information_ratio"):
                        row[f"oos_{period}_{key}"] = float(k[key])
            print(f"{o:34s} {label:5s} done in {time.time() - t0:5.0f}s", flush=True)
        rows.append(row)
        pd.DataFrame(rows).to_csv(config.OUTPUT_TABLES / "research_t425_options.csv", index=False)
        pd.DataFrame(saved).rename_axis("option | inputs").to_csv(config.OUTPUT_TABLES / "research_t425_option_weights.csv")
    print("written research_t425_options.csv")


if __name__ == "__main__":
    main()
