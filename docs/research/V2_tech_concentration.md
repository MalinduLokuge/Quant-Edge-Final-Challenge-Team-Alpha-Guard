# V2 Hidden technology concentration: O6 vs lower-XLK alternatives [E]

**Status: decided 2026-10-30. O6 kept; D35 (tech-led crash stress), D36 (grouped effective contributors) and D37 (tech concentration trigger) approved and implemented in the pipeline on branch `version-2`.** O6 (D31 v2) and the memo verdict (D34) are unchanged.

**Reproduce:** `python scripts/research_v2_tech_concentration.py` (about 17 minutes) → `research_v2_tech_concentration.csv`, `research_v2_tech_concentration_weights.csv`.

## 1. Question
SPY already holds the large technology companies that make up XLK. Holding both means:
- more technology exposure than the ETF weights suggest;
- a D27 cap (no single ETF above 40% of ES) that cannot see SPY and XLK falling together.

Does a portfolio with less XLK serve the fund better, using the same CMA, the same 2.65% spending (D30), the same D6/D7/D27 limits, the D32 126-day 5-year test and the same stress tests?

## 2. Design
**Variants.** Each variant is built by the approved D26 rule on the 2026 inputs. Only one constraint is added:
- **O6:** the approved portfolio. It is re-selected here as a control and reproduces the saved weights to within 0.05 pp.
- **V1:** XLK at most 5%.
- **V2:** no XLK.
- **V3a / V3b:** D27 also applied to SPY + XLK as one group: the pair's share of 99% ES is at most 50% (V3a) or 40% (V3b).
- **V4:** no technology overweight. Technology exposure, looking through the ETFs to their holdings, is at most SPY's own technology share × the equity weight.

**Two views:**
- **(a)** The D26 rule is re-run: each variant takes its own highest return that passes every D7 test, and we compare the spending it supports.
- **(b)** Expected return is held at O6's 5.80%, and we compare risk at that return.

**Diagnostics** (no re-optimisation):
- **S1:** O6 with XLK's 10% moved into SPY.
- **S2:** XLK replaced by 1.13 × its weight in SPY (XLK's CAPM beta), with the extra taken from AGG.

**New stress test: tech-led crash.**
- The SPY loss equals D29 B: −21.6% central, −40.4% severe. The difference is that the crash is led by technology.
- Central: technology −40%, all other equities −10%. Severe: technology −65%, other equities −25%.
- AGG and GLD get no hedge credit.

**Look-through assumptions (not repo data):**
- SPY is 38.62% Information Technology. This is an SSGA figure for 2026-10-28, supplied by the team. **Checked 2026-10-30:** the ssga.com SPY fund page shows 38.40% as of 2026-10-29, and the pipeline uses that figure (`lookthrough`). O6's look-through tech becomes 17.7% (17.8% in the tables below) and the tech-led losses 9.17% / 16.73%. The rankings and the adoption-rule outcome are unchanged.
- EFA 9% and EEM 24% technology are approximate.
- A "broad tech" sensitivity adds AI-related names classified in other sectors: SPY 50%, EFA 12%, EEM 35%.

**Adoption rule** (fixed in the script before the run). A variant replaces O6 only if all four hold:
1. It passes D6, D7 (126-day 5-year test) and D27.
2. It loses less than O6 in the tech-led crash, both central and severe.
3. ES99, VaR99, maximum drawdown and the worst historical stress loss are no worse than O6's, at 0.01 pp.
4. It supports spending of at least 2.60%, the lower end of D30's "about 2.65%".

## 3. Results, view (a): D26 re-run
| | O6 | V1 XLK ≤ 5% | V2 no XLK | V3a group ≤ 50% | V3b group ≤ 40% | V4 no tech overweight |
|---|---|---|---|---|---|---|
| Weights AGG / SPY / XLK / EFA / XLE | 61.1 / 18.4 / 10.0 / 7.2 / 3.0 | 62.2 / 18.2 / 5.0 / 11.4 / 3.2 | 63.0 / 18.1 / 0 / 15.5 / 3.4 | 62.5 / 12.8 / 10.0 / 10.9 / 3.8 | 63.3 / 8.0 / 10.0 / 14.2 / 4.4 | 61.7 / 18.3 / 6.8 / 9.9 / 3.3 |
| Expected return | 5.80% | 5.73% | 5.66% | 5.75% | 5.71% | 5.77% |
| Spending (change vs O6, per year) | 2.65% | 2.58% (−$6.5k) | 2.52% (−$13.1k) | 2.60% (−$4.7k) | 2.56% (−$8.8k) | 2.62% (−$3.0k) |
| ES99 / VaR99 (1 day) | 2.10 / 1.38% | 2.07 / 1.33% | 2.05 / 1.30% | 2.07 / 1.33% | 2.04 / 1.30% | 2.09 / 1.38% |
| Max drawdown (GFC) | −23.5% | −23.7% | −23.9% | −23.7% | −23.8% | −23.7% |
| P(DD > 25%, 5y), 126-day blocks | 4.94% | 4.79% | 4.92% | 4.93% | 4.94% | 5.00% |
| SPY + XLK share of ES99 | 61.5% | 50.9% | 39.6% | 49.9% | 39.6% | 54.6% |
| Effective risk contributors: by ETF / SPY + XLK grouped | 3.86 / **2.32** | 3.73 / 2.82 | 3.11 / 3.11 | 4.51 / 2.90 | 4.41 / 3.29 | 3.87 / 2.66 |
| Tech exposure, look-through (% of fund / % of equity) | **17.8% / 46%** | 13.1 / 35% | 8.4 / 23% | 15.9 / 42% | 14.4 / 39% | 14.8 / 39% |
| Tech-led crash, central / severe | −9.2 / **−16.7%** | −7.7 / −14.7% | −6.2 / −12.6% | −8.5 / −15.7% | −8.0 / −14.9% | −8.3 / −15.5% |
| D29 B AI unwind, severe | −14.2% | −13.5% | −12.9% | −13.7% | −13.3% | −13.9% |
| 2022 rates and inflation | −17.8% | −17.3% | −17.1% | −17.3% | −17.1% | −17.4% |
| Adoption rule | (baseline) | fails 3, 4 | fails 3, 4 | fails 3 | fails 3, 4 | fails 3 |

The "broad tech" sensitivity changes the levels but not the ranking: O6's severe tech-led crash loss is −17.7%, against −15.6% (V1), −13.6% (V2) and −16.5% (V4).

**View (b), at O6's 5.80% return:** every lower-XLK variant **fails D7**. P(DD > 25%, 5y) is 5.5–9.5%, against a limit of 5%. With these return assumptions, O6's return cannot be reached within D7 without XLK at its cap.

**Diagnostics:**
- **S1** (XLK moved into SPY) breaches D27: SPY's share of ES rises above 40%.
- **S2** (beta-matched SPY) has the same expected return but higher ES99 (2.15%) and a deeper drawdown (−23.8%), and fails the 5-year test (5.23%).

## 4. Findings
1. **Under the adoption rule, O6 stays.** Every variant fails criterion 3 on the historical maximum drawdown: −0.20 to −0.42 pp worse in the GFC. V1, V2 and V3b also fail on spending.
2. **The concern is real.** O6's look-through tech exposure is 17.8% of the fund, 46% of the equity sleeve against 38.6% inside SPY itself. The new tech-led crash costs **−16.7% ($1.67M)**. That is 2.6 pp worse than our current AI scenario (D29 B severe, −14.2%) and the second-worst hypothetical after A severe (−18.9%). It stays within the 25% stress limit.
3. **The data are blind to this risk.** In 2004–26, XLK *helped*: the GFC was led by financials, not tech. Replacing XLK with beta-matched SPY (S2) worsens every historical tail measure. Any rule calibrated on this sample (D7, D27, ES caps) will favour XLK. The sample contains no tech-led crash; 2000–02 ended before it starts.
4. **D27 hides the risk.** Grouping SPY and XLK, O6 has **2.3** effective risk contributors, not the 3.9 counted by ETF. Applying D27 to the group (V3) is the wrong tool. It keeps XLK at 10% (higher CAPM return) and cuts SPY, so look-through tech barely falls (17.8% → 15.9%).
5. **The cheapest real protection is V4 (no tech overweight).** It costs $3.0k a year in spending (2.65% → 2.62%) and makes the GFC drawdown 0.24 pp worse. In return, the severe tech-led crash loss falls by 1.2 pp ($123k). V1 halves XLK for $6.5k a year and saves 2.1 pp ($208k).

## 5. Team decision (APPROVED 2026-10-30: keep O6, adopt D35–D37)
- **D35 (stress test):** add the tech-led crash to the hypothetical set and report it in the memo and report. No portfolio change.
- **D36 (disclosure):** report effective risk contributors with SPY + XLK grouped (2.3) next to the per-ETF figure, and qualify D27's "1.7 → 3.8" claim.
- **D37 (monitoring, D23 ladder):** look-through tech above 20% of the fund triggers a committee review, with V4 as the pre-agreed fallback.
- **Alternative to the rule:** the committee may still choose V4 as insurance against a tech-led crash, accepting a −0.24 pp historical drawdown. That needs an explicit override of criterion 3 and would reopen D31 v2 / D34 and the outputs snapshot.

## 6. Limitations
- Look-through shares are assumptions. The SPY figure is unverified, and EFA/EEM are approximate.
- The tech-led crash is an instant shock with no hedge credit for AGG or GLD. Being designed rather than estimated, it does not compare the variants neutrally.
- Only the 2026 inputs were used. Out-of-sample checks on 2014 inputs were not run, because O6's walk-forward validation (T20.07) already covers the rule.
