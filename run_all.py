"""QuantEdge 1.0 — master orchestration entry point.

Regenerates every result from the raw snapshot in one command, stage by stage:

    python run_all.py                 # run all stages, write to data/processed/ and outputs/
    python run_all.py --app           # run all stages, then launch the Streamlit app
    python run_all.py --only risk     # re-run one stage (uses saved upstream outputs)
    python run_all.py --refresh-data  # re-download prices instead of using the snapshot

Stages are the code architecture; they are NOT the brief's methodology Layers 1-5.
The Streamlit app never recomputes models; it only reads outputs/ and data/processed/.
"""
from __future__ import annotations

import argparse
import importlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

# Ordered stage registry. A stage is runnable once its package exposes run().
STAGES: dict[str, str] = {
    "data": "quantedge.data",
    "portfolio": "quantedge.portfolio",
    "risk": "quantedge.risk",
    "validation": "quantedge.validation",
    "decision": "quantedge.decision",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--only", choices=STAGES, help="run a single stage")
    parser.add_argument("--app", action="store_true", help="launch Streamlit after the pipeline")
    parser.add_argument("--refresh-data", action="store_true", help="re-download prices (needs yfinance)")
    args = parser.parse_args()

    for key in [args.only] if args.only else STAGES:
        module = importlib.import_module(STAGES[key])
        if not hasattr(module, "run"):
            if args.only:
                raise NotImplementedError(f"Stage '{key}' has no run() yet.")
            print(f"[run_all] {key}: not implemented yet — stopping here.")
            break
        print(f"[run_all] {key}: running")
        module.run(refresh=args.refresh_data) if key == "data" else module.run()

    if args.app:
        return subprocess.call([sys.executable, "-m", "streamlit", "run", str(ROOT / "app" / "Home.py")])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
