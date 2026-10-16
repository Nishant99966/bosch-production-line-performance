from __future__ import annotations

import numpy as np
from sklearn.metrics import matthews_corrcoef


def optimize_mcc_threshold(y_true: np.ndarray, y_prob: np.ndarray,
                           max_candidates: int = 2000) -> tuple[float, float]:
    """Return the threshold yielding the highest validation MCC."""
    y_true = np.asarray(y_true, dtype=np.int8)
    y_prob = np.asarray(y_prob, dtype=float)
    if y_true.shape[0] != y_prob.shape[0]:
        raise ValueError("y_true and y_prob must have equal length")
    if y_true.size == 0:
        raise ValueError("Cannot optimize threshold on empty arrays")
    unique = np.unique(y_prob)
    candidates = unique if unique.size <= max_candidates else np.unique(
        np.quantile(y_prob, np.linspace(0.0, 1.0, max_candidates)))
    candidates = np.unique(np.concatenate(
        [candidates, np.array([0.01, 0.02, 0.05, 0.1, 0.2, 0.5])]))
    candidates = candidates[(candidates >= 0.0) & (candidates <= 1.0)]
    best_threshold, best_mcc = 0.5, -1.0
    for threshold in candidates:
        mcc = matthews_corrcoef(y_true, (y_prob >= threshold).astype(np.int8))
        if mcc > best_mcc:
            best_mcc, best_threshold = float(mcc), float(threshold)
    return best_threshold, best_mcc
