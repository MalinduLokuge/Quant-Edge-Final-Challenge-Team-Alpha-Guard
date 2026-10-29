"""The data stage must reproduce Raveena's original T2 outputs from the committed snapshot."""
from pathlib import Path

import pandas as pd
import pytest

from quantedge.common import config
from quantedge.data import clean, diagnostics, ingest

FIX = Path(__file__).resolve().parents[1] / "fixtures" / "reference_t2"


@pytest.fixture(scope="module")
def stage():
    s = config.load_settings()
    raw = ingest.load_snapshot(config.DATA_RAW / s["data"]["snapshot"])[sorted(s["universe"])]
    prices = clean.align_common_sample(raw)
    log = clean.log_returns(prices)
    return prices, log, clean.zscore_outlier_flags(log, s["data"]["outlier_z_threshold"])


def test_common_sample_window(stage):
    prices, _, _ = stage
    assert str(prices.index[0].date()) == "2004-11-18"
    assert str(prices.index[-1].date()) == "2026-10-19"
    assert prices.notna().all().all()


def test_log_returns_match_reference(stage):
    _, log, _ = stage
    ref = pd.read_csv(FIX / "log_returns_head_tail.csv", index_col=0, parse_dates=True)
    pd.testing.assert_frame_equal(log.loc[ref.index], ref, check_names=False, rtol=1e-12)
    summ = pd.read_csv(FIX / "log_returns_summary.csv", index_col=0)
    pd.testing.assert_series_equal(log.sum(), summ["sum"], check_names=False, rtol=1e-10)
    assert (log.count() == summ["n"]).all()


def test_outlier_flags_match_reference(stage):
    _, _, flags = stage
    ref = pd.read_csv(FIX / "outlier_flag_counts.csv", index_col=0)["flags"]
    assert (flags.sum() == ref.loc[flags.columns]).all()


def test_adf_matches_reference(stage):
    _, log, _ = stage
    ref = pd.read_csv(FIX / "adf_results.csv", index_col=0)
    adf = diagnostics.adf_table(log)
    pd.testing.assert_series_equal(adf["ADF Statistic"].astype(float).loc[ref.index], ref["ADF Statistic"], check_names=False, rtol=1e-9)


def test_fred_rates_cover_whole_sample(stage):
    from quantedge.data import fred

    prices, _, _ = stage
    d = config.load_settings()["data"]
    snaps = {k: fred.load_snapshot(config.DATA_EXTERNAL / v) for k, v in d["fred_snapshots"].items()}
    rates = fred.rates_frame(snaps["DTB3"], snaps["DGS10"], prices.index, d["fred_max_stale_days"])
    assert rates[["dtb3_pct", "dgs10_pct"]].notna().all().all()
    assert rates["dtb3_pct"].between(-1, 20).all()
    assert rates["dgs10_pct"].between(0, 20).all()


def test_split_matches_approved_d5(stage):
    from quantedge.data import split

    _, log, _ = stage
    s = config.load_settings()
    summ = split.summary(split.split_labels(log.index, s["split"]["train_end"], s["split"]["validation_end"]))
    assert summ["observations"].tolist() == [2546, 1258, 1708]  # D5 (research doc §5b)
    assert str(summ.loc["train", "start"]) == "2004-11-19" and str(summ.loc["test", "end"]) == "2026-10-19"


def test_train_and_full_hurdles_match_d12():
    from quantedge.portfolio import return_objective as ro
    import pandas as pd

    s = config.load_settings()
    rates = pd.read_csv(config.DATA_PROCESSED / "rates_daily.csv", index_col=0, parse_dates=True)
    full = ro.required_return_as_of(rates, rates.index[-1], s["mandate"])
    train = ro.required_return_as_of(rates, s["split"]["train_end"], s["mandate"])
    # D12 with the D30 spending rate 2.65% (revised 2026-10-30; 7.19% / 6.66% at 4%): (1.0235)(1.0265)(1.005)(1.002) − 1
    assert round(full["required_gross"], 4) == 0.058 and round(full["required_minimum"], 4) == 0.0527
    assert train["inflation"] == 0.0168 and round(train["required_gross"], 4) == 0.0511


def test_p1_candidates_meet_d6_and_d7():
    import pandas as pd

    s = config.load_settings()
    c, lim = s["constraints"], s["risk_limits"]
    for p1 in ("p1_train", "p1_final"):
        w = pd.read_csv(config.OUTPUT_TABLES / f"{p1}_weights.csv", index_col=0)
        d = pd.read_csv(config.OUTPUT_TABLES / f"{p1}_diagnostics.csv", index_col=0)
        assert {"min_variance", "risk_parity", "max_sharpe", "min_cvar", "target_return"} <= set(w.index)
        for name, row in w.iterrows():
            assert abs(row.sum() - 1) < 1e-6 and (row >= -1e-12).all()
            assert all(row[t] <= c["max_weight"][t] + 1e-6 for t in row.index)
            for g in c["groups"].values():
                assert g["min"] - 1e-6 <= row[g["tickers"]].sum() <= g["max"] + 1e-6
            # historical D7 limits are hard constraints; the 5-year probability is a post-check that may flag
            assert str(d.loc[name, "pass_D7_historical"]) == "True"
            p = float(d.loc[name, "P(DD>limit, 5y)"])
            assert str(d.loc[name, "pass_D7"]) == str(p <= lim["max_prob_drawdown_breach_5y"])
            assert float(d.loc[name, "max_drawdown"]) >= -lim["max_drawdown"] - 1e-9
            assert float(d.loc[name, "ES99_1d"]) <= lim["es99_1d_max"] + 1e-9


def test_frontier_is_monotone_and_starts_at_min_variance():
    import pandas as pd

    f = pd.read_csv(config.OUTPUT_TABLES / "frontier_full.csv", index_col=0)
    d = pd.read_csv(config.OUTPUT_TABLES / "p1_final_diagnostics.csv", index_col=0)
    assert (f["expected_geo"].diff().dropna() > -1e-6).all()          # return rises along the frontier
    assert (f["volatility"].diff().dropna() > -1e-6).all()            # and so does risk
    assert abs(f["expected_geo"].iloc[0] - float(d.loc["min_variance", "expected_geo"])) < 1e-6
    assert (f["spending_usd"].diff().dropna() > 0).all()


def test_kpis_and_d26_selection_outputs():
    import pandas as pd

    s = config.load_settings()
    k = pd.read_csv(config.OUTPUT_TABLES / "kpis.csv", index_col=0)
    assert set(k["period"]) == {"train", "validation", "test", "full (in-sample)"}
    spy = k[k.index == "[benchmark] SPY (CAPM market)"]
    assert (spy["beta"].sub(1).abs() < 1e-9).all() and (spy["Jensen_alpha"].abs() < 1e-9).all()
    for p1 in ("p1_train", "p1_final"):
        d = pd.read_csv(config.OUTPUT_TABLES / f"{p1}_diagnostics.csv", index_col=0)
        sel = d.loc["d26_selected"]
        assert str(sel["pass_D7"]) == "True"
        assert float(sel["P(DD>limit, 5y)"]) <= s["risk_limits"]["max_prob_drawdown_breach_5y"]
        assert float(sel["expected_geo"]) >= float(d.loc["min_variance", "expected_geo"]) - 1e-9


def test_p2_var_es_complete_and_consistent():
    import pandas as pd

    s = config.load_settings()
    v = pd.read_csv(config.OUTPUT_TABLES / "p2_var_es.csv")
    assert set(v["method"]) == {"historical", "normal", "student_t", "monte_carlo_t_copula"}
    assert set(v["alpha"]) == set(s["risk"]["confidence_levels"])
    assert (v["ES"] >= v["VaR"] - 1e-12).all()                      # ES never below VaR
    assert ((v["VaR_ci_low"] <= v["VaR"] + 1e-12) & (v["VaR"] <= v["VaR_ci_high"] + 1e-12)).all()
    d26 = v[(v.portfolio == "d26_selected") & (v.method == "historical") & (v.alpha == 0.99)].iloc[0]
    assert d26["VaR"] <= s["risk_limits"]["var99_1d_max"] and d26["ES"] <= s["risk_limits"]["es99_1d_max"]
