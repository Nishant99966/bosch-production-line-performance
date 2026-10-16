from __future__ import annotations

from pathlib import Path
from typing import Any
import yaml


def load_config(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if not isinstance(cfg, dict):
        raise ValueError(f"Invalid config: {path}")
    return cfg


def ensure_output_dirs(cfg: dict[str, Any]) -> None:
    for key in ("processed_dir", "artifacts_dir"):
        Path(cfg["paths"][key]).mkdir(parents=True, exist_ok=True)
