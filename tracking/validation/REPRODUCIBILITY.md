# Reproducibility log (T17.04, T17.05, QA-10)

## Clean-install test, 2026-10-30
**Setup:**
- Fresh `git clone` of `version-1` from GitHub at commit `916105a`.
- New Python 3.12.10 virtual environment.
- `pip install -r requirements.txt` with exact pins. Solvers present: CLARABEL, ECOS, OSQP, SCIPY, SCS.

**Run:** `python run_all.py` (all stages from the committed data snapshots, no internet).
- Finished in **59 min 34 s**, exit 0.
- `pytest`: 133 passed.

**Result: every pipeline output reproduces exactly.**
- **52 of 54 tables:** identical (max absolute difference < 1e-9, no text differences).
- **`limit_stability.csv`:** differed in one column (share of days above the rolling-ES watch level). The committed copy had been generated before D23's watch level changed from 2.0% to 2.5%. It was regenerated; the difference is now 0.0. **This was a stale-snapshot error that the clean run caught.**
- **`p3_summary.csv`:** the snapshot has 3 extra rows (diversification benefit, QA-02), added after commit `916105a`. All shared rows are identical.
- **Research tables** (`research_*.csv`) are produced by the scripts in `scripts/`, not by `run_all.py`. They were not part of this test (T17.09).

**Fresh-clone quick start (D16):** a clean clone at `048107b` with no pipeline run. All 9 Streamlit pages run (`tests/integration/test_app.py`, 9 passed).

## Known environment issues
| Issue | Cause | Fix |
|---|---|---|
| Windows install fails with "No such file or directory" deep inside `site-packages/streamlit` | Path longer than 260 characters when the repo or venv sits in a long folder | Use a short path (e.g. `C:\qe`) or enable Windows long paths |
| `pyarrow requires NumPy 2.0` in the app | pyarrow ≥ 21 needs numpy 2, but cvxpy 1.5 needs numpy 1.x | Pinned `pyarrow==19.0.1` |
| Importing scikit-learn before cvxpy crashed Python | Binary conflict | Ledoit–Wolf is implemented in-house; scikit-learn is not a dependency |
| Full pipeline takes 1–2 h | Daily rolling backtests (2015–2026, 7 methods × 6 portfolios) | Committed results snapshot (D16) for the app; `--only <stage>` for partial reruns |
