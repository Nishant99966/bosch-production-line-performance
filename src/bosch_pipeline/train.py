from __future__ import annotations
import argparse
import json
from pathlib import Path
import pandas as pd
from .config import ensure_output_dirs, load_config
from .io import load_frame
from .model import fit_full, train_with_validation

def run(config_path: str) -> None:
    cfg = load_config(config_path)
    ensure_output_dirs(cfg)
    processed = Path(cfg["paths"]["processed_dir"])
    artifacts = Path(cfg["paths"]["artifacts_dir"])
    train = load_frame(processed / "train_features.parquet")
    test = load_frame(processed / "test_features.parquet")
    y = train.pop("Response").astype("int8")
    train.pop("Id")
    test_ids = test.pop("Id")
    missing = [c for c in train if c not in test]
    if missing:
        raise ValueError(f"Test feature schema missing columns: {missing[:10]}")
    test = test[train.columns]
    print(f"Training rows: {len(train):,}; features: {train.shape[1]:,}; positive rate: {y.mean():.5f}")
    _, metrics = train_with_validation(train, y, cfg["validation"], cfg["model"])
    print(json.dumps(metrics, indent=2))
    model = fit_full(train, y, cfg["model"], metrics["best_iteration"])
    model.booster_.save_model(str(artifacts / "model.txt"))
    importance = pd.DataFrame({
        "feature": train.columns,
        "importance_gain": model.booster_.feature_importance(importance_type="gain"),
        "importance_split": model.booster_.feature_importance(importance_type="split"),
    }).sort_values("importance_gain", ascending=False)
    importance.to_csv(artifacts / "feature_importance.csv", index=False)
    probs = model.predict_proba(test)[:, 1]
    result = pd.DataFrame({"Id": test_ids.to_numpy(),
                           "Response": (probs >= metrics["optimal_threshold"]).astype("int8")})
    result.to_csv(artifacts / "submission.csv", index=False)
    metrics["test_predicted_positive_rate"] = float(result["Response"].mean())
    metrics["feature_count"] = int(train.shape[1])
    (artifacts / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"Saved artifacts to {artifacts}")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs.yaml")
    run(parser.parse_args().config)

if __name__ == "__main__":
    main()
