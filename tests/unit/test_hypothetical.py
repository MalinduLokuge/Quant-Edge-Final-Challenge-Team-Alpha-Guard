import numpy as np
import pandas as pd
import pytest

from quantedge.common.conventions import MONTH_END
from quantedge.data import fred
from quantedge.validation import hypothetical as H

F = ["SPY", "d_real10", "d_be10", "d_baa", "oil", "usd"]
TRUE = pd.DataFrame(0.0, index=list(H.ETFS), columns=F)
TRUE.loc["SPY", "SPY"] = 1.0
TRUE.loc["AGG", ["d_real10", "d_be10", "d_baa"]] = [-0.05, -0.05, -0.015]
TRUE.loc["EFA", ["SPY", "usd"]] = [0.7, -1.2]
TRUE.loc["EEM", ["SPY", "usd"]] = [0.5, -1.8]
TRUE.loc["GLD", ["SPY", "d_real10", "usd"]] = [-0.4, -0.08, -1.5]
TRUE.loc["XLE", ["SPY", "oil"]] = [0.7, 0.23]
TRUE.loc["XLK", ["SPY", "usd"]] = [1.2, 0.4]


def _panel(n=600, noise=0.002, seed=0):
    rng = np.random.default_rng(seed)
    f = pd.DataFrame(rng.normal(0, [0.04, 0.2, 0.15, 0.2, 0.08, 0.02], (n, 6)), columns=F,
                     index=pd.date_range("1975-01-31", periods=n, freq=MONTH_END))
    etf = f @ TRUE.T + rng.normal(0, noise, (n, len(H.ETFS)))
    etf["SPY"] = f["SPY"]
    return etf.join(f.drop(columns="SPY"))


def test_factor_vector_converts_percent_to_log():
    v = H.factor_vector({"SPY": -0.2, "d_real10": 0.5, "d_be10": 0.1, "d_baa": 1.0, "oil": 0.5, "usd": -0.1}, F)
    assert v["SPY"] == -0.2 and v["d_baa"] == 1.0
    assert v["oil"] == pytest.approx(np.log(1.5)) and v["usd"] == pytest.approx(np.log(0.9))


def test_fit_betas_recovers_loadings_and_spy_is_exact():
    fit = H.fit_betas(_panel(), F)
    np.testing.assert_allclose(fit["beta"].loc[list(H.ETFS), F], TRUE.loc[list(H.ETFS), F], atol=0.01)
    assert (fit["se"].drop(index="SPY") > 0).all().all() and fit["r2"]["AGG"] > 0.9
    assert fit["beta"].loc["SPY"].tolist() == [1, 0, 0, 0, 0, 0] and fit["months"] == 600


def test_instant_return_equals_sum_of_contributions():
    w = pd.Series({"AGG": 0.6, "SPY": 0.2, "XLK": 0.1, "EFA": 0.1})
    f = pd.Series({"SPY": -0.3, "d_real10": 1.0, "d_be10": 0.5, "d_baa": 1.5, "oil": np.log(1.5), "usd": np.log(1.08)})
    ret, move, c = H.instant(w, TRUE, f)
    assert ret == pytest.approx(c.sum()) and ret == pytest.approx(float(w.reindex(TRUE.index, fill_value=0) @ (TRUE @ f)))
    assert move["AGG"] == pytest.approx(-0.05 * 1.0 - 0.05 * 0.5 - 0.015 * 1.5)


PROF = {"equity": [0.5, 0.5] + [0.0] * 10, "rates": [1.0] + [0.0] * 11, "oil": [1.0] + [0.0] * 11}


def test_path_zero_shock_is_flat_and_costless():
    p = H.path(pd.Series({"AGG": 0.5, "SPY": 0.5}), TRUE, pd.Series(0.0, index=F), PROF, 0.001)
    np.testing.assert_allclose(p["nav"], 1.0)
    assert p["turnover"] == 0 and p["cost"] == 0 and p["max_drawdown"] == 0


def test_path_single_asset_compounds_profile_and_rebalancing_costs():
    f = pd.Series({"SPY": -0.3, "d_real10": 0.0, "d_be10": 0.0, "d_baa": 0.0, "oil": 0.0, "usd": 0.0})
    one = H.path(pd.Series({"SPY": 1.0}), TRUE, f, PROF, 0.001)
    assert one["end_return"] == pytest.approx(-0.3) and one["turnover"] == 0  # (1 − 0.3)^(0.5 + 0.5)
    mix = H.path(pd.Series({"SPY": 0.5, "AGG": 0.5}), TRUE, f, PROF, 0.001)
    # AGG flat, SPY −30% by month 2 → drift to 35/50; one-way turnover at month 3 = |0.4118 − 0.5| = 0.0882
    assert mix["turnover"] == pytest.approx(0.5 - 0.35 / 0.85, rel=1e-9)
    assert mix["cost"] == pytest.approx(0.85 * 2 * mix["turnover"] * 0.001)
    assert mix["end_return"] == pytest.approx(0.85 * (1 - 2 * mix["turnover"] * 0.001) - 1)


def test_d24_spending_rule():
    sp = H.next_year_spending(10e6, -0.2, 0.04, 0.05)
    assert sp["spending"] == pytest.approx(0.7 * 400_000 * 1.05 + 0.3 * 0.04 * 8e6)
    assert sp["real_change"] == pytest.approx(sp["spending"] / 420_000 - 1)
    assert H.next_year_spending(10e6, 0.0, 0.04, 0.0)["spending"] == pytest.approx(400_000)


def test_mc_is_reproducible_and_collapses_without_uncertainty():
    fit = H.fit_betas(_panel(), F)
    w = pd.Series({"AGG": 0.6, "SPY": 0.4})
    f = pd.Series({"SPY": -0.3, "d_real10": 1.0, "d_be10": 0.5, "d_baa": 1.5, "oil": 0.4, "usd": 0.08})
    a = H.mc_losses(w, fit, f * 0.5, f, f * 1.2, 500, 3, 7)
    np.testing.assert_array_equal(a, H.mc_losses(w, fit, f * 0.5, f, f * 1.2, 500, 3, 7))
    certain = dict(fit, se=fit["se"] * 0, resid=fit["resid"] * 0)
    b = H.mc_losses(w, certain, f, f, f, 200, 3, 7)
    np.testing.assert_allclose(b, -H.instant(w, fit["beta"], f)[0], atol=1e-12)


def test_backcast_is_exact_on_noise_free_data():
    panel = _panel(noise=0.0)
    fit = H.fit_betas(panel, F)
    bc = H.backcast(panel, fit["beta"], {"one month": ("1980-03", "1980-03")}, F)
    np.testing.assert_allclose(bc["error"], 0, atol=1e-10)


def test_one_at_a_time_and_scenario_var():
    w = pd.Series({"SPY": 1.0})
    f = pd.Series({"SPY": -0.2, "d_real10": 0.0, "d_be10": 0.0, "d_baa": 0.0, "oil": 0.0, "usd": 0.0})
    oat = H.one_at_a_time(w, TRUE, f, 1.5)
    assert oat["base"] == pytest.approx(0.2) and oat["SPY"] == pytest.approx(0.3) and oat["oil"] == pytest.approx(0.2)
    assert H.scenario_var(0.01, 0.0125, 20, 40) == (0.02, 0.025)


def test_stress_factor_panel_levels_changes_and_end_date():
    days = pd.bdate_range("2020-01-01", "2020-04-30")
    lvl = lambda a, b: pd.Series(np.linspace(a, b, len(days)), index=days)
    series = {"DFII10": lvl(1, 2), "T10YIE": lvl(2, 2.5), "DGS10": lvl(3, 4.5), "DGS2": lvl(1, 1), "BAA10Y": lvl(2, 3),
              "DCOILBRENTEU": lvl(60, 120), "DCOILWTICO": lvl(55, 110), "DTWEXBGS": lvl(100, 110), "VIXCLS": lvl(15, 30)}
    p = fred.stress_factor_panel(series, "2020-03-31")
    assert p.index[-1] == pd.Timestamp("2020-03-31") and len(p) == 3
    assert p["d_real10"].iloc[-1] == pytest.approx(p["lvl_real10"].iloc[-1] - p["lvl_real10"].iloc[-2])
    assert p["oil"].iloc[-1] == pytest.approx(np.log(p["lvl_brent"].iloc[-1] / p["lvl_brent"].iloc[-2]))
