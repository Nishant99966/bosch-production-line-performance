from __future__ import annotations
import argparse
import json
from pathlib import Path
from .config import ensure_output_dirs, load_config
from .features import (add_temporal_order_features, build_categorical_features,
                       build_date_features, build_numeric_features, select_categorical_columns)
from .io import save_frame, validate_raw_data
from .numeric_selection import score_numeric_features

def run(config_path: str) -> None:
    cfg = load_config(config_path)
    ensure_output_dirs(cfg)
    raw = Path(cfg["paths"]["raw_dir"])
    processed = Path(cfg["paths"]["processed_dir"])
    chunk_size = int(cfg["io"]["chunk_size"])
    fcfg = cfg["features"]
    include_cat = bool(fcfg.get("include_categorical", True))
    validate_raw_data(raw, include_categorical=include_cat)
    print("[1/6] Scoring numeric features...")
    scores = score_numeric_features(raw / "train_numeric.csv", chunk_size,
                                    float(fcfg.get("min_numeric_coverage", 0.0)))
    selected_num = scores.head(int(fcfg["numeric_top_k"]))["feature"].tolist()
    scores.to_csv(processed / "numeric_feature_scores.csv", index=False)
    print("[2/6] Building numeric blocks...")
    tr_num = build_numeric_features(raw / "train_numeric.csv", selected_num, chunk_size, True)
    te_num = build_numeric_features(raw / "test_numeric.csv", selected_num, chunk_size, False)
    print("[3/6] Compressing date columns...")
    tr_date = build_date_features(raw / "train_date.csv", chunk_size)
    te_date = build_date_features(raw / "test_date.csv", chunk_size)
    tr_date, te_date = add_temporal_order_features(tr_date, te_date)
    print("[4/6] Encoding categorical columns...")
    selected_cat = []
    if include_cat:
        selected_cat = select_categorical_columns(raw / "train_categorical.csv",
                        int(fcfg["categorical_top_k"]),
                        float(fcfg.get("min_categorical_coverage", 0.0)), chunk_size)
        tr_cat, te_cat = build_categorical_features(raw / "train_categorical.csv",
                             raw / "test_categorical.csv", selected_cat, chunk_size)
    else:
        tr_cat, te_cat = tr_num[["Id"]].copy(), te_num[["Id"]].copy()
    print("[5/6] Merging...")
    train = tr_num.merge(tr_date, on="Id", how="left", validate="one_to_one")
    train = train.merge(tr_cat, on="Id", how="left", validate="one_to_one")
    test = te_num.merge(te_date, on="Id", how="left", validate="one_to_one")
    test = test.merge(te_cat, on="Id", how="left", validate="one_to_one")
    train = train.sort_values("Id").reset_index(drop=True)
    test = test.sort_values("Id").reset_index(drop=True)
    print("[6/6] Saving...")
    train_saved = save_frame(train, processed / "train_features.parquet")
    test_saved = save_frame(test, processed / "test_features.parquet")
    metadata = {"train_rows": len(train), "test_rows": len(test),
                "feature_count": len([c for c in train if c not in {"Id", "Response"}]),
                "train_feature_file": str(train_saved), "test_feature_file": str(test_saved),
                "selected_numeric": selected_num, "selected_categorical": selected_cat}
    (processed / "feature_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps({**metadata, "selected_numeric": len(selected_num),
                      "selected_categorical": len(selected_cat)}, indent=2))

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs.yaml")
    run(parser.parse_args().config)

if __name__ == "__main__":
    main()
