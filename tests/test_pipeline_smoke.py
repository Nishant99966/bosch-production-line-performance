from pathlib import Path
import subprocess
import sys
import pandas as pd
import yaml
from bosch_pipeline.prepare import run as prepare_run
from bosch_pipeline.train import run as train_run

def test_end_to_end_synthetic(tmp_path: Path):
    raw, processed, artifacts = (
        tmp_path / "raw", tmp_path / "processed", tmp_path / "artifacts")
    subprocess.run([sys.executable, "scripts/make_synthetic_data.py",
                    "--output-dir", str(raw), "--rows", "800"], check=True)
    cfg = {
        "paths": {"raw_dir": str(raw), "processed_dir": str(processed),
                  "artifacts_dir": str(artifacts)},
        "io": {"chunk_size": 200},
        "features": {"numeric_top_k": 8, "include_categorical": True,
                     "categorical_top_k": 3, "min_numeric_coverage": 0.0,
                     "min_categorical_coverage": 0.0},
        "validation": {"strategy": "stratified",
                       "validation_fraction": 0.25, "random_state": 42},
        "model": {"n_estimators": 40, "learning_rate": 0.08, "num_leaves": 15,
                  "max_depth": -1, "min_child_samples": 10, "subsample": 0.9,
                  "colsample_bytree": 0.9, "reg_alpha": 0.0, "reg_lambda": 0.5,
                  "random_state": 42, "n_jobs": 2, "early_stopping_rounds": 10}
    }
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    prepare_run(str(path))
    train_run(str(path))
    submission = pd.read_csv(artifacts / "submission.csv")
    assert list(submission.columns) == ["Id", "Response"]
    assert set(submission["Response"].unique()).issubset({0, 1})
    assert (artifacts / "model.txt").exists()
    assert (artifacts / "metrics.json").exists()
