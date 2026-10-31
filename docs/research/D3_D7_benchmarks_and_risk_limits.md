# D3 Benchmarks & D7 Risk Limits: Research Findings (2026-10-28)

**Reproduce:** `python run_all.py --only data`, then `--only portfolio`, then `python scripts/research_d3_d7.py` → `outputs/tables/research_d3d7_*.csv`.
**Labels:** **[E]** evidence (our data or a cited source) · **[A]** assumption · **[P]** provisional recommendation · **[O]** open (cannot be finalised yet).
**Scope warning [E]:** all portfolio statistics are *historical, in-sample* (Nov 2004 – Oct 2026, one path that includes 2008). They describe what happened, not what will happen. Expected returns are CAPM estimates (ERP 5%, risk-free 4.10%, D12).

---

## 1. Benchmark comparison (D3)

### 1.1 Three different jobs, not one benchmark
| Role | Used for | Requirement |
|---|---|---|
| CAPM market proxy | β, Treynor, Jensen's α | Broad market portfolio; brief p.7 requires CAPM |
| Primary policy benchmark | Information Ratio, tracking error, "did optimisation add value?" | Same risk profile and asset classes as the mandate; specified in advance; investable |
| Secondary comparisons | Context for the committee | Conventional, easy to understand |

Professional standard [E]: a valid benchmark is **Specified in advance, Appropriate, Measurable, Unambiguous, Reflective of current opinion, Accountable, Investable** ("SAMURAI", Bailey & Tierney; CFA curriculum). See [AnalystPrep](https://analystprep.com/study-notes/cfa-level-iii/test-of-benchmark-quality-2/) and [abrdn](https://abrdn.com/en-us/institutional/insights-and-research/the-way-of-the-samurai). "Appropriate" is where the current proposal fails.

### 1.2 Candidates, quarterly rebalanced, total return [E]
| Benchmark | CAGR | Vol | Sharpe | Max DD | 1-day ES99 | GFC | COVID | 2022 | FY2009 | Exp. return (CAPM) |
|---|---|---|---|---|---|---|---|---|---|---|
| 60/40 SPY/AGG | 8.00% | 11.2% | 0.59 | −35.0% | 3.01% | −34.7% | −20.8% | −20.4% | −13.2% | 6.80% |
| 40/60 SPY/AGG | 6.39% | 8.0% | 0.60 | −22.9% | 2.13% | −22.4% | −14.4% | −18.6% | −6.7% | 6.07% |
| Global 60/40 (SPY 37/EFA 16/EEM 7/AGG 40) | 7.11% | 11.6% | 0.50 | −36.9% | 3.11% | −36.0% | −20.2% | −21.3% | −13.8% | 6.76% |
| Global 40/60 | 5.81% | 8.2% | 0.52 | −24.5% | 2.16% | −23.5% | −14.0% | −19.2% | −7.0% | 6.04% |
| **Policy 40/50/10** (SPY 25/EFA 10/EEM 5/AGG 50/GLD 10) | 6.65% | 8.5% | 0.59 | −25.3% | 2.18% | −22.1% | −14.1% | −18.6% | −7.6% | 6.03% |
| Equal weight 7 | 9.91% | 15.5% | 0.58 | −42.8% | 4.05% | −38.7% | −26.0% | −14.3% | −20.2% | 7.13% |
| SPY | 10.91% | 18.8% | 0.55 | −55.2% | 5.05% | −54.8% | −33.4% | −24.1% | −26.2% | 8.02% |

Turnover from quarterly rebalancing is 6–10% a year for every blend. At 1–5 bp spreads the cost is under 0.01% a year, so it's negligible [E, A for the spread].

### 1.3 Assessment of the current proposal (SPY / 60/40 / equal-weight)
- **SPY as the CAPM proxy: keep [P].** It's the only broad-market ETF in the universe, the standard proxy, and our betas use it. Caveat: it's US-only, so EFA/EEM betas (0.96/1.04) understate global risk. Robustness check: recompute betas against a global equity mix.
- **60/40 as the primary (IR) benchmark: replace [P].** It fails "Appropriate": its −35% drawdown and 3.0% ES are far beyond what we'd allow the portfolio, so a conservative portfolio would show a large "negative alpha" just for being conservative. That is an unfair comparison. It also leaves out international equity and gold. **Keep it as a secondary benchmark**: it's the yardstick a committee knows.
- **Equal weight 7 as secondary: keep [P].** It's the standard test of whether optimisation beats naive 1/N diversification (DeMiguel, Garlappi & Uppal, *Review of Financial Studies*, 2009). It is not a policy benchmark: its 43% drawdown and sector bets don't fit the mandate.

### 1.4 Recommended structure [P]
| Role | Benchmark | Why |
|---|---|---|
| CAPM market proxy | **SPY** | Required for β, Treynor, Jensen's α |
| **Primary policy benchmark** | **Policy 40/50/10:** 40% global equity (SPY 25 / EFA 10 / EEM 5 ≈ world market-cap split 62/25/13), 50% AGG, 10% GLD; quarterly rebalance; total return | Matches a conservative risk level (ES 2.2%, DD −25%), covers every *asset class* in the universe, investable and specified in advance. Sector ETFs (XLE, XLK) are excluded because they are active tilts inside SPY, not asset classes |
| Secondary 1 | 60/40 SPY/AGG | Conventional yardstick |
| Secondary 2 | Equal weight 7 | Does optimisation add value beyond 1/N? |
| Simpler alternative | 40/60 SPY/AGG | Nearly identical risk to Policy 40/50/10; use it if the team prefers simplicity over asset-class coverage |

**Integrity rule [P]:** the policy weights come from market-cap proportions and the mandate (bond-heavy, 10% real asset), **not** from the best historical result. Freeze them in config before running any optimisation (SAMURAI "specified in advance").

---

## 2. Risk-limit analysis (D7)

### 2.1 Separate four kinds of limit [P]
| Tier | Measure | Purpose | How to set it |
|---|---|---|---|
| Long-term loss tolerance | **Max drawdown, from peak** | Protect spending and the fund's real value | Client choice, traded off against supported spending (§4) |
| Construction limit | **1-day ES 99% (and 97.5%) on full-cycle history** | Statistical tail limit used in optimisation | Calibrated from stressed history; consistent with the drawdown tolerance |
| Scenario limit | **Loss in each stress scenario** (2008, Mar-2020, 2022, hypothetical) | "How bad could it get?" (brief p.5) | ≤ drawdown tolerance |
| Structure | Weight caps (D6); **no ETF > X% of portfolio ES** (component ES) | Diversification and robustness | Set after the risk stage gives component ES |
| Monitoring (not a limit) | Rolling 250-day ES, VaR exceptions | Early warning: review, not forced selling | Trigger review when rolling ES > construction limit |

VaR stays as the **backtesting and monitoring** measure (brief p.7). ES is the better limit because it is coherent (Artzner et al., 1999) and is what Basel's market-risk framework (FRTB) moved to: 97.5% ES replacing 99% VaR ([BPI explainer](https://bpi.com/why-is-the-frtb-expected-shortfall-calculation-designed-as-it-is/)) [E]. Volatility is reported but not used as a limit, because it says nothing about crash severity.

### 2.2 Why the window matters for an ES limit [E]
Rolling 250-day 1-day ES99 for **Policy 40/50/10** ranges **0.5% to 4.5%** (median 1.4%) and is above 2.5% on 10% of days. For 60/40 the range is 0.9–5.6%, above 2.5% on 26% of days. An "always ≤ 2.5%" rule on a rolling estimate would force selling during every crisis, which is pro-cyclical and harmful. **So the ES limit must apply to a full-cycle (stressed) estimate at construction**, and the rolling figure is only a review trigger.

### 2.3 Are 20% drawdown / 2.5% ES the right levels?
- **Peer evidence [E]:** the average US endowment returned **−18.7% in FY2009** (NACUBO-Commonfund, [PlanSponsor](https://www.plansponsor.com/study-confirms-tough-year-for-endowments/)). On that *same fiscal-year basis*, 60/40 lost 13.2% and Policy 40/50/10 lost 7.6%. Fiscal-year losses are much smaller than peak-to-trough drawdowns (−35% / −25%), so **always compare like with like**.
- **What the universe allows [E]:** no tested blend with meaningful equity stays within 20% through 2008. 40/60 reached −22.9% and Policy 40/50/10 −25.3%. A 20% limit forces roughly ≤ 30–35% equity-like exposure.
- **ES 2.5% [E]:** consistent with a ~25% drawdown tolerance. In the feasibility search, ES ≤ 2.5% does not bind once DD ≤ 25% (§4), so the two limits don't conflict. ES limits below 2.0% start to bind.
- **Verdict [P]:** 20% is achievable but **too restrictive for the return objective** (§4). 25% (peak-to-trough, including a 2008 replay) with **ES99 ≤ 2.5%** is the most defensible provisional pair. **Final values [O]** depend on the committee's choice between drawdown and spending (§4) and on the forward-looking drawdown probabilities (§3, gap G1).

---

## 3. Data gaps [O]
| # | Missing | Why / which decision | Source / method | Available? |
|---|---|---|---|---|
| G1 | **Forward-looking drawdown probabilities**, e.g. P(DD > 25% within 5 years) | History is one path; limits need probabilities (D7) | Block bootstrap / Monte Carlo of our ETF returns (risk stage) | Data yes, calculation no |
| G2 | Longer crisis history (2000–02 dot-com, 1994 bonds) | 2008 may not be the worst case | Disclosed proxies: SPY and XLK exist from 1993/1998; AGG proxy from FRED DGS10 duration model; gold has no approved pre-2004 source | Partial |
| G3 | Hypothetical scenario (D9) | Scenario limit | Factor shocks via SPY and DGS10 betas | Not started |
| G4 | Component ES per ETF | Risk-contribution limit | Risk stage, Euler allocation | Not started |
| G5 | Client liquidity need | Liquidity rule | Assumption: 4% × $10M = $0.4M a year; AGG at 40–50% covers more than 10 years | [A] |
| G6 | Spending-rate source | D12 | NACUBO FY2024 average effective spending **4.8%**, FY2025 4.9% ([NACUBO tables](https://edge.sitecorecloud.io/nacubo1-nacubo-prd-dc8b/media/Nacubo/Documents/EndowmentFiles/2024-NCSE-Public-Tables--Spending-Rates-FINAL.pdf), [FY2025 summary](https://edge.sitecorecloud.io/nacubo1-nacubo-prd-dc8b/media/Nacubo/Documents/EndowmentFiles/2025-NCSE---Summary-and-Key-Insights-from-the-2025-NCSE-FINAL.pdf)); cite as context, not a data input | [E] |
| G7 | Expected-return uncertainty in the frontier | Feasibility depends on ERP | Rerun the feasibility search at ERP 3–6% (and a resampled frontier) | Data yes |
| G8 | Out-of-sample check of the limits | In-sample limits are optimistic | Set limits on the training window (D5), check on the test window | Blocked by D5 |

---

## 4. Return–risk compatibility (D7 × D12) [E with the stated assumptions]
Highest CAPM expected compound return (ERP 5%) among 50,000 long-only portfolios that respect each historical limit pair:

| Max drawdown limit | ES99 ≤ 2.5%, no caps | ES99 ≤ 2.5%, with draft D6 caps | Spending supported (with caps)* |
|---|---|---|---|
| 20% | 5.74% | **5.27%** | **2.1%** |
| 25% | 6.31% | 6.00% | 2.8% |
| 30% | 6.36% (ES binds; 6.64% at ES 3.0%) | 6.21% (6.58% at ES 3.0%) | 3.0% (3.4%) |
| 35% | 6.36% (7.01% at ES 3.5%) | 6.21% (6.81% at ES 3.5%) | 3.0% (3.6%) |

\*Keeps inflation, 0.5% real growth and 0.2% costs: S* = (1+E)/((1+I)(1+G)(1+C)) − 1.

What it takes to meet each D12 tier (lowest historical risk among portfolios that meet it):
| Tier | Without caps | With draft D6 caps |
|---|---|---|
| Minimum 6.66% | DD ≈ 31%, ES99 ≈ 2.8% | DD ≈ 32%, ES99 ≈ 3.0% |
| Target 7.19% | DD ≈ 37%, ES99 ≈ 3.6% | **Not achievable** |

**Conclusion [E]: D7 as drafted (20% DD, 2.5% ES) and D12 (6.66–7.19%) cannot both be met.** Meeting even the minimum needs roughly 60/40-level risk (about −31% drawdown), which contradicts "avoid large losses". Under the agreed policy (lower spending, not more risk), the honest options for the committee are:
- **Drawdown 20%:** supports about 2.1% spending.
- **Drawdown 25%:** supports about 2.8% spending.

Both are well below 4% and the NACUBO average of 4.8%. **This conflict is the central finding for the memo** (brief p.4 #5, p.8 "adjust the risk limit").

Caveats [A]: CAPM values gold at ~4.6% (it ignores its hedge value) and rewards only beta, so the search favours XLK (high β) inside the caps. A higher ERP shifts all values up by about 0.4 pp per 1 pp of ERP. Historical drawdowns are one path and in-sample. The draft D6 satellite cap (≤ 10% each) costs about 0.3–0.5 pp of expected return. It is still recommended, because the uncapped optimum concentrates 24–27% in XLK, which is unsuitable.

---

## 4b. Forward-looking drawdown probabilities (gap G1, closed 2026-10-28) [E with assumptions]
5,000 five-year paths from a moving-block bootstrap (63-day blocks) of daily ETF returns, each ETF's mean reset to its CAPM expectation (ERP 5%). Reproduce with `python scripts/research_d3_d7.py --g1` → `research_d7_forward_drawdowns.csv`.

| Portfolio | Median max DD | Worst 5% of paths | P(DD > 20%) | P(DD > 25%) | P(DD > 30%) | P(5-yr return < inflation) |
|---|---|---|---|---|---|---|
| Best within 20% DD (caps): AGG 40 / GLD 37 / SPY 9 / XLK 9 / EFA 4 / XLE 1 | −13.3% | −24.0% | 12.6% | 3.9% | 1.0% | **18.9%** |
| Best within 25% DD (caps): AGG 39 / SPY 27 / GLD 22 / EFA 5 / XLK 5 / EEM 1 | −13.3% | −24.8% | 19.0% | 4.9% | 1.4% | 14.0% |
| Best within 30% DD (caps) | −14.2% | −26.3% | 23.5% | 6.9% | 2.2% | 13.6% |
| Policy 40/50/10 | −12.9% | −24.7% | 20.7% | 4.7% | 1.4% | 13.3% |
| 40/60 SPY/AGG | −13.1% | −23.3% | 12.7% | 3.1% | 0.8% | 11.0% |
| 60/40 SPY/AGG | −17.8% | −31.8% | 41.1% | 19.7% | 7.0% | 14.5% |

Findings:
- **A historical 20% limit is not a 20% guarantee:** even the strictest portfolio has a 12.6% chance of a deeper drawdown within 5 years.
- **Tightening to 20% *raises* the risk of losing purchasing power** (18.9% vs 14.0%). It pushes the optimiser into gold (37%), which is volatile and has a low CAPM expected return.

Drawdown tolerance should therefore be stated as a probability, e.g. "historical ≤ 25% including 2008 **and** P(DD > 25% within 5 years) ≤ 5%".

## 5. Final recommendations
| Decision | Recommendation | Status |
|---|---|---|
| D3 market proxy | SPY (robustness: global-equity beta) | [P] ready to approve |
| D3 primary benchmark | Policy 40/50/10 (SPY 25 / EFA 10 / EEM 5 / AGG 50 / GLD 10), quarterly, total return; frozen before optimisation | [P] ready to approve |
| D3 secondary | 60/40 SPY/AGG and Equal weight 7 | [P] ready to approve |
| D7 drawdown tolerance | **25%** peak-to-trough including a 2008 replay (20% as a stricter alternative, with 2.1% spending) | [P], final after G1 and the committee's spending choice |
| D7 construction ES | **1-day ES99 ≤ 2.5% NAV ($250k)** on full-cycle history; also report ES97.5 | [P] |
| D7 scenario limit | Every stress scenario loss ≤ drawdown tolerance | [P] |
| D7 risk contribution | No ETF > 40% of portfolio ES (value to confirm after G4) | [O] |
| D7 monitoring | Rolling 250-day ES above the limit and Basel yellow/red trigger a review, not a forced sale | [P] |
| D7 liquidity | Keep at least 2 years of spending (≥ 8% NAV) in AGG | [P] |
| D12 interaction | Present the drawdown ↔ spending trade-off table (§4) to the committee; do not force 6.66% | [P] |

Implementation: `config/settings.yaml` gets `benchmarks` and `risk_limits` blocks. The optimiser uses the DD/ES/D6 limits. KPI code uses SPY for CAPM and Policy 40/50/10 for IR. The memo uses the §4 table.

## 5b. D5 data split and D6 weight caps (2026-10-28)

### D5 split options [E]
| Option | Train | Validation | Test | Validation: expected 99% exceptions | Test: exceptions / Basel windows | Test regime |
|---|---|---|---|---|---|---|
| A | 2004-11 → 2016 (3,050 days) | 2017–19 (754) | 2020 → 2026-10 (1,708) | 7.5 | 17.1 / 6 | COVID, 2022, 2025 |
| **B (recommended)** | 2004-11 → 2014 (2,546) | **2015–19 (1,258)** | 2020 → 2026-10 (1,708) | **12.6** | 17.1 / 6 | COVID, 2022, 2025 |
| C | 2004-11 → 2012 (2,042) | 2013–17 (1,259) | 2018 → 2026-10 (2,211) | 12.6 | 22.1 / 8 | adds 2018 |

- B keeps 2008 in training and gives validation 68% more exceptions than A, so model selection (VaR method, EVT threshold, GARCH spec, window length) has more statistical power.
- B tests on an **unseen regime**: SPY–AGG correlation is +0.19 in 2020–26, against −0.10 in training. Every validation option is calm (SPY volatility ~13%); that is a known limitation.
- The 1,000-day VaR window (D13) has enough history before 2015.
- **Protocol:** methods and settings are frozen on train + validation, and the test set is used once. Final client weights are re-estimated on the full sample with the frozen method (decision as of 2026-10-19).

### D6 cap designs under the approved D7 limits (hist. DD ≤ 25%, ES99 ≤ 2.5%) [E]
Reproduce: `python scripts/research_d3_d7.py --d6` → `research_d6_cap_designs.csv`.

| Design | Share of random portfolios feasible | Best expected return | Best portfolio | Top-50 avg GLD / XLK |
|---|---|---|---|---|
| Draft (each ≤ 40%, AGG+GLD ≥ 40%, satellites ≤ 10% each / 25% total) | 6% | 6.06% | AGG 39 / SPY 36 / GLD 20 | 25% / 4% |
| **Policy ranges** (equity 25–55%, AGG 30–60%, GLD ≤ 20%, SPY ≤ 40%, EFA ≤ 20%, EEM/XLE/XLK ≤ 10% each, ≤ 20% together) | **39%** | **6.28%** | AGG 55 / SPY 33 / XLK 7 | 3% / 4% |
| Policy ranges, sector tilts ≤ 15% | 33% | 6.31% | AGG 55 / SPY 27 / XLK 14 | 3% / 9% |
| Long-only, AGG ≥ 8% only | 6% | 6.26% | AGG 58 / XLK 26 / EFA 7 | 4% / 19% |

- The draft caps **contradict the benchmark** (AGG ≤ 40% while the policy benchmark holds 50%) and push the optimiser into gold (25%).
- Policy ranges around the D3 benchmark are standard institutional practice (strategic allocation ± bands). They give the **same return as no caps (6.28% vs 6.26%) without the 26% XLK concentration**, and six times the feasible region.
- Sustainable spending rises from about 2.8% (draft caps) to about **3.1%**.

## 5c. D6 v2: constraints derived from the mandate, calibrated on data (supersedes the §5b options)

**Principle.** Every constraint must answer "which client risk does this control?" before any backtest is run. Data calibrates the level; it does not choose the rule. Two kinds of constraint do different jobs:
- **Weight constraints** (this section): governance rules that protect against estimation error and concentration. Simple, explainable, set in advance.
- **Risk limits** (D7: drawdown, ES, stress): outcome limits that the optimiser must satisfy.

The client has **two** risks that pull in opposite directions:
- **Large-loss risk:** a drawdown that forces spending cuts.
- **Purchasing-power risk:** returns too low to beat inflation, which slowly erodes the endowment.

Reproduce: `python scripts/research_d3_d7.py --d6b` → `research_d6_allocation_sweeps.csv`.

**Sweep A: equity share** (global equity mix SPY/EFA/EEM 62.5/25/12.5, gold 10%, rest AGG; 4,000 five-year bootstrap paths with CAPM means) [E]:

| Equity | Hist. max DD (full = train) | ES99 | CAPM exp. return | P(DD > 25%, 5y) | P(5-yr return < inflation) |
|---|---|---|---|---|---|
| 10% | −17.2% | 1.3% | 4.8% | 0.2% | 13.8% |
| **20%** | −17.7% | 1.5% | 5.2% | 0.5% | **12.4% (lowest)** |
| 30% | −20.8% | 1.9% | 5.6% | 2.0% | 12.6% |
| **40%** | −25.3% | 2.3% | 6.0% | **5.3%** | 14.0% |
| 50% | −30.2% | 2.8% | 6.4% | 14.3% | 15.8% |
| 60% | −35.4% | 3.3% | 6.7% | 25.8% | 17.2% |

**Sweep B: gold share at 40% equity (gold replaces AGG)** [E]: gold 0% → 30% moves historical drawdown from −24.5% to −27.6%, P(DD > 25%) from 4.8% to 10.6%, and P(5-yr return < inflation) from 13.0% to 18.0%. Expected return stays flat at about 6.0%. In this sample and under CAPM, gold **does not** reduce either risk when it replaces bonds. Its case is a hedge against regimes this sample barely contains: high inflation, and stocks and bonds falling together (as in 2022).

**Correlations with SPY [E]:** XLK 0.91 (mostly duplicates SPY's mega-caps), EFA 0.88, EEM 0.82, XLE 0.70 (energy and inflation sensitivity), GLD 0.07, AGG 0.00.

### The four constraint layers
| Layer | Rule | Client risk it controls / reason | Evidence |
|---|---|---|---|
| 1 Structural | Long-only, fully invested, only the 7 ETFs, no leverage or cash | Mandate and brief p.4–5 (D10) | Brief |
| 2 Strategic range: equity | **Equity (SPY+EFA+EEM+XLE+XLK) 20–45%** | Lower bound: below 20%, purchasing-power risk *rises* again and expected return falls under 5.2%. Upper bound: above ~40%, the 25% drawdown tolerance is breached (P(DD > 25%) 5.3% at 40%, 9.0% at 45%). The extra 5pp above 40% is a governance band; D7 binds first | Sweep A |
| 2 Strategic range: gold | **GLD 0–20%** (benchmark 10% × 2) | A hedge for stagflation and 2022-type regimes, but no expected premium and higher drawdown risk when it replaces bonds | Sweep B, correlations |
| 2 Strategic range: bonds | **AGG = remainder (≥ 35% implied)** | Stability, income (4.2% yield), liquidity (≥ 8% liquidity rule easily met). AGG is a diversified index, so no single-issuer concentration | Yields, D7 |
| 3 Position caps | **Each ETF ≤ 2 × its policy-benchmark weight** (EFA ≤ 20%, EEM ≤ 10%, GLD ≤ 20%; SPY's 50% is never binding under the equity cap) | One rule for all ETFs: prevents the optimiser chasing noisy estimates into concentrated bets | Michaud (1989) error-maximisation; the uncapped optimum puts 35% in XLK |
| 3 Sector tilts | **XLE, XLK ≤ 10% each, ≤ 15% together** | Not asset classes (they sit inside SPY), so allowed only as small tilts. XLK adds concentration (ρ 0.91), XLE adds inflation sensitivity (ρ 0.70) | Correlations |
| 4 Risk budget | **Component ES per ETF ≤ cap** (value set in the risk stage) | Position sizing by contribution to risk, not by weight (brief §8.6 risk budgeting) | Method only [O] |
| — | No minimum weights (except the implied AGG ≥ 35%) | Lets the optimiser exclude an ETF when the evidence says so | — |

**Check against D7 [E]** (`--d6`, row "D6 v2"): 80% of portfolios within these ranges also meet the D7 limits, against 6% for the draft caps. So the weight and risk constraints are consistent rather than conflicting. The best expected return is **6.28%** (AGG 51 / SPY 31 / XLK 9 / GLD 5 / XLE 3 / EFA 1), the same as no caps (6.34% with 35% in XLK), supporting **~3.1% spending**.

**Robustness [E]:** drawdowns from the training sample alone (2004–14) are identical to the full sample at every equity level. The binding event is 2008 in both, so the calibration is not driven by the test period.

**Judge-facing summary:** "Our caps come from the client's two risks. Equity is bounded by the purchasing-power minimum (20%) and the drawdown tolerance (≈ 40–45%). Every ETF is capped at twice its strategic weight to prevent error-maximising concentration. Sector funds are small tilts. Position risk is then budgeted by component ES."

## 7. Gold assessed outside CAPM (warning 2, 2026-10-28) [E]
Reproduce: `python scripts/research_d3_d7.py --gold` → `research_gold_assessment.csv` (daily-rebalanced weights).

| Test | GLD | SPY | AGG |
|---|---|---|---|
| GFC 2007-10-09 → 2009-03-09 | **+24.9%** | −54.8% | +7.2% |
| COVID 2020-02-19 → 2020-03-23 | −3.1% | −33.4% | −1.4% |
| 2022 rate shock | **−8.8%** | −24.1% | −15.0% |
| Average month when SPY < −5% (24 months) | **+1.6%** | −7.9% | −0.2% |
| Average month when CPI YoY > 4% (41 months) | +0.1% | −0.7% | −0.2% |
| Policy 40/50/10 vs the same with gold → AGG: GFC / 2022 / COVID | −20.9% vs −22.6% · −18.3% vs −18.9% · −14.9% vs −14.8% | | |

**Reading:**
- Gold was the best hedge in equity crashes and the 2022 rate shock, which is exactly what CAPM's β ≈ 0 (4.6% expected) doesn't capture.
- But gold has its own long drawdowns (−45%, 2011–15), which is why sweep B shows full-history drawdown rising when gold *replaces* bonds in large amounts.
- **Conclusion:** the evidence supports a **5–15% strategic role** (benchmark 10%, D6 cap 20%), not a large allocation. Its expected return stays at the CAPM value, and its hedge value is shown through stress tests, not by inflating its expected return.

> **Superseded for the final portfolio (note 2026-10-31).** This was a design-stage reading of hedge behaviour, used to set the D6 range (gold 0–20%). The final selection tested a 5% gold floor directly (O4, T4_25) and rejected it: the expected-return edge reverses when rates fall, and the 2020–26 gain came from one gold cycle already seen. A robustness run with gold-specific expected returns is in V2_gold_return.md. O6 holds 0.4%, and the documents give it no hedge credit.

## 8. Revision 2026-10-28b: model warnings fixed (supersedes figures in §4, §5b, §5c)
| Warning | Fix in code | Effect |
|---|---|---|
| 5 Daily vs monthly volatility | `cma.annual_covariance` now uses **daily** returns (monthly reported separately, `volatility_monthly`) | Variance drag larger → expected returns −0.1 to −0.5 pp |
| 4 Withholding tax | Rate **per ETF** on each fund's own yield; cases: AGG interest exempt (30% on equity ETFs) and 30% on all | Drag 0.09–0.37 pp (AGG exempt), 0.55–0.87 pp (upper bound); base case stays tax-exempt |
| 3 Risk-free rate | Scenarios: today's T-bill 4.10% (base), 3.0%, 2.5% | Every expected return falls one-for-one; at 2.5% the 60/40 earns 4.99% |
| 2 Gold vs CAPM | Separate assessment (§7) | Supports a 5–15% hedge role |
| 1 ERP | Already handled: base 5%, sensitivity 3–6% | — |

**Updated headline numbers (ERP 5%, today's T-bill, tax-exempt):**

| Item | Before | After |
|---|---|---|
| 60/40 / 40/60 / Defensive expected return | 6.80 / 6.07 / 5.63% | **6.59 / 5.99 / 5.58%** |
| Best within D7 + D6 v2 | 6.28% (~3.1% spending) | **6.16% (~3.0% spending)** |
| Best within D7, draft caps | 6.00% | 5.90% |
| Risk needed for the 6.66% minimum | DD ≈ 31%, ES ≈ 2.8% | **DD ≈ 33%, ES ≈ 3.2% without caps; infeasible with any caps** |
| Risk needed for the 7.19% target | DD ≈ 37% | **DD ≈ 45% without caps** |
| Equity 40% (sweep A): expected / P(DD > 25%) / P(below inflation) | 6.03% / 5.3% / 14.0% | 5.94% / 5.3% / 14.0% (probabilities unchanged: bootstrap uses daily data already) |

**Rate-scenario stress on the decision:** if the T-bill averages 2.5% over the 5 years, the best D7-compliant portfolio earns about 4.6%, which supports only ~1.4% spending.

**Conclusion:** D5, D6 v2 and D7 choices are unchanged; only levels moved. The conflict with D12 is **sharper**: a conservative portfolio supports about **3.0% spending in the base case and 1.4–2.0% if rates fall**, against the 4% assumed. The memo should present spending as a range tied to the rate outlook.

## 8b. Revision 2026-10-28c: D25 (AGG expected return = its yield)
AGG's expected return is now its distribution yield on the as-of date (4.17% in 2026; 2.40% at the 2014 train end, where CAPM gave 0.16%). Pure CAPM is kept as a reference column (`capm_E[R] …`). Every table was rerun:

| Item | Rev. b | **Rev. c (D25)** |
|---|---|---|
| 60/40 / 40/60 / Defensive expected return (today's T-bill) | 6.59 / 5.99 / 5.58% | **6.47 / 5.81 / 5.44%** |
| Same at a 2.5% T-bill | 4.99 / 4.39 / 3.98% | **5.51 / 5.17 / 4.64%** (AGG's yield is locked in, so falling rates hurt less) |
| Best within D7 + D6 v2 | 6.16% (~3.0% spending) | **6.01% (~2.9% spending)** |
| Best within 25% DD, ES 2.5%, no caps / draft caps | 6.20 / 5.90% | 6.03 / 5.79% |
| Risk needed for the 6.66% minimum (no caps) | DD ≈ 33% | **DD ≈ 35%** (still infeasible under any caps) |
| P(DD > 25% in 5y), policy benchmark | 4.7% | 4.9% |
| P(real value < 80% in 5y), 40% equity, 4% smoothed spending | 17.8% | 18.5% |

No decision changes. The return conflict is slightly larger in the base case, but **much less severe under falling rates**, which is more realistic for a bond-heavy fund.

## 9. Risk tolerance and risk capacity: the 12-factor review (2026-10-28)
The brief gives no loss number, so the client's tolerance must be **approximated**. Method (CFA investment-policy framework): **risk tolerance = the lower of willingness and ability (capacity)**.
Reproduce: `python scripts/research_d7_capacity.py` → `research_capacity_*.csv`. Bootstrap: 4,000 five-year paths (2,000 ten-year paths for recovery), CAPM means, quarterly spending, inflation 2.35%. Portfolios: global equity mix + 10% gold + rest AGG.

### 9.1 Willingness (factor 1) [A, anchored on evidence]
| Evidence | Reading |
|---|---|
| Brief: "conservative", "capital preservation", "avoiding large losses is more important than maximising gains" (pp.3–4) | Below-average willingness to bear loss |
| Peers: average US endowment lost 18.7% in FY2009 ([NACUBO via PlanSponsor](https://www.plansponsor.com/study-confirms-tough-year-for-endowments/)) | A conservative fund should lose **less than peers** in a GFC year. Policy-type portfolio lost 7.6% on the same fiscal-year basis |
| A conventional 60/40 lost 35% peak-to-trough in 2008 | A conservative client should accept clearly less than a balanced investor |
| **Willingness proxy** | **Peak-to-trough loss ≤ ~25%** (well below 60/40's 35%) and fiscal-year loss below peers' ~19% |

### 9.2 Ability: risk capacity (factors 2, 3, 4) [E]
**Analytic capacity.** With fixed-dollar spending S, a loss d raises the spending rate to S/(1−d). If the highest acceptable rate is S_max, then capacity is d* = 1 − S/S_max.

| Spending S \ highest acceptable rate | 5.0% (top of NACUBO size bands) | 5.5% | 6.0% |
|---|---|---|---|
| 4.0% | **20%** | 27% | 33% |
| 3.5% | 30% | 36% | 42% |
| 3.0% | 40% | 45% | 50% |

**Simulated capacity, 5-year paths with spending** (probability that the fund's real value ever falls below 80% of today):

| Equity | Spending 4%: fixed-real / %-of-NAV / smoothed | Spending 3% (smoothed) | Median real value after 5 years (4%) |
|---|---|---|---|
| 20% | 14.5% / 11.5% / 13.2% | 6.6% | 95% |
| 30% | 15.5% / 13.3% / 14.5% | 9.1% | 97% |
| **40% (policy)** | 18.6% / 16.4% / 17.8% | 11.8% | 99% |
| 45% (D6 max) | 20.3% / 18.2% / 19.3% | 13.5% | 100% |
| 60% | 25.6% / 23.9% / 24.8% | 19.8% | 102% |

**Finding:** capacity is driven more by **spending** than by equity. At 4% spending, even a 20%-equity fund has a 14.5% chance of losing a fifth of its real value within 5 years, and its median real value falls. That matches D12: conservative portfolios support about 3% spending. **At 4% spending, capacity is about 20–27%; at about 3%, it rises to 40% or more.**

### 9.3 Spending rule (factor 3) [E]
| Rule (policy portfolio, 4%) | P(spending rate ever > 5%) | P(real spending ever cut > 10%) |
|---|---|---|
| Fixed real dollars | 16.7% | 0% (the fund's value absorbs every loss) |
| % of current value | 0% | 41.1% (scholarships absorb every loss) |
| **Smoothed** (70% last year's spending + inflation, 30% × 4% of value; Yale-type) | **5.2%** | **17.4%** |

A smoothing rule spreads losses between the fund's value and spending. **Proposed D24.**

### 9.4 Recovery time (factor 8) [E]
Forward paths (10 years, no spending), policy-type portfolio (40% equity):

| Loss | P(it happens within 10 yrs) | Median years to recover | 90th percentile | Not recovered within horizon |
|---|---|---|---|---|
| 10% | 91% | 1.1 | 3.3 | 6% |
| 15% | 67% | 1.5 | 3.8 | 15% |
| 20% | 39% | 2.1 | 4.3 | 25% |
| 25% | 11% | 2.8 | 4.9 | 38% |

Historical (one path): about 1.0–1.2 years from first hitting each level back to the prior peak (40% equity). At 60% equity it was about 2 years.

**Reading:** a 25% loss can take most of the 5-year horizon (D4) to recover. That supports 25% as an **upper bound**, not a level to loosen.

### 9.5 Liquidity (factor 10) [E]
- AGG at 50% is $5.0M, about **12.5 years** of spending.
- AGG's worst day was −6.8% (2008-10-10). Selling a whole year's spending that day would have cost **$27k (0.27% NAV)**.
- AGG gained 7.2% over the GFC window.

Funding spending from bonds in a crisis is cheap. **Forced-sale risk is low**; the AGG ≥ 8% rule is more than met.

### 9.6 Losses beyond history (factor 11) [E]
Crisis replays with daily losses scaled up:

| Equity | GFC ×1.0 / ×1.25 / ×1.5 | 2022 ×1.5 | COVID ×1.5 |
|---|---|---|---|
| 30% | −13.9 / −17.4 / −21.0% | −25.0% | −17.3% |
| **40%** | −20.9 / **−26.0 / −30.9%** | −26.4% | −21.9% |
| 45% | −24.3 / −30.0 / −35.5% | −27.2% | −24.1% |

A crisis 25% worse than 2008 breaks the 25% limit for the policy-type portfolio. **The limit is a target, not a guarantee**, which is why the action ladder (§9.8) is needed. The hypothetical scenario (D9) should include a crisis of this severity.

### 9.7 Other measures and optimised results (factors 5, 6, 7, 9)
Already covered: the feasibility map (§4, §8), crisis tables (§1.2, §7), and the VaR/ES limits consistent with the drawdown limit (D7). **Committee framing:** the ES99 limit of $250k on one bad day equals about **7.5 months of spending** ($400k a year).

### 9.8 Conclusion: approximated risk tolerance [P]
| | Value |
|---|---|
| Willingness | ≤ ~25% peak-to-trough |
| Ability at 4% fixed spending | ~20–27% |
| Ability at ~3% spending with a smoothing rule | 40% or more (willingness binds) |
| **Risk tolerance (lower of the two)** | **25% peak-to-trough, conditional on a smoothing spending rule** and spending moving toward the sustainable ~3% |

**D7 stays at 25% (confirmed, T3.28)**, with three conditions:
- **D24:** a smoothed spending rule.
- **D23:** a monitoring and action ladder.
- **Disclosure:** at 4% fixed spending the fund is at its capacity edge (~20%).

**Proposed D23 action ladder** (drawdown from peak, or a risk-measure breach):

| Level | Trigger | Action |
|---|---|---|
| Watch | −10%, or rolling ES99 > 2.0% | Report to the committee. No trading beyond quarterly rebalancing. Likely ~1 in 10 years |
| Review | −15%, or Basel yellow zone | Committee meeting: check the model, stress results and next year's spending under D24 |
| Act | −20%, or rolling ES99 > 2.5% | Formal decision: keep, reduce risk at the next rebalance, or adjust spending. **No forced selling at the low point** |
| Limit | −25%, or Basel red zone | Mandatory committee decision using the memo options: accept / adjust the risk limit / reject the strategy |

## 6. Next actions (added to the tracker)
T3.17 approve D3 structure · T3.18 approve D7 provisional limits · T6.12 forward-looking drawdown probabilities (G1) · T8.13 ERP-sensitivity feasibility (G7) · T11.11 longer-history proxy crises (G2, optional) · T9.06 component-ES limit (G4) · T10.12 out-of-sample check of the limits (G8) · T20.06 drawdown/spending trade-off table in the memo.
