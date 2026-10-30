# Subtask Tracker

Detailed breakdown of every main task in `TASKS.md`. Sources: **PM** = Project Management Tracker (original 98 subtasks, IDs kept), **FJ** = FigJam Pipeline Block Reference (block id), **BR** = official brief (page), **DEC** = `docs/DECISIONS.md`, **REV** = 2026-10-28 review / data findings.

**How to update:** change only the Status cell (`Not started` → `In progress` → `Done`, or `Blocked (…)`), then run `python tracking/update_counts.py`. New subtasks take the next free number in their task. Never renumber.
Priority: **Critical** = brief-mandated or blocks other work · **High** = needed for correctness · **Medium** = strengthens the submission · **Low** = nice to have.

## T1 — Project setup & shared decisions
Stage: — · Owner: Malindu · Priority: Supporting · Target: Week 1

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T1.01 | Create shared GitHub repository and directory structure | Folder tree, README, git repo; GitHub remote | Critical | Malindu | — | In progress | PM · local repo done, remote pending |
| T1.02 | Define environment, dependencies and setup commands | requirements.txt (pinned), setup steps in README | High | Malindu | T1.01 | In progress | PM · unpinned list exists |
| T1.03 | Agree on common model input/output conventions | conventions.py + CALCULATION_DICTIONARY.md (D17) | Critical | Malindu | — | Done | PM · DEC D17 |
| T1.04 | Agree date range, risk-free rate, benchmark and ETF universe | D1, D2, D3 approved in DECISIONS.md | Critical | Malindu | T2.06 | Done | PM · D2 implemented, D1/D3 open |
| T1.05 | Record decisions, responsibility owners and review process | DECISIONS.md, AGENTS.md, review rules | High | Malindu | — | Done | PM |
| T1.06 | Map brief Layers 1–5 to code stages; keep the vocabularies separate | PROJECT_KNOWLEDGE.md §1 | High | Malindu | — | Done | REV |
| T1.07 | Settle blocking decisions D3, D5, D6, D7, D12 before portfolio stage | All five APPROVED in DECISIONS.md | Critical | All members | T3.01–T3.04 | Done | DEC |
| T1.08 | Settle remaining decisions D1, D4, D8, D9, D11, D13, D16 | all decisions settled (D16 approved 2026-10-30) | High | All members | T1.07 | Done | DEC · QA 2026-10-30 |
| T1.09 | Upload missing Batch04 explainer (slides 61–80); remove duplicate Batch02 | docs/references/explainers complete | Low | Malindu | — | Not started | REV |
| T1.10 | Approve decisions already implied by approved work: D4 5-year horizon (D7 uses it), D11 quarterly (D3 uses it), D13 1,000-day window, D1 full sample, D2 DTB3, D8 EVT method | APPROVED rows in DECISIONS.md | Critical | All members | — | Done | Review 2026-10-28 (all approved 2026-10-28) |
| T1.11 | Approve optimiser design for drawdown limit (CVaR constraint + CDaR or post-check) | Decision D22 | Critical | All members | T4.20 | Done | Review 2026-10-28 |

## T2 — Data pipeline & cleaning
Stage: data · Owner: Raveena · Priority: Core · Target: Week 1

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T2.01 | Download adjusted prices for all seven allowed ETFs | data/raw/yahoo_adj_close_2026-10-20.csv | Critical | Raveena | — | Done | PM · FJ M04 · BR p.9 |
| T2.02 | Document data source, download date and adjustment choices | raw .meta.json + data/README.md source log | Critical | Raveena | T2.01 | Done | PM · FJ M04 |
| T2.03 | Align calendars, missing observations and common sample | prices_aligned.csv; data_quality_missing.csv | Critical | Raveena | T2.01 | Done | PM · FJ M05 · BR p.9 |
| T2.04 | Calculate daily log returns and verify computations | log_returns.csv + tests | Critical | Raveena | T2.03 | Done | PM · BR p.9 |
| T2.05 | Flag potential outliers without automatically deleting them | outlier_flags_zscore.csv (abs z > 5) | Critical | Raveena | T2.04 | Done | PM · BR p.9 |
| T2.06 | Run ADF tests and export reproducible clean datasets | outputs/tables/adf_results.csv | Critical | Raveena | T2.04 | Done | PM · BR p.9 |
| T2.07 | Move notebook logic into tested data-stage code; prove it reproduces the original files | src/quantedge/data/, regression test (diff ≤ 3e-14) | Critical | Raveena | T2.06 | Done | REV · BR p.9 reproducible |
| T2.08 | Calculate simple returns and state where simple vs log are used | simple_returns.csv; D17 | Critical | Raveena | T2.03 | Done | BR p.9 · FJ M05 |
| T2.09 | Download FRED DTB3, DGS10, CPI; align to trading days without look-ahead | rates_daily.csv, cpi_monthly.csv | Critical | Raveena | T2.03 | Done | BR p.9 · FJ M04 |
| T2.10 | Extra quality checks: stale prices, jumps, reversals, large negatives, variance breaks | data_quality_flags.csv, flag counts, Inclán–Tiao table | Critical | Raveena | T2.04 | Done | BR p.9 |
| T2.11 | Review every flag against market events; document decisions | Flag review table in data/README.md | High | Raveena | T2.10 | Done | BR p.9 'documented, not hidden' |
| T2.12 | Confirm GLD −10.8% on 2026-01-30 against market news | Note in data/README.md | Medium | Raveena | T2.11 | Not started | REV |
| T2.13 | Implement chronological train / validation / test split in code | data/processed/split_labels.csv, outputs/tables/split_summary.csv, data/split.py + 5 tests | Critical | Raveena | T1.07 (D5) | Done | FJ M06 · DEC D5 |
| T2.14 | Download ETF distributions (dividends) for the income objective | data/raw dividends snapshot; distribution yield per ETF | Medium | Raveena | T2.01 | Done | FJ M-N01 · BR p.3 income |
| T2.15 | ETF instrument register: asset class, role, inception, distribution policy (no extra data sources) | docs/ETF_REGISTER.md | Medium | Raveena | — | Not started | FJ M03/M-N01 |
| T2.16 | Team sign-off of data-stage validation log entries | Signed rows in HUMAN_VALIDATION_LOG.md | High | Raveena | T2.11 | Not started | BR p.8 · REV |
| T2.17 | Move quarterly-rebalanced NAV/turnover function from research script into common/conventions with tests | conventions.rebalanced_returns + 4 tests; research script uses it (results identical, turnover −0.08 pp) | High | Malindu | T1.03 | Done | Review: portfolio and benchmark must use identical rebalancing |

## T3 — Client mandate (investment policy)
Stage: mandate · Owner: Sujan · Priority: Core · Target: Week 1

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T3.01 | Define endowment horizon, investment purpose and liquidity needs | Horizon D4 + liquidity statement in IPS | Critical | Sujan | — | Done | PM · FJ M01 · BR p.4 · D4 PROPOSED 5y (used by D7) |
| T3.02 | Propose justified return and inflation-protection objectives | Return objective D12 (CPI + x%) with evidence | Critical | Sujan | T2.09 | Done | PM · DEC D12 APPROVED (provisional) |
| T3.03 | Set no-short-selling, allocation caps and risk-budget rules | Constraints D6 in config | Critical | Sujan | T3.01 | Done | PM · FJ M02 · BR p.4 |
| T3.04 | Propose VaR, ES and drawdown tolerances | Risk limits D7 (USD and % NAV) | Critical | Sujan | T3.01 | Done | PM · FJ M02 · BR p.4 |
| T3.05 | Document assumptions and secure team agreement | assumptions documented except 4 empty sections in ASSUMPTIONS_LIMITATIONS.md (QA-01) | Critical | Sujan | T3.01–T3.08 | In progress | PM · QA 2026-10-30 |
| T3.06 | Spending rule and cost assumptions (spending rate, turnover cost; ETF fees already in prices) | D24 + D30 (2.65%), D12 costs 0.2%, D11 turnover (config mandate) | High | Sujan | T3.02 | Done | FJ M-N02 · D12 S/C approved; IPS write-up pending · QA 2026-10-30 |
| T3.07 | Rebalancing policy (frequency, drift band) | D11 approved; config | High | Sujan | T3.01 | Done | DEC D11 PROPOSED quarterly (used by D3 benchmark) |
| T3.08 | Choose benchmarks: CAPM market proxy and policy benchmark | D3 approved; config | Critical | Sujan | — | Done | DEC D3 · BR p.7 |
| T3.09 | Define suitability criteria used by the decision gate | suitability conditions T4_25 §3; Decision page gate (app/pages/6_Decision.py) | High | Sujan | T3.02, T3.04 | Done | FJ VD08 · D7 + D12 define criteria; checklist pending · QA 2026-10-30 |
| T3.10 | Confirm no cash sleeve / derivatives; spending liquidity from AGG | D10 in IPS | High | Sujan | — | Done | DEC D10 |
| T3.11 | Required-vs-expected return table (breakeven inflation, CAPM, income yield, history; ERP and withholding sensitivity) | outputs/tables/required_return_grid.csv, cma_assets.csv, required_vs_expected.csv | Critical | Sujan | T2.09, T2.14 | Done | DEC D12 |
| T3.12 | Choose base ERP and risk-free assumption for expected returns (own-data ERP 9.7%, CI 3.5–15.8%, too wide to use alone) | ERP base + rf choice in DECISIONS.md | Critical | Sujan | T3.11 | Done | DEC D12 |
| T3.13 | Confirm base spending rate, real growth and extra costs (S, G, C); cite the spending benchmark source | D12 values APPROVED | Critical | All members | T3.11 | Done | DEC D12 |
| T3.15 | Highest sustainable spending per portfolio + auto-generated one-page summary | outputs/reports/return_objective_summary.md | High | Sujan | T3.11 | Done | DEC D12 (shortfall policy: lower spending) |
| T3.16 | Revisit S, G, C and ERP after further team research; rerun and compare | Updated D12 values + summary | Medium | All members | T3.13 | Not started | Team 2026-10-28 |
| T3.17 | Research and approve D3 benchmark structure | Research doc §1; D3 APPROVED | Critical | All members | T3.11 | Done | Research 2026-10-28 (analysis done, approval pending) |
| T3.18 | Research and approve D7 provisional risk limits | Research doc §2/§4; D7 APPROVED | Critical | All members | T3.17 | Done | Research 2026-10-28 (analysis done, approval pending) |
| T3.19 | Committee choice on the drawdown ↔ spending trade-off (20% → 2.1%, 25% → 2.8%) | Recorded in D7/D12 | Critical | All members | T3.18 | Done | Research §4 |
| T3.20 | Fix model warnings: daily covariance, per-ETF withholding, risk-free scenarios, separate gold assessment | Research doc §7–§8; cma.py; 2 tests | Critical | Sujan | T3.11 | Done | Team warnings 2026-10-28 |
| T3.21 | Risk tolerance approximation: willingness (mandate wording, peer losses) vs ability (capacity); tolerance = lower of the two | Tolerance statement in research doc §9 + IPS | Critical | Sujan | T3.22 | Done | Team 2026-10-28 (12-factor review) |
| T3.22 | Risk capacity: largest loss the fund can take while keeping spending and real value within floors (analytic + bootstrap with spending) | Capacity table by allocation | Critical | Sujan | T3.11 | Done | 12-factor review #2 |
| T3.23 | Spending continuity after losses: fixed-real-dollar vs %-of-NAV vs smoothing rule over 5-year paths | Spending-rule comparison; proposed rule (D24) | Critical | Sujan | T3.22 | Done | 12-factor review #3 |
| T3.24 | Recovery time after 10/15/20/25% losses: historical and forward (bootstrap) | Recovery-time table | High | Dewmini | T6.12 | Done | 12-factor review #8 |
| T3.25 | Liquidity under stress: funding spending and rebalancing from AGG in a crisis (incl. 2008-10-10 discount) | Liquidity note with $ cost | High | Raveena | T2.11 | Done | 12-factor review #10 |
| T3.26 | Losses beyond history: severity-scaled crisis replays (GFC ×1.25, ×1.5) | Severe-scenario table; feeds D9 | High | Dewmini | T11.02 | Done | 12-factor review #11 |
| T3.27 | Drawdown monitoring and action ladder (amber / red / limit) for memo and app | D23 approved; ladder in config risk_limits.action_ladder | Critical | All members | T3.22 | Done | 12-factor review #12 |
| T3.28 | Re-confirm D7 (drawdown, VaR, ES limits) against tolerance and capacity results | D7 confirmed or revised | Critical | All members | T3.21–T3.27 | Done | 12-factor review |
| T3.29 | Open question for committee: is 4% spending compulsory (fixed) or flexible? Memo shows both: fixed → disclosed real erosion ~0.6–1.2%/yr and capacity ~20%; flexible → move toward ~2.9% via D24 | D30 APPROVED: flexible; glide to ~2.8–2.9% via D24 (no risk-limit increase) | Critical | All members | T4.11 | Done | Team discussion 2026-10-29 |
| T3.14 | Tax assumption: tax-exempt base case, dividend withholding as sensitivity (check interest-related dividend exemption for AGG) | Note in IPS + limitations | Medium | Sujan | T3.11 | Done | DEC D12 |

## T4 — Portfolio construction & selection
Stage: portfolio · Owner: Dewmini · Priority: Core · Target: Weeks 1–2

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T4.01 | Estimate training returns, covariance matrix and correlations | cma.estimate_as_of → cma_train.csv, cma_train_cov(_shrunk).csv (data ≤ 2014-12-31) | Critical | Dewmini | T2.13 | Done | PM · FJ PM01 · QA 2026-10-30 |
| T4.02 | Implement constrained minimum-variance allocation | p1_*: min_variance | Critical | Dewmini | T4.08, T3.03 | Done | PM · FJ PM02 |
| T4.03 | Implement risk-parity allocation | p1_*: risk_parity (ERC moved ≤ 1% to meet limits) | Critical | Dewmini | T4.08 | Done | PM · FJ PM03 |
| T4.04 | Implement capped maximum-Sharpe allocation | p1_*: max_sharpe (homogenised) | Critical | Dewmini | T4.08, T3.03 | Done | PM · FJ PM04 |
| T4.05 | Document Markowitz/CAPM concepts and benchmark assumptions | research doc P1_candidates_and_kpis.md + report §4 (draft) | Critical | Dewmini | T4.11 | Done | PM · BR p.7 · QA 2026-10-30 |
| T4.06 | Compare diversification, concentration and feasible weights | p1_*_diagnostics (risk contributions, equity weight) + research doc P1_candidates_and_kpis.md | Critical | Dewmini | T4.02–T4.10 | Done | PM · FJ PM07 |
| T4.07 | Provide candidate and proposed final weights with justification | p1_final/p1_train weights + T4_25 doc + outputs/p3_decision/p3_portfolio.csv | Critical | Dewmini | T4.06, T5.05 | Done | PM · QA 2026-10-30 |
| T4.08 | Robust inputs: shrinkage covariance (Ledoit–Wolf), cautious expected returns | cma.shrunk_covariance (Ledoit–Wolf on correlations); cma_*_cov_shrunk.csv; δ train 1.6% / full 0.8% / 1y 7% / 3m 18%; stability test (--shrink): turnover 1.61% → 1.57% a month; 2 tests | High | Dewmini | T4.01 | Done | FJ PM01/robust frontier · REV |
| T4.09 | Implement minimum-CVaR allocation (Rockafellar–Uryasev) | p1_*: min_cvar (CVaR LP) | High | Dewmini | T4.08 | Done | DEC D20 |
| T4.10 | Implement target-return Markowitz at the D12 hurdle (minimum 6.66% / target 7.19%) with fallback to lowest-risk feasible portfolio | p1_*: target_return (fallback per D12) | High | Dewmini | T4.08, T4.18 | Done | FJ PM05 |
| T4.11 | Efficient frontier with candidates and benchmarks plotted; trade-off table | outputs/tables/frontier_full.csv (9 points: return, DD, ES, VaR, P(DD>25%), spending $), outputs/figures/frontier_full.png | Critical | Dewmini | T4.02–T4.10 | Done | BR p.4 #5 · R16 |
| T4.12 | Feasibility filters: D6 v2 layers (equity 20–45%, GLD ≤ 20%, ≤ 2× benchmark, sector tilts) + D7 limits | D6 v2 + D7 in optimiser; post-check on compounded quarterly NAV | Critical | Dewmini | T4.02–T4.10 | Done | FJ PM06 |
| T4.13 | Net-of-cost and turnover test under chosen rebalancing | turnover 7.0%/yr, rebalancing cost < 0.02%/yr at 10 bp (research_t425_eval_summary.csv, stress_hyp path costs) | Medium | Dewmini | T3.06, T3.07 | Done | FJ PM-N03 · QA 2026-10-30 |
| T4.14 | Diversification metrics: diversification ratio, risk contribution vs weight | p2_diversification.csv (benefit, diversification ratio) + component ES vs weight (p2_attribution.csv) | High | Dewmini | T4.12 | Done | BR p.4 'diversification benefits' · QA-02: diversification benefit not quantified anywhere (brief p.4) |
| T4.15 | Weight sensitivity to input changes (sub-period / bootstrap re-estimation) | weight shift 2014→2026 inputs (research_t425_eval_summary.csv) + walk-forward weights at 6 origins (research_walkforward_weights.csv) | Medium | Dewmini | T4.12 | Done | FJ robust frontier · QA 2026-10-30 |
| T4.16 | Freeze P1 handoff: candidate weights + metadata file | outputs/tables/p1_*_weights.csv (regenerated by run_all) | Critical | Dewmini | T4.12 | Done | FJ PM08 |
| T4.17 | Unit tests for all optimisers (constraints respected, known solutions) | tests/unit/test_optimise.py (7) + integration | Critical | Dewmini | T4.02–T4.10 | Done | BR p.6 software |
| T4.18 | Capital market assumptions estimated on the training window only, for out-of-sample candidates | cma.estimate_as_of; outputs/tables/cma_train*.csv, cma_full*.csv, cma_sets_summary.csv; 4 tests incl. leakage | Critical | Dewmini | T2.13 | Done | Review: current CMA uses full sample |
| T4.19 | Produce two P1 sets: P1-train (frozen, for OOS backtests) and P1-final (full-sample re-fit, same frozen method) | p1_train_* and p1_final_* | Critical | Dewmini | T4.16, T4.18 | Done | DEC D5 protocol |
| T4.20 | Optimiser design meeting D6 v2 + D7 (ES as CVaR constraint; drawdown via CDaR or post-check) | portfolio/optimise.py: CVaR LP + CDaR(β→1) + bisection post-check | Critical | Dewmini | T4.12 | Done | Review 2026-10-28 |
| T4.21 | Add every candidate to the required-vs-expected table with sustainable spending | p1_final/p1_train_diagnostics.csv: sustainable_spending + hurdle for every candidate | High | Dewmini | T4.16 | Done | DEC D12 · QA 2026-10-30 |
| T4.22 | Decide bond expected-return method for near-zero rates (D25) and apply to both CMA sets | D25 approved; cma.expected_returns applied to both CMA sets, D12 tables, research; 1 test; research doc §8b | Critical | All members | T4.18 | Done | T4.18 finding |
| T4.23 | Required return in training-period terms (2014 breakeven, same S/G/C) for P1-train return targets | return_objective.required_return_as_of; cma_sets_summary.csv: train 6.49% / 5.96% (breakeven 1.68%), full 7.19% / 6.66%; 2 tests | High | Dewmini | T4.18 | Done | D5 + D12 consistency |
| T4.24 | Decide portfolio choice rule when the hurdle is infeasible (D26) | D26 approved (option b); frontier.select_highest_compliant; d26_selected in P1-train / P1-final | Critical | All members | T4.11 | Done | T4 finding 2026-10-29 |
| T4.25 | Final-selection robustness: D26 with a 5-year-test margin, component-ES cap, or blend with Risk Parity (out-of-sample evidence) | O1–O5 evaluated (research_t425_eval_*.csv, research doc T4_25): O4 gold floor not justified; O2 recommended (conditional) | High | Dewmini | T9.06, T10.07 | Done | KPI findings 2026-10-29 · component-ES cap option done (D27) |
| T4.26 | Speed up portfolio stage (~7 min): cache solves, fewer bisection steps | run_all under ~2 min | Medium | Malindu | — | Not started | Review 2026-10-29 |

## T5 — KPIs & benchmarks
Stage: portfolio · Owner: Raveena · Priority: Supporting · Target: Week 2

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T5.01 | Implement Sharpe and Sortino metrics consistently | kpis.kpis: Sharpe, Sortino | Critical | Raveena | T1.03 | Done | PM · BR p.7 |
| T5.02 | Compute Treynor and Jensen alpha with market benchmark | kpis.kpis: beta, Jensen α vs SPY (D3) | Critical | Raveena | T3.08 (D3 done) | Done | PM · BR p.7 |
| T5.03 | Compute Information Ratio against the Policy 40/50/10 benchmark (D3) | kpis.kpis: IR vs Policy 40/50/10 | Critical | Raveena | T3.08 | Done | PM · BR p.7 |
| T5.04 | Compute maximum drawdown and Calmar ratio | kpis.kpis: max DD, Calmar | Critical | Raveena | T1.03 | Done | PM · BR p.7 |
| T5.05 | Prepare comparative KPI and benchmark results | outputs/tables/kpis.csv (candidates + D3 benchmarks) | Critical | Raveena | T4.16, T5.01–T5.04 | Done | PM · FJ PM-N02 |
| T5.06 | CAPM expected return and beta per ETF and candidate | cma_full.csv / cma_train.csv betas and CAPM E[R] | Critical | Raveena | T3.08 | Done | FJ PM-N01 · BR p.7 |
| T5.07 | Report KPIs separately for training and out-of-sample periods | kpis.csv periods: train / validation / test (P1-train) + full (P1-final) | High | Raveena | T2.13, T5.05 | Done | REV leakage |
| T5.08 | Verify KPIs against hand-calculated examples | tests/unit/test_kpis.py (4 known-answer tests) | High | Raveena | T5.01–T5.04 | Done | REV |
| T5.09 | KPIs for portfolio and all D3 benchmarks with identical (quarterly) rebalancing and total returns | same quarterly rebalancing for all (conventions.rebalanced_returns) | High | Raveena | T2.17 | Done | DEC D3 |

## T6 — VaR with 3 methods
Stage: risk · Owner: Sujan · Priority: Core · Target: Week 2

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T6.01 | Fix portfolio losses convention and risk horizon | Loss = −return, 1-day, constant target weights (risk/var_es.py) | Critical | Sujan | T1.03, T4.16 | Done | PM · FJ R01 · conventions done |
| T6.02 | Implement Historical VaR at 95% and 99% | var_es.historical | Critical | Sujan | T6.01 | Done | PM · BR p.7 |
| T6.03 | Implement Parametric VaR at 95% and 99% | var_es.normal + student_t (MLE) | Critical | Sujan | T6.01 | Done | PM · BR p.7 |
| T6.04 | Implement Monte Carlo VaR at 95% and 99% | var_es.monte_carlo: t-copula + empirical marginals (D19), 100k sims, seed 42 | Critical | Sujan | T6.01 | Done | PM · BR p.7 · DEC D19 |
| T6.05 | Compare all methods on identical portfolios and windows | outputs/tables/p2_var_es.csv: 6 portfolios × 4 methods × 3 levels | Critical | Sujan | T6.02–T6.04 | Done | PM · FJ R-N01 |
| T6.06 | Explain disagreements under calm and stressed conditions | docs/research/P2_var_es_methods.md §2 | Critical | Sujan | T6.05, T8.11 | Done | PM · BR p.7 |
| T6.07 | Add 90% level to every VaR method (app requirement) | 90/95/99 in every method | Critical | Sujan | T6.02–T6.04 | Done | BR p.5 · R20 |
| T6.08 | Test model assumptions: Jarque–Bera, Ljung–Box on squared returns, QQ plots | var_es.assumption_diagnostics → p2_diagnostics.csv (JB, kurtosis, Ljung–Box², t ν) | Critical | Sujan | T6.01 | Done | BR p.7 · DEC D21 |
| T6.09 | Uncertainty bands: bootstrap CI (historical), MC standard error | bootstrap 95% intervals; MC batch SE | Critical | Sujan | T6.02–T6.04 | Done | BR p.5 · DEC D18 |
| T6.10 | Multi-day horizon by simulation (no silent √t) | 10-day / monthly VaR | Medium | Sujan | T6.04 | Not started | DEC D17 |
| T6.11 | Express VaR in USD on the $10M NAV | VaR_usd / ES_usd columns | Critical | Sujan | T6.05 | Done | FJ R-N01 |
| T6.12 | Forward-looking drawdown probabilities, e.g. P(DD > 25% in 5 years), by block bootstrap | Probability table (reference + frontier portfolios; rerun for final candidates) | High | Sujan | T4.16 | Done | Research gap G1 |
| T6.13 | Speed up risk stage (~7 min; Student-t bootstrap refits) | run under ~2 min | Medium | Sujan | — | Not started | Build 2026-10-29 |

## T7 — Expected Shortfall
Stage: risk · Owner: Sujan · Priority: Core · Target: Week 2

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T7.01 | Compute Historical ES at 95% and 99% | var_es.historical ES | Critical | Sujan | T6.02 | Done | PM · BR p.7 |
| T7.02 | Compute ES from Parametric and Monte Carlo approaches | normal, Student-t (closed form) and MC ES | Critical | Sujan | T6.03, T6.04 | Done | PM |
| T7.03 | Compare corresponding VaR and ES outcomes | ES_over_VaR column; research doc §4 | Critical | Sujan | T7.01, T7.02 | Done | PM |
| T7.04 | Explain expected tail losses and data limitations | research doc §2, §4 | Critical | Sujan | T7.03 | Done | PM · BR p.7 |
| T7.05 | ES at 90% and uncertainty bands | ES at 90/95/99 with intervals | Critical | Sujan | T7.01, T7.02 | Done | BR p.5 · DEC D18 |

## T8 — EVT & GARCH
Stage: risk · Owner: Sujan · Priority: Core · Target: Week 2

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T8.01 | Implement and diagnose conditional volatility (GARCH) | risk/evt_garch.fit_garch (GARCH(1,1)-t, rescaled) → p2_garch.csv; persistence 0.99, half-life 68–85 days | High | Sujan | T6.01 | Done | PM · FJ R05 |
| T8.02 | Select EVT/GPD exceedance threshold with justification | choose_threshold: ≥150 exceedances, q<95%, ξ stability; chosen on 2004–2019 → q=0.90 | Critical | Sujan | T8.08 | Done | PM · BR p.7 |
| T8.03 | Fit tail distribution and test threshold sensitivity | threshold_stability (7 thresholds, bootstrap ξ CI) → p2_evt_thresholds.csv + figure | Critical | Sujan | T8.02 | Done | PM · FJ R06 |
| T8.04 | Estimate EVT VaR and ES at high confidence | evt_table → p2_evt.csv (95/99/99.5%) | Critical | Sujan | T8.03 | Done | PM |
| T8.05 | Compare GARCH/EVT and baseline estimates side by side | research doc P2 §5 (EVT vs historical vs GARCH-EVT vs normal) | Critical | Sujan | T8.04, T6.05 | Done | PM · BR p.5 risk dashboard |
| T8.06 | Record instability, model assumptions and sparse-tail caveats | research doc §5: noise above 96%, regime dependence | Critical | Sujan | T8.03 | Done | PM |
| T8.07 | Fit EVT on GARCH-filtered residuals (i.i.d. requirement) | garch_evt (McNeil–Frey) → p2_garch_evt.csv (current + long-run) | High | Sujan | T8.01 | Done | DEC D8 · REV |
| T8.08 | Mean-excess and parameter-stability plots | figures/evt_threshold_d26.png (mean excess + ξ stability) | Critical | Sujan | T6.01 | Done | DEC D8 · FJ EVT quality gate |
| T8.09 | Confidence intervals for ξ, β and EVT VaR/ES | bootstrap intervals for EVT VaR/ES (200 reps on exceedances) | Critical | Sujan | T8.04 | Done | BR p.5 · DEC D18 |
| T8.10 | Rule for EVT at 90% when the quantile falls below the threshold | α ≤ threshold quantile → not applicable (explicit rule + test) | High | Sujan | T8.04 | Done | REV · BR p.5 |
| T8.11 | Evaluate VaR/ES/EVT performance on stress windows (2008, 2020) | T10 doc §4: COVID 4 vs 8 exceptions, 2022 3 vs 8 (GARCH-EVT vs historical) | Critical | Sujan | T10.02 (rolling OOS forecasts) | Done | BR p.7 · R18 · moved to validation stage |
| T8.12 | Feasibility frontier under ERP 3–6% and a resampled frontier | Sensitivity of §4 table | Medium | Sujan | T4.11 | Not started | Research gap G7 |

## T9 — Risk budgeting
Stage: risk · Owner: Sujan · Priority: Supporting · Target: Week 2

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T9.01 | Define marginal and component VaR methodology | risk/attribution.py: Euler, scenario-based (ES exact, VaR band) + normal cross-check | Critical | Sujan | T6.05 | Done | PM · BR p.8 |
| T9.02 | Estimate ETF-level marginal VaR and ES contributions | outputs/tables/p2_attribution.csv (6 portfolios × 7 ETFs × 95/99%) | Critical | Sujan | T9.01 | Done | PM |
| T9.03 | Check contribution aggregation and approximations | sum-to-total test (exact for ES/VaR); normal cross-check within 4 pp | High | Sujan | T9.02 | Done | PM |
| T9.04 | Recommend position-size adjustments and rationale | D27 cap applied in D26 re-selection: SPY 36→20%, EFA 0→9%, XLE 3%, XLK 10% (P2 §6a) | Critical | Sujan | T9.03 | Done | PM · BR p.8 |
| T9.05 | Risk contribution vs capital weight chart | outputs/figures/risk_vs_weight.png | High | Sujan | T9.02 | Done | FJ R07 |
| T9.06 | Set the component-ES concentration limit (draft: no ETF > 40% of ES) | D27 APPROVED 40% (config constraints.component_es_max); 5-cap study research_d27_cap.csv | High | Sujan | T9.02 | Done | Research gap G4 |

## T10 — Backtesting
Stage: validation · Owner: Malindu · Priority: Core · Target: Weeks 2–3

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T10.01 | Define chronological out-of-sample rolling window | D13 1,000-day window, forecasts from 2015-01-02 (history from 2011); validation 2015–19, test 2020 → (locked) | Critical | Malindu | T2.13, T1.07 | Done | PM · FJ VD01 |
| T10.02 | Produce date-aligned VaR forecasts without look-ahead | validation/backtest.rolling_forecasts (data ≤ t−1; GARCH/MC refit 21d) + no-look-ahead unit test | Critical | Malindu | T10.01, T6.05 | Done | PM · BR p.7 |
| T10.03 | Count exceptions against the chosen confidence level | coverage.evaluate (loss > VaR) → backtest_results_validation.csv | Critical | Malindu | T10.02 | Done | PM |
| T10.04 | Perform Kupiec unconditional coverage test | coverage.kupiec (+ x = 0 case, unit test) | Critical | Malindu | T10.03 | Done | PM · BR p.7 |
| T10.05 | Perform Christoffersen independence/coverage tests | coverage.christoffersen (n₁₁ = 0 via xlogy, unit test) | Critical | Malindu | T10.03 | Done | PM · BR p.7 |
| T10.06 | Apply Basel traffic light only for appropriate VaR settings | coverage.basel: 99% only, every 250-day window | Critical | Malindu | T10.03 | Done | PM · BR p.7 |
| T10.07 | Choose the model on validation data only; freeze before test | D28 APPROVED: GARCH-EVT frozen (60e67e3) before test; test run once: 22/17.1 exc, p_cc 0.29, no red window | Critical | Malindu | T10.04, T10.05 | Done | FJ OOS integrity gate |
| T10.08 | Backtest each method and candidate, not only the chosen one | 7 methods × 6 portfolios × 95/99%, validation and test | High | Malindu | T10.03 | Done | REV |
| T10.09 | Window-length sensitivity (500 vs 1000 days) | backtest_window_sensitivity.csv: 1,000 beats 500 on FZ0 for every method | Medium | Malindu | T10.04 | Done | DEC D13 |
| T10.10 | Recompute tests for any user-selected date range (for the app) | coverage.evaluate_table(fc, start, end) | Critical | Malindu | T10.04–T10.06 | Done | BR p.5 sidebar |
| T10.11 | ES / tail-severity check on exceptions | severity ratio + Acerbi–Szekely Z2 per model | Medium | Malindu | T10.03, T7.05 | Done | FJ VD03 |
| T10.12 | Out-of-sample check of D7 limits (set on train, test on held-out) | validation/limits.py → limit_stability.csv: P1-train portfolios keep every D7 limit in 2015–19 and 2020–26; 2026 D26 ES99 2.61% in 2020–26 alone (full-cycle 2.24%) | High | Malindu | T2.13 | Done | Research gap G8 |

## T11 — Stress testing
Stage: validation · Owner: Dewmini · Priority: Core · Target: Weeks 2–3

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T11.01 | Define precise 2008, COVID 2020 and 2022 periods | config stress.windows: GFC, taper 2013, COVID, 2022 (S&P peak/trough dates) | Critical | Dewmini | — | Done | PM · BR p.8 · windows used in scripts/research_d3_d7.py; confirm in D9/T11 |
| T11.02 | Recalculate portfolio performance in historical windows | stress.replay → stress_results.csv (window loss, worst day, recovery) | Critical | Dewmini | T11.01, T4.16 | Done | PM · FJ VD04 |
| T11.03 | Design one plausible hypothetical macro/market shock | D9 APPROVED: stagflation SPY −25%, 10y +200bp, BE +100bp (+ oil/gold variant); D26 loss 16.7% | Critical | Dewmini | T1.08 (D9) | Done | PM · BR p.8 |
| T11.04 | Estimate ETF reactions and document assumptions | stress.factor_betas (SPY, Δ10y, Δbreakeven; monthly OLS) → stress_factor_betas.csv | Critical | Dewmini | T11.03, T2.09 | Done | PM |
| T11.05 | Summarize losses, vulnerabilities and possible adjustments | research doc T11 §2–4 (% NAV and USD) | Critical | Dewmini | T11.02, T11.04 | Done | PM · FJ VD06 |
| T11.06 | Asset-level stress attribution: which ETFs drive the loss | stress_contributions.csv: GFC SPY −10.7pp, AGG +4.2pp; 2022 AGG −8.7pp | High | Dewmini | T11.05 | Done | FJ VD06 joint-loss |
| T11.07 | Correlation / joint losses under stress vs calm | stress_correlations.csv: SPY–EFA 0.85→0.93, SPY–AGG −0.05→+0.06 | High | Dewmini | T11.02 | Done | FJ joint-loss stress |
| T11.08 | AGG rate sensitivity estimated from DGS10 (no external duration data) | AGG β to 10y = −0.049/pp (≈5y duration) | Medium | Dewmini | T2.09 | Done | FJ AGG rate-risk · REV |
| T11.09 | ETF liquidity under stress (e.g. AGG −7.1% on 2008-10-10) | AGG −6.8% 2008-10-10, −4.0% 2020-03-12: liquidity note in T11 §3 | Medium | Dewmini | T2.11 | Done | FJ exit gate · REV |
| T11.10 | Check every scenario against client risk limits | breach_table: no breach; GFC binding (24.5% vs 25%) | Critical | Dewmini | T11.05, T3.04 | Done | FJ VD06 |
| T11.11 | Optional: longer-history crises via disclosed proxies (2000–02, 1994) | Proxy scenario losses | Low | Dewmini | T11.02 | Not started | Research gap G2 |
| T11.12 | Research current macro/market vulnerabilities (oil, Fed, yields, credit, USD, AI valuations, stock–bond correlation) | Design report §1 (tagged V/H/F/N/A, sources dated) | Critical | Dewmini | T11.03 | Done | User brief 2026-10-29 |
| T11.13 | Compare candidate hypothetical scenarios (energy stagflation, AI unwind/recession, term premium, EM/USD) | Design report §2 + recommendation | Critical | Dewmini | T11.12 | Done | User brief |
| T11.14 | Download and disclose new FRED stress factors (DFII10, BAA10Y, Brent/WTI, DTWEXBGS, VIXCLS, DGS2) | 7 FRED stress factors in config + data stage → stress_factors_monthly.csv; disclosed in README and data/README | High | Dewmini | T2.09 | Done | Snapshots saved 2026-10-29; pipeline wiring pending |
| T11.15 | Calibrate central and severe factor shocks from history, current levels and published scenarios | D9 v2 APPROVED 2026-10-29; config stress.hypothetical | Critical | Dewmini | T11.12 | Done | Awaiting D9 v2 approval |
| T11.16 | Six-factor ETF response model: full vs stress betas, SEs; reject unconditional oil→equity mapping | Design report §4.3 | Critical | Dewmini | T11.14 | Done | Research script; module pending |
| T11.17 | Validate factor model by back-casting six episodes (2008, 2020, 2022, Mar 2026) | Back-cast table; XLE/GLD flagged unreliable | High | Dewmini | T11.16 | Done | Research script; test pending |
| T11.18 | Implement validation/hypothetical.py (panel, betas, back-cast, shocks, instant impact) | validation/hypothetical.py + run_hypothetical; 10 tests; stress_hyp_*.csv | Critical | Dewmini | D9 v2 | Done | Design report §8 |
| T11.19 | 12-month scenario path: quarterly rebalancing, costs, D24 spending, liquidity | stress_hyp_paths.csv: A severe worst −19.3%, spending $399k (−6.7% real), AGG 12 yrs of spending | High | Dewmini | T11.18 | Done | Prototype in design report §6.2 |
| T11.20 | Robustness: Monte Carlo over shock ranges and beta SEs; one-at-a-time; XLE/GLD variants | stress_hyp_sensitivity.csv: MC 99th pct 16.1%; SPY ×1.5 → 25.7% (only breach) | High | Dewmini | T11.18 | Done | Prototype in design report §7 |
| T11.21 | Scenario-conditional VaR (GARCH-EVT scaled by stressed volatility) vs D7/D23 triggers | scenario VaR99 2.38% (A severe) > 1.7% → D23 review; explained vs multi-month loss | Medium | Dewmini | T11.18, T10.07 | Done | Design report §6.3 |
| T11.22 | Stress page: scenario/severity selector, factor sliders, contribution waterfall, path chart | pages/4_Stress: scenario/severity selector, factor sliders, waterfall, path chart | High | Dewmini | T11.18, T14 | Done | BR pp.5–6 |
| T11.23 | Feed severe-scenario loss and headroom into memo and T20 decision (gold/XLE hedge test in T4.25) | memo + tear sheet + report §7 report severe losses and headroom; gold/XLE hedge tested as O4 (rejected, T4_25 §2) | Critical | Dewmini | T11.20, T20 | Done | Decision 30% · QA 2026-10-30 |

## T12 — Macro & industry risk (optional)
Stage: validation · Owner: Malindu · Priority: Optional · Target: Week 3

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T12.01 | Identify the important rates, inflation, oil and geopolitical exposures | T11_hypothetical_stress_design.md §1 (rates, inflation, oil, geopolitics) | Medium | Malindu | — | Done | PM · BR p.4 #9 · QA 2026-10-30 |
| T12.02 | Research ETF sensitivity to recession and policy shocks | six-factor betas full + stress samples (stress_hyp_betas.csv) | Medium | Malindu | T12.01 | Done | PM · QA 2026-10-30 |
| T12.03 | Connect industry exposures with the chosen shock scenario | scenarios A/B/C → ETF moves (stress_hyp_shocks.csv) | Medium | Malindu | T12.02 | Done | PM · QA 2026-10-30 |
| T12.04 | Write macro-risk notes for the report and stress test | design report written; report §7 summary; macro-risk notes to finalise with team | Medium | Malindu | T12.03 | In progress | PM · BR p.10 counts in decision score · QA 2026-10-30 |
| T12.05 | Macro context from World Bank / IMF open data only | Partial: context cites IEA/EIA/Fed/news besides IMF/World Bank (brief 9.1) → QA-07 | Low | Malindu | T12.04 | In progress | BR p.9 · QA 2026-10-30 |

## T13 — Innovation extension
Stage: risk/validation · Owner: Sujan · Priority: Optional · Target: Week 3

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T13.01 | Choose one additional model and state a testable hypothesis | Entry in INNOVATION_LOG.md | Medium | Sujan | T6.05 | Not started | PM |
| T13.02 | Specify the method and baseline comparison fairly | Method note | Medium | Sujan | T13.01 | Not started | PM |
| T13.03 | Implement innovation without future-data leakage | GARCH-EVT, t-copula MC, EVT threshold rule, regime VaR built without leakage (rolling data ≤ t−1, test_validation no-look-ahead) | Medium | Sujan | T13.02 | Done | PM · QA 2026-10-30 |
| T13.04 | Backtest innovation and compare standalone methods | GARCH-EVT backtested vs 6 standalone methods (backtest_results_*.csv, T10 doc) | Medium | Sujan | T13.03, T10.04 | Done | PM · QA 2026-10-30 |
| T13.05 | Report gains, failures, limitations and overfitting concerns | INNOVATION_LOG.md I1, I12–I16 with results and failures; audit corrections T4_25 §0 | Medium | Sujan | T13.04 | Done | PM · QA 2026-10-30 |
| T13.06 | Agree the innovation set (rec. #12) and wavelets decision (rec. #13) | Approved list in DECISIONS.md | Medium | All members | — | Not started | REV |
| T13.07 | Evaluate conditional drawdown-at-risk (CDaR) optimisation as innovation | CDaR constraint in optimise.py (D22), INNOVATION_LOG I14 | Medium | Sujan | T4.20 | Done | Review 2026-10-28 · QA 2026-10-30 |

## T14 — Streamlit app
Stage: app · Owner: Malindu · Priority: Core · Target: Weeks 2–3

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T14.01 | Build sidebar: confidence 90/95/99, method and backtest dates | app/components/ui.py sidebar: confidence 90/95/99, VaR method, backtest dates (session state) | Critical | Malindu | T6.07, T10.10 | Done | PM · BR p.5 |
| T14.02 | Build ETF weights and cumulative return portfolio panel | pages/1_Portfolio: weights, growth of $10M vs benchmarks | Critical | Malindu | T4.16 | Done | PM · BR p.5 |
| T14.03 | Add drawdown figure and KPI section | pages/1_Portfolio: drawdown chart with D7 line, KPI table by period | Critical | Malindu | T5.05 | Done | PM · BR p.5 |
| T14.04 | Create VaR/ES/EVT side-by-side risk dashboard | pages/2_Risk: VaR/ES/EVT/GARCH-EVT side by side at chosen confidence, CIs, component ES vs D27 | Critical | Malindu | T8.05 | Done | PM · BR p.5 |
| T14.05 | Build backtesting results and traffic-light panel | pages/3_Backtest: Kupiec, Christoffersen, Basel recomputed on any date range; exception chart | Critical | Malindu | T10.06 | Done | PM · BR p.5 |
| T14.06 | Build historical/hypothetical stress visualization | pages/4_Stress: scenario table, contribution waterfall, 12-month paths, factor sliders | Critical | Malindu | T11.05 | Done | PM · BR p.6 |
| T14.07 | Add Assumptions page and test app interactions | pages/7_Assumptions from docs/ASSUMPTIONS_LIMITATIONS.md; tests/integration/test_app.py (9 pages run) | Critical | Malindu | T15.05 | Done | PM · BR p.6 |
| T14.08 | Shared loader: app reads outputs only, cached; no model code in UI | app/components/data.py: cached loaders, outputs only | High | Malindu | T4.16 | Done | FJ app 03 · AGENTS.md |
| T14.09 | Decision & tear-sheet page (P3, limits, monitoring triggers) | pages/6_Decision: P3, suitability gate, validation, triggers | High | Malindu | T20.04 | Done | FJ app 08 |
| T14.10 | AI disclosure & sources page | pages/8_Disclosure: AI disclosure, data sources, decision log | Medium | Malindu | T18.05 | Done | FJ app 10 |
| T14.11 | Export & reproducibility page (CSV/figures download) | download buttons on Decision page (CSV / Markdown) | Low | Malindu | T14.02–T14.06 | Done | FJ app 11 |
| T14.12 | Plain-language labels for a non-technical committee (units, horizon on every number) | UI copy review | High | Malindu | T14.01–T14.07 | In progress | BR p.5 · masterclass |
| T14.13 | What-if sliders on decision page: spending, growth, costs, ERP → required return, gap, sustainable spending | pages/5_Sustainability: what-if sliders (spending, growth, costs, inflation, ERP) + trade-off + recovery | Medium | Malindu | T4.21 | Done | Team request 2026-10-28 |
| T14.14 | D23 monitoring status in the app: current step + drawdown, rolling ES99, Basel zone (as of snapshot end); watch / review / act lines on the drawdown chart | Home + Decision panel, Portfolio chart; `limits.ladder_step` + 9 unit tests; signals recomputed independently (DD 1.69%, ES99 1.40%, Basel green); GARCH-EVT VaR99 next-day tile (0.94% vs 1.7%, shown not a trigger) and Basel relabelled as model check (P1-train weights) | Medium | Malindu | T20.05 | Done (D38 rule PROPOSED) | User request 2026-10-30 |

## T15 — Assumptions & Limitations
Stage: docs/app · Owner: Raveena + Dewmini · Priority: Core · Target: Week 3

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T15.01 | Document data universe, dates, sourcing and limitations | Data section | Critical | Raveena + Dewmini | T2.11 | In progress | PM · FRED notes written |
| T15.02 | Explain distribution, volatility and dependence assumptions | A&L '## Models' (non-normality, MC marginals, weight conventions, CAPM, stable correlations) | Critical | Raveena + Dewmini | T6.08 | Done | PM · QA-01: section '## Models' empty |
| T15.03 | Explain unseen shocks, low liquidity and tail-data scarcity | A&L '## Tail / EVT uncertainty' + '## Not captured' (unseen crises, liquidity, regime change, costs, university side) | Critical | Raveena + Dewmini | T8.06, T11.09 | Done | PM · QA-01: sections '## Tail / EVT uncertainty', '## Not captured' empty |
| T15.04 | Clarify what backtesting can and cannot establish | A&L '## Backtesting scope' (power, what is out of sample, first-day misses) | Critical | Raveena + Dewmini | T10.07 | Done | PM · QA-01: section '## Backtesting scope' empty |
| T15.05 | Ensure app and report state identical assumptions | app/pages/7_Assumptions.py renders docs/ASSUMPTIONS_LIMITATIONS.md (same text as report) | Critical | Raveena + Dewmini | T15.01–T15.04 | Done | PM · FJ limitations audit · QA 2026-10-30 |
| T15.06 | Add return-objective, benchmark and risk-limit assumptions (CAPM gold, rf level, ERP, USD spending, tax, in-sample calibration) | docs/ASSUMPTIONS_LIMITATIONS.md updated | High | Raveena + Dewmini | — | Done | Review 2026-10-28 |

## T16 — Written deliverables
Stage: decision/docs · Owner: Raveena · Priority: Core · Target: Week 3

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T16.01 | Outline 7–15 page technical report based on actual results | docs/deliverables/report/technical_report.md: 11 sections + appendix (draft, team review) | Critical | Raveena | T1.07 | In progress | PM · BR p.6 |
| T16.02 | Complete methods, evidence, tests and limitations writeup | report draft: methods, evidence, tests, limitations (team to edit and own) | Critical | Raveena | T20.04 | In progress | PM |
| T16.03 | Create concise one-page portfolio tear sheet | docs/deliverables/tear_sheet/tear_sheet.md (draft, team review) | Critical | Raveena | T20.04 | In progress | PM · BR p.6 |
| T16.04 | Write one-page investment committee decision memo | memo drafted; verdict ACCEPT confirmed by team (D34); wording to be finalised by team | Critical | Raveena | T20.04 | Done | PM · BR p.8 |
| T16.05 | Cross-check all numbers between report, memo and app | scripts/check_deliverables.py: 30 figures vs outputs, 0 mismatches (caught one rounding error) | Critical | Raveena | T16.02–T16.04, T14.* | Done | PM · FJ calculation audit |
| T16.06 | Data sources and cleaning steps section | report §3 data sources and cleaning (draft) | Critical | Raveena | T2.11 | In progress | BR p.6 |
| T16.07 | Report sections: return objective & sustainable spending; benchmark and risk-limit research (appendix) | report §2, §4.4 return objective, spending and risk-limit research (draft) | High | Raveena | T20.04 | In progress | DEC D3, D7, D12 |

## T17 — Repository & reproducibility
Stage: — · Owner: Malindu · Priority: Core · Target: Week 3

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T17.01 | Finalize organized, documented GitHub repository | Public / judge-accessible repo | Critical | Malindu | T1.01 | Not started | PM · BR p.6 |
| T17.02 | Pin package versions and supply reproducible setup | requirements.txt exact pins (916105a); clean venv install from GitHub OK 2026-10-30 | Critical | Malindu | T1.02 | Done | PM · QA 2026-10-30 |
| T17.03 | Provide one-command Streamlit run instructions | README quick start (streamlit run app/Home.py) + full rerun (python run_all.py --app) | Critical | Malindu | T14.* | Done | PM · BR p.6 · entry point exists |
| T17.04 | Test clean installation and reproduce key results | clean clone + pinned venv: run_all 59.5 min, 133 tests pass, 54/54 pipeline tables identical after fixing one stale snapshot table (REPRODUCIBILITY.md) | Critical | Malindu | T17.02 | Done | PM · QA 2026-10-30 |
| T17.05 | Log reproducibility evidence and known environment issues | tracking/validation/REPRODUCIBILITY.md (results + known environment issues) | High | Malindu | T17.04 | Done | PM |
| T17.06 | Decide which reference files to publish (third-party decks) | .gitignore rule: decks kept local, removed from history | Medium | Malindu | — | Done | REV |
| T17.07 | Optional: deploy to Streamlit Community Cloud | Public app URL (D16) | Low | Malindu | T17.04 | Not started | BR p.6 · DEC D16 |
| T17.08 | First git commit and judge-accessible GitHub remote | GitHub remote, branch version-1 pushed; URL in README | Critical | Malindu | T17.06 | Done | BR p.6 · Review |
| T17.09 | Make research evidence reproducible from the one-command run (run_all --research) | run_all flag + README | High | Malindu | T17.03 | Not started | Review: scripts/ not in pipeline |

## T18 — AI disclosure & validation log
Stage: — · Owner: Malindu · Priority: Core · Target: Ongoing

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T18.01 | Keep a running list of AI tools and their purposes | docs/AI_DISCLOSURE.md: 11 rows covering all stages (2026-10-30) | Critical | Malindu | — | Done | PM · BR p.8 |
| T18.02 | Record which code, figures or text used AI assistance | material components column filled per stage | Critical | Malindu | — | Done | PM · BR p.8 |
| T18.03 | Document manual verification, corrections and tests | HUMAN_VALIDATION_LOG.md | Critical | Malindu | — | In progress | PM · BR p.8 |
| T18.04 | Review completeness of the log before submission | Signed-off log | Critical | Malindu | T18.01–T18.03 | Not started | PM |
| T18.05 | Use the brief's four disclosure columns exactly | brief's four columns used exactly | High | Malindu | — | Done | BR p.8 |
| T18.06 | Every member can explain each module (judging rule) | Walk-through sessions per stage | High | All members | each stage | Not started | BR p.9 |
| T18.07 | Record Claude Code use to date in the brief's four columns (tool, purpose, human validation, material components) | Claude Code use recorded to 2026-10-30 | Critical | Malindu | — | Done | BR p.8 · Review |
| T18.08 | Team sign-off of every HUMAN_VALIDATION_LOG entry (9 unsigned on 2026-10-28) | Signed log | Critical | All members | — | Not started | BR p.8–9 |

## T19 — Pitch & Q&A prep
Stage: — · Owner: All members · Priority: Conditional · Target: If finalist

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T19.01 | Create a 10–12 minute presentation storyline and deck | Deck | Medium | All members | T16.04 | Not started | PM · BR p.6 |
| T19.02 | Assign presenters and rehearse timing | Rehearsal plan | Medium | All members | T19.01 | Not started | PM |
| T19.03 | Prepare judges' Q&A on assumptions, VaR and crisis results | Q&A bank | Medium | All members | T19.01 | Not started | PM |
| T19.04 | Run mock Q&A and refine explanations | Mock session notes | Medium | All members | T19.03 | Not started | PM |

## T20 — Decision gate & final recommendation (P3)
Stage: decision · Owner: All members · Priority: Core · Target: Week 3

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T20.01 | Assemble committee evidence: six panels (allocation, return, loss limit, tail, model trust, governance) | evidence: T4_25 doc + p3_summary (allocation, return, loss limit, tail, model trust, governance) | Critical | All members | T5.05, T8.05, T10.07, T11.10 | Done | FJ VD07 · masterclass |
| T20.02 | Suitability gate: validated and within client limits? | suitability gate: T4_25 §3 conditions; O6 passes all mandatory | Critical | All members | T20.01, T3.09 | Done | FJ VD08 |
| T20.03 | Revise & retest loop when the gate fails | revise & retest loop: audit 2026-10-29 (D31 withdrawn → D31 v2, D32, D33) | High | All members | T20.02 | Done | FJ VD09 |
| T20.04 | Final P3 recommendation: weights, horizon, expected real return, downside | decision stage → outputs/p3_decision (O6: AGG 61.1, SPY 18.4, XLK 10, EFA 7.2, XLE 3.0, GLD 0.4; 5.80%, $265k spending) | Critical | All members | T20.02 | Done | FJ VD10 · BR p.8 |
| T20.05 | Monitoring triggers and exit / de-risking rules | p3_triggers.csv: D23 ladder + Basel model check + quarterly rebalance + annual review | High | All members | T20.04 | Done | FJ VD10 |
| T20.06 | Drawdown ↔ spending trade-off table in memo and app | p3_tradeoff.csv: frontier spending vs drawdown vs P(DD), O6 marked (app widget pending T14) | High | All members | T3.19 | Done | Research §4 |
| T20.07 | Walk-forward (rolling-origin) validation of the selection rule (O1 vs O2), origins 2009–2021, CMA as of each origin | research_walkforward_*.csv: 6 origins 2008–2023; D7 drawdown held every segment; chained 7.3%/yr, Sharpe 0.89, DD −16.4% (policy 0.75, −19.2%); D27×D7 conflict at 2008/2011 noted | Critical | Malindu | T4.25 | Done | Selection-bias precaution 2026-10-29 |
| T20.08 | Recalibrate D23 rolling-ES99 watch trigger (fires on 26% of days at 2.0%) | Approved 2026-10-30: watch rolling ES99 2.5% (was 2.0%; 20% → 9.6% of days) | Medium | All members | T10.12 | Done | Limit-stability finding 2026-10-29 |
| T20.09 | Endowment sustainability & recovery stress test: 15/20/25% falls, 1/3/5/7-year and lost-decade recoveries, D24 at 2.8%, costs, taxes, inflation; market view; bootstrap | sustainability_*.csv + research_t425_eval_sustainability_*.csv | Critical | All members | T20.10 | Done | User request 2026-10-29 |
| T20.10 | Audit fix: 5-year drawdown test seed-tuned (4k paths) → 32k paths, block-length sensitivity; D30 2.8% propagated to hurdle and spending | Pipeline rerun, D26 re-selected | Critical | Malindu | — | Done | Audit 2026-10-29 |

## T21 — Quality gates & compliance QA
Stage: — · Owner: Malindu (coordinates) · Priority: Core · Target: Ongoing

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T21.01 | Compliance check after every stage (R1–R20) | COMPLIANCE_MATRIX.md updated | Critical | Malindu (coordinates) | each stage | In progress | FJ N01 governance · REV |
| T21.02 | Out-of-sample integrity gate: no leakage, frozen test, trial log | D5 split, as-of CMA, rolling forecasts data ≤ t−1 (unit test), D28 rule frozen in commit 60e67e3 before test run, walk-forward | Critical | Malindu (coordinates) | T2.13 | Done | FJ OOS integrity gate · QA 2026-10-30 |
| T21.03 | Calculation audit: units, signs, horizon consistent across stages | QA independent recomputation: returns, VaR/ES, drawdown, CAPM, required return, Kupiec, Basel, look-ahead all match (QA report §3) | Critical | Malindu (coordinates) | each stage | Done | FJ calculation audit · QA 2026-10-30 |
| T21.04 | App / code QA: required panels, one-command run, tests green | 9 pages run in workspace and fresh clone; sidebar controls; README current; backtest 90% → 99% fallback (QA-09, optional) | Critical | Malindu (coordinates) | T14.* | Done | FJ app/code QA · QA 2026-10-30 |
| T21.05 | Update FigJam board to match approved decisions (edit list in docs/research/PROJECT_REVIEW_2026-10-28.md §4) | Board matches MODEL_DESIGN.md | High | Malindu (coordinates) | — | Not started | DEC D14, D20 |
| T21.06 | QA-01 Fill the four empty Assumptions & Limitations sections and update stale text (63-day blocks → D32 126; 2.8% → 2.65%) | ASSUMPTIONS_LIMITATIONS.md: Models, Tail/EVT, Backtesting scope, Not captured written; 5 stale lines fixed (D30, D32, AGG −6.8%) | Critical | All members | T15.02–T15.04 | Done | QA audit 2026-10-30 |
| T21.07 | QA-02 Quantify diversification benefit: undiversified vs portfolio VaR/ES (QA estimate O6: −29% VaR99, −25% ES99), diversification ratio, risk vs weight; add to report, tear sheet, app Risk page | attribution.diversification_table → p2_diversification.csv; O6 VaR99 −28.8%, ES99 −24.5%, DR 1.38; report §5, tear sheet, Risk page, p3_summary; test | Critical | Dewmini | T4.14 | Done | QA audit 2026-10-30 |
| T21.08 | QA-03 Update README: status, app pages, run time (~2 h full pipeline), quick start, troubleshooting (Windows path length, numpy < 2) | README rewritten: recommendation, run commands, run time, troubleshooting, 9 app pages, stages, sources | High | Malindu | T17.03 | Done | QA audit 2026-10-30 |
| T21.09 | QA-04 Judge quick start: decide whether to ship a results snapshot so the app opens without the 2-hour pipeline (outputs/ is gitignored) | D16 approved: outputs/ committed (048107b); fresh GitHub clone → all 9 app pages run with no pipeline (test_app.py, clean venv) | High | All members | D16 | Done | QA audit 2026-10-30 |
| T21.10 | QA-06 Tear sheet: add the recommendation (ACCEPT, D34) and fit one page; memo fit one page (709 words now) | recommendation line added to tear sheet (D34); memo condensed to one A4 page at 10.5pt (2026-10-30, 645 words, A4 PDF render); tear sheet condensed to one A4 page at 10.5pt (584 words); team to re-check in the final PDF layout | High | Raveena | T16.03, T16.04 | Done | QA audit 2026-10-30 |
| T21.11 | QA-07 Data-source compliance: macro context in memo/report from IMF/World Bank; IEA/EIA/Fed/news kept as disclosed background in research docs only | memo/report/README wording | Medium | Raveena | T12.05 | Not started | QA audit 2026-10-30 |
| T21.12 | QA-08 Report: convert to PDF, verify 7–15 pages, rerun scripts/check_deliverables.py after edits | report PDF | Critical | Raveena | T16.02 | Not started | QA audit 2026-10-30 |
| T21.13 | QA-09 Optional: backtest forecasts at 90% so the sidebar 90% applies to the backtest panel | backtest_forecasts_* with 0.90 | Low | Malindu | T10 | Not started | QA audit 2026-10-30 |
| T21.14 | QA-10 Record clean-install reproducibility result (diff of key outputs vs original) in a reproducibility log | REPRODUCIBILITY.md: clean run reproduces every pipeline output exactly | High | Malindu | T17.04 | Done | QA audit 2026-10-30 |
| T21.06 | Add R16–R20 to compliance matrix; update every status with evidence | COMPLIANCE_MATRIX.md | Critical | Malindu | — | Done | Review 2026-10-28 |
| T21.07 | Record innovations to date in the innovation log | INNOVATION_LOG.md | High | Sujan | — | Done | Review 2026-10-28 |
| T21.08 | Generate both Excel trackers from the repo tracker (tracking/export_excel.py) | tracking/exports/*.xlsm | High | Malindu | — | Done | Review 2026-10-28 |
