from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import pandas as pd
from .io import read_header

@dataclass
class _RunningStats:
    count: np.ndarray
    sum: np.ndarray
    sumsq: np.ndarray
    missing: np.ndarray

def _empty(n: int) -> _RunningStats:
    return _RunningStats(*(np.zeros(n, dtype=np.float64) for _ in range(4)))

def _update(stats: _RunningStats, arr: np.ndarray) -> None:
    finite = np.isfinite(arr)
    clean = np.where(finite, arr, 0.0)
    stats.count += finite.sum(axis=0)
    stats.sum += clean.sum(axis=0)
    stats.sumsq += (clean * clean).sum(axis=0)
    stats.missing += (~finite).sum(axis=0)

def score_numeric_features(train_numeric_path: str | Path, chunk_size: int,
                           min_coverage: float) -> pd.DataFrame:
    """Score numeric columns with streaming class-conditional statistics."""
    columns = read_header(train_numeric_path)
    feature_cols = [c for c in columns if c not in {"Id", "Response"}]
    pos, neg = _empty(len(feature_cols)), _empty(len(feature_cols))
    n_pos = n_neg = 0
    for chunk in pd.read_csv(train_numeric_path, usecols=["Response", *feature_cols],
                             chunksize=chunk_size, low_memory=False):
        y = chunk.pop("Response").to_numpy(dtype=np.int8)
        x = chunk.to_numpy(dtype=np.float64, copy=False)
        pos_mask, neg_mask = y == 1, y != 1
        if pos_mask.any():
            _update(pos, x[pos_mask])
            n_pos += int(pos_mask.sum())
        if neg_mask.any():
            _update(neg, x[neg_mask])
            n_neg += int(neg_mask.sum())
    pos_mean = pos.sum / np.maximum(pos.count, 1.0)
    neg_mean = neg.sum / np.maximum(neg.count, 1.0)
    pos_var = np.maximum(pos.sumsq / np.maximum(pos.count, 1.0) - pos_mean**2, 0.0)
    neg_var = np.maximum(neg.sumsq / np.maximum(neg.count, 1.0) - neg_mean**2, 0.0)
    pooled_std = np.sqrt((pos_var + neg_var) / 2.0) + 1e-12
    pos_missing = pos.missing / max(n_pos, 1)
    neg_missing = neg.missing / max(n_neg, 1)
    coverage = (pos.count + neg.count) / max(n_pos + n_neg, 1)
    mean_shift = np.abs(pos_mean - neg_mean) / pooled_std
    missing_shift = np.abs(pos_missing - neg_missing)
    score = 2.0 * missing_shift + np.nan_to_num(mean_shift, nan=0.0, posinf=0.0) * np.sqrt(coverage)
    result = pd.DataFrame({"feature": feature_cols, "score": score, "coverage": coverage,
                           "missing_shift": missing_shift, "standardized_mean_shift": mean_shift})
    return result[result["coverage"] >= min_coverage].sort_values(
        "score", ascending=False, kind="stable").reset_index(drop=True)
