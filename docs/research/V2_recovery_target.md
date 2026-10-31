# V2 Real-recovery target: can we reach a 60% chance of recovery within 15 years? [E]

**Status: research on branch `version-2`. Result: not adopted.** O6, the 2.65% policy (D30) and D39 are unchanged.

**Reproduce:** `python scripts/research_v2_recovery_target.py` (about 10 minutes) → `research_v2_recovery_target.csv`, `research_v2_recovery_target_portfolios.csv`.

## 1. Question
The proposed target: **after a fall of 25% or more, at least a 60% chance that real value (after spending and costs) is back to its pre-crisis level within 15 years.** It is a probability target, not a deadline.

Can it be met within every approved limit (D6, D7, D27, the stress limits), and at what cost to the university?

## 2. Design
The machinery is the same as T20.09 view 4 (D39):
- 8,000 bootstrap paths of 25 years, using the CMA, D24 spending, 0.2% costs and 2.35% inflation;
- seeds random_seed + 100 + k, the same as the pipeline;
- a crisis is the portfolio's own drawdown reaching 25% (or 20%) within the first 10 years.

**Experiments:**
- **A:** O6 with D24 at 2.65% (approved).
- **B1:** O6, finding the highest D24 spending rate that meets the target.
- **B2:** O6 at 2.65%, plus recovery-mode spending. After a 20% fall (the D23 "act" step), the fund spends a lower rate × NAV until real value is back. We find the highest lower rate that meets the target.
- **C:** other portfolios at 2.65%.
  - The approved rule family (D26 with D6, D7 and the D27 cap) at expected returns of 5.32%, 5.48% and 5.64%. Higher returns fail D7: O6 is already the highest compliant portfolio.
  - The P1 candidates, for reference.
- **D:** joint, meaning each C portfolio with its own highest D24 rate that meets the target.

**Checks:**
- Every case that meets the target is re-checked on independent seeds with 16,000 paths.
- Every portfolio is scored like O6: D7 (including the 126-day, 32,000-path 5-year test), D27, and every historical, hypothetical and tech-led stress test.

**Adoption rule** (fixed in the script before the run). A candidate is adopted only if all three hold:
1. It passes D6, D7 and D27, and every stress loss is at most 25%.
2. It meets the 60% target on both seed sets.
3. It is affordable: normal-times spending of at least 2.60% (D30's "about 2.65%") and no crisis-time cut beyond D24's own.

## 3. Results
| | Rule | P(back ≤ 15 yrs \| ≥ 25% fall) | New seeds, 16k | Median yrs | Avg real spending, yrs 1–20 | Meets the rule? |
|---|---|---|---|---|---|---|
| **A** O6 | D24 2.65% | 46% | — | 17.8 | 2.9% of start value | (baseline) |
| **B1** O6 | **D24 1.80%** | 61% | 62% | 10.8 | 2.1% | target yes; **not affordable** (−$85k first year) |
| **B2** O6 | 2.65% + recovery mode at **1.00%** | 62% | 63% | 11.0 | 2.8% | target yes; **not affordable**: the budget falls to 30% of normal for about 8 years in 14% of paths |
| **C** best: Risk Parity | D24 2.65% | 48% | — | 16.8 | 2.8% | no |
| **C** D26+D27 at 5.64% / 5.48% / 5.32% | D24 2.65% | 44% / 40% / 35% | — | 20.8 / ∞ / ∞ | 2.8% | no |
| **D** best: O6 or Risk Parity | D24 1.80% | 61% | 62% | 10.3–10.8 | 2.0–2.1% | not affordable |

Notes on the C portfolios:
- They all pass D6, D7, D27 and the stress limits. Min-CVaR and target-return fail D27 (SPY's share of ES is 62–73%). Min-variance fails D27 and never reaches 60% at any tested spending rate.
- The lower-return D26 portfolios suffer far fewer 25% crashes (139–427 paths vs 629), but recover more slowly when they do. Their chance of real value being at least today's after 15 years is also lower (59–65%, against O6's 67%).

## 4. Findings
1. **The 60% target cannot be met without unaffordable spending cuts.** The two routes that meet it on both seed sets cost too much:
   - permanent spending of about 1.8%: about −$85k in year 1, and real spending about 0.8% of start value lower each year on average;
   - recovery-mode spending at 1.0%: about a 70% budget cut for about 8 years whenever a 20% fall occurs.
2. **The portfolio cannot buy recovery.** No approved-rule portfolio, and no P1 candidate, reaches 60% at 2.65%. O6 is already the highest-return portfolio within D7. Lower-risk portfolios crash less often but recover more slowly and preserve less real value overall.
3. **O6 remains the best approved portfolio on the long-run measure.** Among D27-compliant portfolios, it has the highest chance that real value is at least today's after 15 years (67%).
4. **Recovery probability costs a lot of spending:**

   | Recovery chance (≥ 25% fall, within 15 yrs) | Rule |
   |---|---|
   | 46% | 2.65% (approved) |
   | 52% | 2.65% + recovery mode at 2.0% |
   | 58% | 2.0% permanently |
   | 61% | 1.8% permanently |

   Each extra 1 pp of recovery chance costs roughly $5–6k a year of permanent spending.

## 5. Conclusion
**Not adopted.** O6 and 2.65% stay (D30, D39). A 60% target is not feasible at a spending level the university can afford, and changing the portfolio does not help. If the committee wants a recovery target, a realistic one is the level the policy already delivers (about 46–52%). Alternatively, it can choose recovery-mode spending at 2.0% (52%), knowingly accepting a crisis-time cut of about a third.

## 6. Limitations
- Same as view 4: one set of CMA assumptions, a bootstrap of 2004–26, and quarterly spending.
- The C search is the approved rule at a grid of targets, not a free search over all weights. A free search would still face the D7 return ceiling.
- The D26+D27 targets below 5.3% gave no solution with the cap (the optimiser falls back), so the low end is covered by P1 min-variance.
- The 16,000-path stability check moves results by up to 2 pp. D at 5.48% and 5.64% falls just below 60% on the new seeds (59.9%).
