# V2 Gold weight vs the gold expected-return assumption (review item G-12) [E]

**Reproduce:** `python scripts/research_v2_gold_return.py` → `outputs/tables/research_v2_gold_return.csv` (about 25 min).

**Question (external QA review):** O6 holds 0.4% gold, while research §7 (D3_D7) concluded that the evidence supports a 5–15% role, and the tear sheet called the 0.4% a "crisis hedge". Is the 0.4% an artifact of CAPM giving gold about 4.6% (β ≈ 0)?

## Method
- The approved D26 rule (D6, D7, D27 cap, D32 5-year test) is re-run on the full-sample CMA, the same as `candidates.build("full")`. **Only GLD's expected arithmetic return is changed.**
- **Reproduction:** the CAPM case reproduces O6 exactly (GLD 0.39%, AGG 61.05%, P 4.94%).
- **Fair scoring:** every portfolio is scored under the **base** CMA as well as under its own case, so a higher gold assumption cannot raise its own score.
- **Cases:**
  - zero real return (Erb & Harvey 2013): breakeven 2.35% + σ²/2 = 4.0% arithmetic;
  - CAPM, 4.6%;
  - CAPM + 0.5 / 1 / 2 / 4 pp;
  - the 2004–26 sample mean, 11.5% (in-sample: one gold cycle).

## Results

| Gold E[R] (arith.) | GLD | AGG | E[R] geo, base CMA | Spending supported | P(DD > 25%, 5y), base CMA | 2022 | Stagflation severe | GFC |
|---|---|---|---|---|---|---|---|---|
| 4.0% zero real (Erb–Harvey) | 0.0% | 61.6% | 5.79% | 2.64% | 4.8% | −17.8% | −18.8% | −23.4% |
| **4.6% CAPM (O6)** | **0.4%** | **61.1%** | **5.80%** | **2.65%** | **4.9%** | **−17.8%** | **−18.8%** | **−23.5%** |
| 5.1% (+0.5 pp) | 4.7% | 56.6% | 5.81% | 2.66% | 5.0% | −17.6% | −18.7% | −23.3% |
| 5.6% (+1 pp) | 9.2% | 53.0% | 5.79% | 2.64% | 4.9% | −17.3% | −18.5% | −23.1% |
| 6.6% (+2 pp) | 18.0% | 45.8% | 5.72% | 2.58% | **5.3%** | −16.9% | −18.0% | −23.5% |
| 8.6% (+4 pp) | 20.0% (cap) | 43.6% | 5.73% | 2.58% | **5.9%** | −16.9% | −17.9% | −23.8% |
| 11.5% historical (in-sample) | 20.0% (cap) | 43.1% | 5.74% | 2.59% | **6.3%** | −16.9% | −18.0% | −24.1% |

All columns are in the CSV.

## Reading
1. **The friend is right that the weight depends on the assumption.** Each extra percentage point assumed for gold adds about 9 pp of gold. A modest premium (+0.5 to +1 pp) gives a 5–9% gold weight.
2. **The literature does not support a premium.** At a zero real return (Erb & Harvey 2013), gold drops to 0%. The only case with a large gold weight needs gold to beat CAPM by 2 pp or more a year, or uses the in-sample 2004–26 history.
3. **More gold buys almost no protection inside the D7 frame.** Gold replaces AGG, not equities: SPY rises slightly and XLK stays at its cap. At 18–20% gold, the 2022 loss improves by 0.9 pp, stagflation by 0.8 pp, and the GFC loss slightly worsens.
4. **Under our base assumptions, large gold weights fail D7.** The 5-year drawdown probability is 5.3–6.3% against the 5% limit, and supportable spending falls to 2.58%. These portfolios meet D7 only if one believes the gold premium that produced them.
5. **The 5–9% range (+0.5 to +1 pp) is a matter of judgment.** It changes expected return and risk by under 0.02 pp and 0.1 pp. That is consistent with T4_25: the O4 5% floor had no robust edge, and its 2020–26 gain came from one gold cycle.

## Decisions on the wording (no portfolio change; D43, PROPOSED)
- **Tear sheet:** the 0.4% is described as a "residual weight from the optimiser; too small to hedge, no hedge credit taken" (was "crisis hedge").
- **Research §7 (D3_D7):** marked as superseded for the final portfolio by the O4 test and this run.
- **Report §4.5:** this result and the mixed literature. **Report §10 and Assumptions & Limitations:** O6 has no effective inflation hedge (XLE 3.0%, GLD 0.4%; −17.8% in 2022, −18.8% in severe stagflation). The committee accepts this risk through D7 and the D23 ladder.
- **Not changed:** O6, CAPM for gold (D12), D6 (gold 0–20%), D7, D24 at 2.65%, D34.

## Literature
- Baur, D. G. & Lucey, B. M. (2010). Is gold a hedge or a safe haven? *Financial Review* 45(2). On average gold is a hedge for stocks and a safe haven in extreme falls, but only for about 15 trading days.
- Erb, C. B. & Harvey, C. R. (2013). The golden dilemma. *Financial Analysts Journal* 69(4). Gold is an unreliable inflation hedge over practical horizons. Its real return is near zero in the long run, and its high real price predicts low future real returns.

## Limitations
- This is a one-input sensitivity; gold's covariance, the stress betas and the other assets' expected returns are kept.
- The 5-year test uses 32,000 paths (s.e. about 0.12 pp at 5%). The 5.0% at +0.5 pp is at the limit within Monte Carlo noise.
