import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from quantedge.risk.extensions import regime as RG
from quantedge.validation import backtest as B
from quantedge.validation import coverage as C


def _script():
    path = Path(__file__).resolve().parents[2] / "scripts" / "research_v2_regime_blend.py"
    spec = importlib.util.spec_from_file_location("research_v2_regime_blend", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _daily(seed=0):
    """Synthetic daily table in the script's layout: O6, both levels, three periods."""
    rng = np.random.default_rng(seed)
    rows = []
    for p, start in (("early", "2009-01-01"), ("validation", "2015-01-01"), ("test", "2020-01-01")):
        idx = pd.bdate_range(start, periods=800)
        sig = 0.01 * np.exp(np.cumsum(rng.normal(0, 0.05, 800)))
        loss = rng.standard_t(5, 800) * sig
        for a in (0.95, 0.99):
            k = 2.0 if a == 0.95 else 3.0
            rows.append(pd.DataFrame({"period": p, "portfolio": "O6", "alpha": a, "date": idx, "loss": loss,
                                      "VaR_historical": k * 0.010 + 0 * sig, "ES_historical": k * 0.013 + 0 * sig,
                                      "VaR_evt": k * 0.011 + 0 * sig, "ES_evt": k * 0.015 + 0 * sig,
                                      "VaR_garch_evt": k * sig, "ES_garch_evt": 1.3 * k * sig,
                                      "ratio_252": rng.uniform(0.6, 1.5, 800), "ratio_1000": rng.uniform(0.6, 1.5, 800)}))
    return pd.concat(rows, ignore_index=True)


def test_variant_selection_ignores_the_test_period_and_scores_match_coverage():
    S = _script()
    d = _daily()
    sel, sens = S.select_variant(d, 0.05)
    t = d["period"] == "test"
    d2 = d.copy()
    d2.loc[t, "loss"] *= 3                                             # change everything in the test period
    d2.loc[t, ["ratio_252", "ratio_1000"]] = d2.loc[t, ["ratio_252", "ratio_1000"]][::-1].to_numpy()
    sel2, sens2 = S.select_variant(d2, 0.05)
    assert sel == sel2 and sel in S.GRID and len(S.GRID) == 12 and S.PRIMARY in S.GRID
    v = sens["period"] == "validation"
    pd.testing.assert_frame_equal(sens[v].reset_index(drop=True), sens2[sens2["period"] == "validation"].reset_index(drop=True))
    g = d[(d["period"] == "validation") & (d["alpha"] == 0.99)]
    r = S.evaluate(g, "VaR_garch_evt", "ES_garch_evt", 0.99, 0.05)
    ref = C.evaluate(g["loss"].to_numpy(), g["VaR_garch_evt"].to_numpy(), g["ES_garch_evt"].to_numpy(), 0.99)
    assert all(r[k] == ref[k] for k in ("exceptions", "p_uc", "p_ind", "p_cc", "fz0", "basel_worst_count"))
    assert r["n_invalid"] == 0 and r["n_es_below_var"] == 0


def _returns(n=600, seed=0):
    rng = np.random.default_rng(seed)
    return pd.Series(rng.normal(0, 0.01, n), index=pd.bdate_range("2015-01-01", periods=n))


def test_vol_ratio_matches_hand_calculation_and_uses_only_earlier_days():
    r = _returns()
    ratio = RG.vol_ratio(r, 20, 252)
    t = 300
    hand = r.iloc[t - 20:t].std(ddof=1) / r.iloc[t - 252:t].std(ddof=1)   # days t−20 … t−1 only
    assert ratio.iloc[t] == pytest.approx(hand)
    shocked = r.copy()
    shocked.iloc[t:] *= 10                                             # day t and later change
    assert RG.vol_ratio(shocked, 20, 252).iloc[t] == pytest.approx(ratio.iloc[t])
    assert RG.vol_ratio(shocked, 20, 252).iloc[t + 1] != pytest.approx(ratio.iloc[t + 1])


def test_warm_up_and_zero_volatility_give_undefined_regime():
    r = _returns()
    ratio = RG.vol_ratio(r, 20, 252)
    assert ratio.iloc[:252].isna().all() and ratio.iloc[252:].notna().all()   # first value needs 252 earlier days
    flat = pd.Series(0.0, index=r.index)
    assert RG.vol_ratio(flat, 20, 252).isna().all()
    reg = RG.classify(ratio, 1.0)
    assert reg.iloc[:252].isna().all()
    assert RG.hist_weight(reg).iloc[:252].isna().all()
    assert np.isnan(RG.blend([1.0], [2.0], [np.nan])[0])           # never filled in
    with pytest.raises(ValueError):
        RG.vol_ratio(r, 252, 20)


def test_classification_threshold_boundary():
    ratio = pd.Series([0.5, 1.0, 1.0000001, np.nan, 2.0])
    assert RG.classify(ratio, 1.0).tolist()[:3] == ["calm", "calm", "elevated"]
    assert pd.isna(RG.classify(ratio, 1.0).iloc[3]) and RG.classify(ratio, 1.0).iloc[4] == "elevated"
    assert RG.classify(ratio, 0.4).iloc[0] == "elevated"


def test_weights_sum_to_one_and_blend_formula():
    reg = pd.Series(["calm", "elevated", "calm"])
    w = RG.hist_weight(reg, 0.7, 0.3)
    assert w.tolist() == [0.7, 0.3, 0.7]
    hist, evt = np.array([1.0, 1.0, 2.0]), np.array([3.0, 3.0, 4.0])
    out = RG.blend(hist, evt, w)
    assert out == pytest.approx([0.7 * 1 + 0.3 * 3, 0.3 * 1 + 0.7 * 3, 0.7 * 2 + 0.3 * 4])
    assert np.all((out >= np.minimum(hist, evt)) & (out <= np.maximum(hist, evt)))   # a blend stays inside the envelope
    for bad in ((1.2, 0.3), (0.7, -0.1)):
        with pytest.raises(ValueError):
            RG.hist_weight(reg, *bad)
    with pytest.raises(ValueError):
        RG.blend(hist, evt, [0.5, 1.5, 0.5])


def test_blend_keeps_es_above_var():
    rng = np.random.default_rng(3)
    vh, ve = rng.uniform(0.01, 0.02, 100), rng.uniform(0.01, 0.02, 100)
    eh, ee = vh + rng.uniform(0, 0.01, 100), ve + rng.uniform(0, 0.01, 100)
    w = rng.uniform(0, 1, 100)
    assert np.all(RG.blend(eh, ee, w) >= RG.blend(vh, ve, w))


def test_run_lengths_transitions_and_detection_delay():
    idx = pd.bdate_range("2020-01-01", periods=8)
    reg = pd.Series(["calm", "calm", "elevated", "elevated", "elevated", "calm", np.nan, "calm"], index=idx, dtype=object)
    runs = RG.run_lengths(reg)
    assert runs["state"].tolist() == ["calm", "elevated", "calm"] and runs["days"].tolist() == [2, 3, 2]
    d = RG.diagnostics(reg)
    assert d["transitions"] == 2 and d["undefined_days"] == 1 and d["share_elevated"] == pytest.approx(3 / 7)
    assert RG.detection_delay(reg, idx[0]) == 2 and RG.detection_delay(reg, idx[3]) == 0
    assert np.isnan(RG.detection_delay(reg, idx[5])) and np.isnan(RG.detection_delay(reg, pd.Timestamp("2030-01-01")))


def test_daily_scores_average_to_the_coverage_scores():
    rng = np.random.default_rng(1)
    loss = rng.standard_t(4, 3000) * 0.01
    var, es = np.full(3000, 0.03), np.full(3000, 0.04)
    for a in (0.95, 0.99):
        assert RG.daily_tick(loss, var, a).mean() == pytest.approx(C.quantile_loss(loss, var, a))
        assert RG.daily_fz0(loss, var, es, a).mean() == pytest.approx(C.fz0(loss, var, es, a))
    assert np.isnan(RG.daily_fz0([0.01], [0.02], [-0.01], 0.99)[0])   # ES ≤ 0: undefined, not scored


def test_block_bootstrap_is_reproducible_and_centred():
    x = np.r_[np.full(500, 1.0), np.full(500, -1.0)]
    a, b = RG.block_bootstrap_means(x, 63, 2000, 42), RG.block_bootstrap_means(x, 63, 2000, 42)
    assert np.array_equal(a, b) and len(a) == 2000
    assert abs(a.mean() - x.mean()) < 0.05
    assert np.allclose(RG.block_bootstrap_means(np.full(100, 2.0), 63, 50), 2.0)


def test_blend_on_backtest_components_is_reproducible_and_does_not_change_them():
    rng = np.random.default_rng(2)
    r = pd.DataFrame(rng.standard_t(5, (1300, 2)) * 0.01, columns=["A", "B"], index=pd.bdate_range("2010-01-01", periods=1300))
    port = {"p": pd.Series({"A": 0.6, "B": 0.4})}
    args = (r, port, r.index[1000], r.index[1060], 1000, (0.95, 0.99), ("historical", "evt"))
    f1, f2 = B.rolling_forecasts(*args), B.rolling_forecasts(*args)
    pd.testing.assert_frame_equal(f1, f2)
    alone = B.rolling_forecasts(r, port, r.index[1000], r.index[1060], 1000, (0.95, 0.99), ("historical",))
    pd.testing.assert_frame_equal(alone, f1[f1["method"] == "historical"].reset_index(drop=True))
    wide = f1[f1["alpha"] == 0.99].pivot(index="date", columns="method", values="VaR")
    ratio = RG.vol_ratio(r @ port["p"], 20, 252).reindex(wide.index)
    w = RG.hist_weight(RG.classify(ratio, 1.0))
    v = RG.blend(wide["historical"], wide["evt"], w)
    assert np.isfinite(v).all() and ratio.notna().all()               # 1,000 days of history: no warm-up gap
    loss = f1[(f1["alpha"] == 0.99) & (f1["method"] == "historical")].set_index("date")["loss"]
    assert set(np.unique((loss > v).astype(int))) <= {0, 1}
