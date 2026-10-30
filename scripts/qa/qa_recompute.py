"""Independent QA recomputation: raw prices -> returns -> key published numbers, without project functions."""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

R = str(Path(__file__).resolve().parents[2])  # repo root
out = {}
raw = pd.read_csv(R + r"\data\raw\yahoo_adj_close_2026-10-20.csv", index_col=0, parse_dates=True)
px = raw.loc["2004-11-18":"2026-10-19"].dropna()
ret = px.pct_change().dropna()
proc = pd.read_csv(R + r"\data\processed\simple_returns.csv", index_col=0, parse_dates=True)
out["returns: max abs diff raw→processed"] = float((ret[proc.columns].reindex(proc.index) - proc).abs().max().max())
out["returns: rows raw / processed"] = (len(ret), len(proc))

w = pd.read_csv(R + r"\outputs\tables\p1_final_weights.csv", index_col=0).loc["d26_selected"]
print("weights", w.round(4).to_dict(), "sum", round(w.sum(), 10), "min", w.min())
rp_const = proc @ w
loss = -rp_const.to_numpy()
for a in (0.95, 0.99):
    v = np.quantile(loss, a); e = loss[loss >= v].mean()
    out[f"hist VaR/ES {a} (constant weights)"] = (round(v, 5), round(e, 5))
# normal parametric
mu, sd = loss.mean(), loss.std(ddof=1)
for a in (0.95, 0.99):
    z = stats.norm.ppf(a); out[f"normal VaR/ES {a}"] = (round(mu + sd * z, 5), round(mu + sd * stats.norm.pdf(z) / (1 - a), 5))
# quarterly rebalanced path, own implementation
q = proc.index.to_period("Q"); last = np.r_[q[1:] != q[:-1], False]
h, nav, path = w.to_numpy().copy(), 1.0, []
for t, r in enumerate(proc.to_numpy()):
    g = h * (1 + r); nav *= g.sum(); h = g / g.sum(); path.append(nav)
    if last[t]: h = w.to_numpy().copy()
path = pd.Series(path, index=proc.index)
out["max drawdown quarterly-rebalanced"] = round(float((path / path.cummax() - 1).min()), 5)
gfc = path.loc["2007-10-09":"2009-03-09"]; g0 = path.loc[:"2007-10-08"].iloc[-1]
gn = gfc / g0; out["GFC window worst peak-to-trough"] = round(float((gn / np.maximum.accumulate(np.maximum(gn, 1)) - 1).min()), 5)
# expected return
cma = pd.read_csv(R + r"\outputs\tables\cma_full.csv", index_col=0).reindex(proc.columns)
cov = pd.read_csv(R + r"\outputs\tables\cma_full_cov_shrunk.csv", index_col=0).loc[proc.columns, proc.columns].to_numpy()
wv = w.reindex(proc.columns).to_numpy()
capm = 0.041 + cma["beta"] * 0.05; capm["AGG"] = cma.loc["AGG", "ttm_yield"]
out["CAPM check max diff"] = float((capm - cma["expected_arithmetic"]).abs().max())
exp = float(capm.to_numpy() @ wv - 0.5 * wv @ cov @ wv); out["expected compound return"] = round(exp, 5)
req = 1.0235 * 1.0265 * 1.005 * 1.002 - 1; out["required return at 2.65%"] = round(req, 5)
out["sustainable spending"] = round((1 + exp) / (1.0235 * 1.005 * 1.002) - 1, 5)
# beta check of SPY-based CAPM beta for one ETF (monthly excess returns vs SPY)
# Kupiec / Christoffersen for GARCH-EVT test, from the saved forecasts
fc = pd.read_csv(R + r"\outputs\tables\backtest_forecasts_test.csv", parse_dates=["date"])
f = fc[(fc.portfolio == "d26_selected") & (fc.method == "garch_evt") & (fc.alpha == 0.99)].sort_values("date")
e = (f["loss"] > f["VaR"]).astype(int).to_numpy(); n, x = len(e), e.sum(); p = 0.01; ph = x / n
lr = -2 * ((n - x) * np.log(1 - p) + x * np.log(p) - (n - x) * np.log(1 - ph) - x * np.log(ph))
out["Kupiec GARCH-EVT test: n, x, LR, p"] = (n, int(x), round(lr, 4), round(stats.chi2.sf(lr, 1), 4))
counts = np.convolve(e, np.ones(250, int), "valid"); out["Basel worst 250d count"] = int(counts.max())
# look-ahead check: forecast on first test day must not depend on that day's loss -> compare with a recompute of historical VaR
fh = fc[(fc.portfolio == "d26_selected") & (fc.method == "historical") & (fc.alpha == 0.99)].sort_values("date")
wt = pd.read_csv(R + r"\outputs\tables\p1_train_weights.csv", index_col=0).loc["d26_selected"].reindex(proc.columns).to_numpy()
d0 = fh["date"].iloc[0]; i0 = proc.index.get_loc(d0)
L = -(proc.to_numpy()[i0 - 1000:i0] @ wt)
out["historical VaR recompute (first test day): saved vs mine"] = (round(fh["VaR"].iloc[0], 6), round(float(np.quantile(L, 0.99)), 6))
out["realised loss first test day saved vs mine"] = (round(fh["loss"].iloc[0], 6), round(float(-(proc.to_numpy()[i0] @ wt)), 6))
# diversification benefit (not in the project): standalone vs portfolio ES99 / VaR99
stand_var = sum(wv[j] * np.quantile(-proc.iloc[:, j], 0.99) for j in range(7))
stand_es = 0.0
for j in range(7):
    l = -proc.iloc[:, j].to_numpy(); v = np.quantile(l, 0.99); stand_es += wv[j] * l[l >= v].mean()
out["undiversified VaR99 / ES99 (sum of weighted standalone)"] = (round(stand_var, 5), round(stand_es, 5))
out["diversification benefit VaR99 / ES99"] = (round(1 - np.quantile(loss, 0.99) / stand_var, 4), round(1 - loss[loss >= np.quantile(loss, 0.99)].mean() / stand_es, 4))
# 5y drawdown test independent seeds
mu_d = cma["expected_arithmetic"].to_numpy() / 252
X = proc.to_numpy() + (mu_d - proc.to_numpy().mean(0))
rng = np.random.default_rng(12345); hits = 0; N = 16000
for b in range(4):
    st_ = rng.integers(0, len(X) - 126, size=(4000, 10))
    idx = (st_[:, :, None] + np.arange(126)).reshape(4000, -1)[:, :1260]
    nv = np.cumprod(1 + X[idx] @ wv, axis=1); hits += ((nv / np.maximum.accumulate(nv, 1) - 1).min(1) < -0.25).sum()
out["P(DD>25%,5y) 126-day blocks, independent seed, 16k paths"] = round(hits / N, 4)
for k, v in out.items():
    print(f"{k}: {v}")
