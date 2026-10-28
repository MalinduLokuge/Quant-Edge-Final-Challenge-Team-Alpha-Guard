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
    assert round(full["required_gross"], 4) == 0.0719 and round(full["required_minimum"], 4) == 0.0666  # D12
    assert train["inflation"] == 0.0168 and round(train["required_gross"], 4) == 0.0649
