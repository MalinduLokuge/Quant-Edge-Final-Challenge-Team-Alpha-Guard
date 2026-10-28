"""Project paths and settings loader shared by every stage."""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
CONFIG_FILE = ROOT / "config" / "settings.yaml"
DATA_RAW = ROOT / "data" / "raw"
DATA_EXTERNAL = ROOT / "data" / "external"
DATA_PROCESSED = ROOT / "data" / "processed"
OUTPUT_TABLES = ROOT / "outputs" / "tables"
OUTPUT_REPORTS = ROOT / "outputs" / "reports"


def load_settings(path: Path = CONFIG_FILE) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)
