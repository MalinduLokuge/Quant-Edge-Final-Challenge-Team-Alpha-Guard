"""Version-3 research: are the Sharpe-ratio differences between our portfolio and the Policy 40/50/10 benchmark
statistically significant? Ledoit–Wolf (2008) HAC test and studentized circular block bootstrap
(validation.sharpe_test), on daily excess returns over DTB3, quarterly rebalancing (D11) for both.

Each comparison first reproduces the Sharpe ratios already published, then tests their difference:
    walk-forward 2009–26   R126 rule (D32 → O6) rebuilt from research_walkforward_weights.csv vs policy
                           (the "0.89 vs 0.75" in memo, tear sheet and report)
    2015–19, 2020–26       P1-train D26 weights (data ≤ 2014) vs policy (kpis.csv; tear sheet table)
    full sample            O6 (P1-final) vs policy: in-sample, weights use these years
Bootstrap block lengths 5 / 21 / 63 days (21 primary), 5,000 resamples, seed 42.

    python scripts/research_v2_sharpe_test.py  → outputs/tables/research_v2_sharpe_test.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from quantedge.common import config  # noqa: E402
from quantedge.common import conventions as cv  # noqa: E402
from quantedge.validation import sharpe_test as S  # noqa: E402

ORIGINS = ["2008-12-31", "2011-12-30", "2014-12-31", "2017-12-29", "2020-12-31", "2023-12-29"]   # research_walkforward.py
BLOCKS, REPS, SEED = (5, 21, 63), 5000, 42


def rebal(simple, w):
    w = w[w > 1e-9]
    return cv.rebalanced_returns(simple, w / w.sum(), "quarterly")[0]


def walk_forward(simple, rf, bench):
    """Chained 3-year segments, weights re-chosen at each origin with earlier data only (T20.07)."""
    W = pd.read_csv(config.OUTPUT_TABLES / "research_walkforward_weights.csv")
    W = W[W["rule"] == "R126 (D32, O6 rule)"].set_index("origin")[simple.columns].fillna(0.0)
    ends = ORIGINS[1:] + [str(simple.index[-1].date())]
    a, b = [], []
    for o, e in zip(ORIGINS, ends):
        seg = simple.loc[pd.Timestamp(o) + pd.Timedelta(days=1):e]
        a.append(rebal(seg, W.loc[o]))
        b.append(rebal(seg, bench))
    return pd.concat(a), pd.concat(b)


def main() -> None:
    s = config.load_settings()
    simple = pd.read_csv(config.DATA_PROCESSED / "simple_returns.csv", index_col=0, parse_dates=True)
    rf = pd.read_csv(config.DATA_PROCESSED / "rates_daily.csv", index_col=0, parse_dates=True)["rf_daily"]
    bench = pd.Series(s["benchmarks"]["primary"]["weights"]).reindex(simple.columns, fill_value=0.0)
    train = pd.read_csv(config.OUTPUT_TABLES / "p1_train_weights.csv", index_col=0).loc["d26_selected"]
    final = pd.read_csv(config.OUTPUT_TABLES / "p1_final_weights.csv", index_col=0).loc["d26_selected"]
    kp = pd.read_csv(config.OUTPUT_TABLES / "kpis.csv").set_index(["portfolio", "period"])["Sharpe"]
    wf = pd.read_csv(config.OUTPUT_TABLES / "research_walkforward_summary.csv").set_index("rule")["Sharpe"]
    sp = s["split"]
    cases = [("Walk-forward 2009-26 (R126 rule -> O6)", "out-of-sample (rule chosen in 2026)", *walk_forward(simple, rf, bench),
              wf["R126 (D32, O6 rule)"], wf["Policy 40/50/10 (fixed)"])]
    for label, per, a, z in (("2015-19 (D26 weights from data <= 2014)", "validation", "2015-01-01", sp["validation_end"]),
                             ("2020-26 (D26 weights from data <= 2014)", "test", "2020-01-01", None)):
        r = simple.loc[a:z]
        cases.append((label, "out-of-sample", rebal(r, train), rebal(r, bench),
                      kp[("d26_selected", per)], kp[("[benchmark] Policy 40/50/10", per)]))
    cases.append(("Full sample 2004-26 (O6 final weights)", "in-sample", rebal(simple, final), rebal(simple, bench),
                  kp[("d26_selected", "full (in-sample)")], kp[("[benchmark] Policy 40/50/10", "full (in-sample)")]))
    rows = []
    for label, kind, ra, rb, pub_a, pub_b in cases:
        ex_a = (ra - rf.reindex(ra.index).fillna(0)).to_numpy()
        ex_b = (rb - rf.reindex(rb.index).fillna(0)).to_numpy()
        h = S.lw_hac(ex_a, ex_b)
        row = {"comparison": label, "kind": kind, "start": ra.index[0].date(), "end": ra.index[-1].date(),
               "published_SR_portfolio": pub_a, "published_SR_policy": pub_b, **h}
        for b in BLOCKS:
            row[f"p_boot_b{b}"] = S.lw_bootstrap(ex_a, ex_b, b, REPS, SEED)
        row["significant_5pct"] = bool(row["p_hac"] < 0.05 and row["p_boot_b21"] < 0.05)
        rows.append(row)
        print(f"{label:44s} SR {h['SR_a']:.3f} vs {h['SR_b']:.3f} (published {pub_a:.3f} / {pub_b:.3f})  "
              f"diff {h['diff']:+.3f}  se {h['se']:.3f}  p_HAC {h['p_hac']:.3f}  p_boot21 {row['p_boot_b21']:.3f}", flush=True)
    pd.DataFrame(rows).to_csv(config.OUTPUT_TABLES / "research_v2_sharpe_test.csv", index=False)


if __name__ == "__main__":
    main()
