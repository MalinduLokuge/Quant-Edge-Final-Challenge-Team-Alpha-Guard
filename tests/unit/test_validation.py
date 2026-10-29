import numpy as np
import pandas as pd
import pytest
from scipy import stats

from quantedge.validation import backtest as B
from quantedge.validation import coverage as C


def test_kupiec_matches_hand_calculation_and_zero_exceptions():
    exc = np.r_[np.ones(10), np.zeros(490)]  # 2% vs expected 1%
    lr, p = C.kupiec(exc, 0.99)
    pi = 10 / 500
    hand = -2 * (490 * np.log(0.99) + 10 * np.log(0.01) - 490 * np.log(1 - pi) - 10 * np.log(pi))
    assert lr == pytest.approx(hand) and p == pytest.approx(stats.chi2.sf(hand, 1))
    lr0, p0 = C.kupiec(np.zeros(500), 0.99)  # no exceptions: finite, LR = −2·500·ln(0.99)
    assert lr0 == pytest.approx(-2 * 500 * np.log(0.99)) and 0 < p0 < 1


def test_christoffersen_flags_clustering_and_handles_n11_zero():
    spread = np.zeros(1000); spread[::100] = 1                    # 10 isolated exceptions: n11 = 0
    clustered = np.zeros(1000); clustered[500:510] = 1            # same count, all in a row
    s, c = C.christoffersen(spread, 0.99), C.christoffersen(clustered, 0.99)
    assert s["n11"] == 0 and np.isfinite(s["LR_ind"]) and s["p_ind"] > 0.05
    assert c["n11"] == 9 and c["p_ind"] < 1e-6
    assert c["LR_cc"] == pytest.approx(c["LR_ind"] + C.kupiec(clustered, 0.99)[0])


def test_basel_zones():
    assert [C.basel_zone(k) for k in (0, 4, 5, 9, 10)] == ["green", "green", "yellow", "yellow", "red"]
    exc = np.zeros(400); exc[100:110] = 1
    b = C.basel(exc)
    assert b["basel_worst"] == "red" and b["basel_last_count"] == 0 and b["basel_last"] == "green"


def test_correct_model_passes_and_scores_beat_a_wrong_model():
    rng = np.random.default_rng(0)
    loss = rng.normal(0, 1, 20000)
    a = 0.99
    v, e = np.full_like(loss, stats.norm.ppf(a)), np.full_like(loss, stats.norm.pdf(stats.norm.ppf(a)) / (1 - a))
    good = C.evaluate(loss, v, e, a)
    bad = C.evaluate(loss, v * 0.8, e * 0.8, a)
    assert good["p_uc"] > 0.01 and abs(good["z2"]) < 0.1 and good["severity_ratio"] == pytest.approx(1, abs=0.05)
    assert bad["p_uc"] < 1e-6 and bad["z2"] > 0.2
    assert good["quantile_loss"] < bad["quantile_loss"] and good["fz0"] < bad["fz0"]


def _toy(n=1400, seed=1):
    rng = np.random.default_rng(seed)
    r = pd.DataFrame(rng.standard_t(5, (n, 2)) * 0.01, columns=["A", "B"], index=pd.bdate_range("2010-01-01", periods=n))
    return r, {"p": pd.Series({"A": 0.6, "B": 0.4})}


def test_forecasts_use_no_future_data():
    r, port = _toy()
    start, end = r.index[1000], r.index[1030]
    base = B.rolling_forecasts(r, port, start, end, window=500, methods=("historical", "student_t", "garch_evt"), refit_days=10)
    shocked = r.copy()
    shocked.loc[r.index[1020]:] *= 5                              # change the future from day 1020 on
    alt = B.rolling_forecasts(shocked, port, start, end, window=500, methods=("historical", "student_t", "garch_evt"), refit_days=10)
    before = base["date"] <= r.index[1020]                        # forecast for day 1020 uses data ≤ 1019
    pd.testing.assert_frame_equal(base.loc[before, ["VaR", "ES"]], alt.loc[before, ["VaR", "ES"]])
    assert not np.allclose(base.loc[~before, "VaR"], alt.loc[~before, "VaR"])


def test_historical_forecast_equals_window_quantile():
    r, port = _toy()
    fc = B.rolling_forecasts(r, port, r.index[1000], r.index[1000], window=1000, methods=("historical",), alphas=(0.99,))
    loss = -(r.iloc[:1000] @ port["p"]).to_numpy()
    assert fc["VaR"].iloc[0] == pytest.approx(np.quantile(loss, 0.99))
    assert fc["loss"].iloc[0] == pytest.approx(-(r.iloc[1000] @ port["p"]))
