from __future__ import annotations
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import train_test_split
from .metrics import optimize_mcc_threshold

def make_split(frame: pd.DataFrame, y: pd.Series, strategy: str,
               validation_fraction: float, random_state: int) -> tuple[np.ndarray, np.ndarray]:
    indices = np.arange(len(frame))
    if strategy == "chronological" and "start_time" in frame.columns:
        order = np.argsort(frame["start_time"].fillna(np.inf).to_numpy(), kind="stable")
        cut = max(1, int(len(frame) * (1.0 - validation_fraction)))
        return order[:cut], order[cut:]
    if strategy == "stratified":
        tr, va = train_test_split(indices, test_size=validation_fraction,
                                  random_state=random_state, stratify=y)
        return np.asarray(tr), np.asarray(va)
    raise ValueError(f"Unknown validation strategy: {strategy}")

def train_with_validation(x: pd.DataFrame, y: pd.Series,
                          validation_cfg: dict, model_cfg: dict):
    tr, va = make_split(x, y, strategy=validation_cfg["strategy"],
                        validation_fraction=float(validation_cfg["validation_fraction"]),
                        random_state=int(validation_cfg["random_state"]))
    y_tr, y_va = y.iloc[tr], y.iloc[va]
    pos = max(int(y_tr.sum()), 1)
    neg = max(len(y_tr) - pos, 1)
    params = dict(model_cfg)
    rounds = int(params.pop("early_stopping_rounds", 100))
    model = lgb.LGBMClassifier(objective="binary", scale_pos_weight=neg / pos,
                               verbosity=-1, **params)
    model.fit(x.iloc[tr], y_tr, eval_set=[(x.iloc[va], y_va)],
              eval_metric="binary_logloss",
              callbacks=[lgb.early_stopping(rounds, verbose=False)])
    p = model.predict_proba(x.iloc[va])[:, 1]
    threshold, mcc = optimize_mcc_threshold(y_va.to_numpy(), p)
    metrics = {
        "validation_mcc": float(mcc),
        "optimal_threshold": float(threshold),
        "roc_auc": float(roc_auc_score(y_va, p)) if y_va.nunique() > 1 else None,
        "average_precision": float(average_precision_score(y_va, p)) if y_va.nunique() > 1 else None,
        "best_iteration": int(model.best_iteration_ or model_cfg["n_estimators"]),
        "validation_strategy": validation_cfg["strategy"],
        "train_rows": int(len(tr)), "validation_rows": int(len(va)),
        "positive_rate_train": float(y_tr.mean()),
        "positive_rate_validation": float(y_va.mean()),
    }
    return model, metrics

def fit_full(x: pd.DataFrame, y: pd.Series, model_cfg: dict, best_iteration: int):
    pos = max(int(y.sum()), 1)
    neg = max(len(y) - pos, 1)
    params = dict(model_cfg)
    params.pop("early_stopping_rounds", None)
    params["n_estimators"] = max(int(best_iteration), 1)
    model = lgb.LGBMClassifier(objective="binary", scale_pos_weight=neg / pos,
                               verbosity=-1, **params)
    model.fit(x, y)
    return model
