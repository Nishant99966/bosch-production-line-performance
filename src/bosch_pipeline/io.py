from __future__ import annotations

from pathlib import Path
from typing import Iterable
import pandas as pd

REQUIRED_FILES = ("train_numeric.csv", "train_date.csv", "test_numeric.csv", "test_date.csv")


def validate_raw_data(raw_dir: str | Path, include_categorical: bool = True) -> None:
    raw_dir = Path(raw_dir)
    required = list(REQUIRED_FILES)
    if include_categorical:
        required.extend(["train_categorical.csv", "test_categorical.csv"])
    missing = [name for name in required if not (raw_dir / name).exists()]
    if missing:
        joined = "\n  - ".join(missing)
        raise FileNotFoundError(
            f"Missing required raw files in {raw_dir}:\n  - {joined}\n"
            "Download/extract the Kaggle competition data first."
        )


def read_header(path: str | Path) -> list[str]:
    return list(pd.read_csv(path, nrows=0).columns)


def iter_csv(path: str | Path, chunk_size: int, usecols: Iterable[str] | None = None,
             dtype: dict[str, str] | None = None):
    yield from pd.read_csv(path, chunksize=chunk_size,
                           usecols=list(usecols) if usecols is not None else None,
                           dtype=dtype, low_memory=False)


def save_frame(frame: pd.DataFrame, path: str | Path) -> Path:
    path = Path(path)
    try:
        frame.to_parquet(path, index=False)
        return path
    except ImportError:
        fallback = path.with_suffix(".pkl")
        frame.to_pickle(fallback)
        return fallback


def load_frame(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if path.exists():
        try:
            return pd.read_parquet(path)
        except ImportError:
            pass
    fallback = path.with_suffix(".pkl")
    if fallback.exists():
        return pd.read_pickle(fallback)
    raise FileNotFoundError(f"Prepared dataset not found: {path} or {fallback}")
