# Bosch Production Line Performance — End-to-End Machine Learning

A reproducible, memory-conscious Python machine-learning pipeline for the [Kaggle Bosch Production Line Performance competition](https://www.kaggle.com/competitions/bosch-production-line-performance). The goal is to predict which manufactured parts will fail quality checks.

**Status:** Implemented pipeline and synthetic-data smoke tests. **The full Kaggle competition dataset was not available in this execution environment, so no full-data validation MCC or Kaggle leaderboard result is claimed.** Never interpret synthetic performance as competition performance.

## Features

- Loads Bosch numeric, timestamp, and categorical data in CSV chunks.
- Selects informative numeric features using class-conditional means, missingness and coverage.
- Compresses wide timestamps to per-station minimum, maximum and span.
- Computes part production start/end, time elapsed and visited-station/line counts.
- Creates production-order features from combined training and test timestamps (no test labels).
- Ordinal-encodes selected categorical columns and computes category frequencies.
- Trains a class-weighted LightGBM binary classifier.
- Supports chronological (default) or stratified holdout validation.
- Optimizes the final binary decision threshold for Matthews correlation coefficient (MCC).
- Saves trained model, metrics, feature importance and Kaggle submission CSV.
- Includes synthetic-data generator, automated smoke test and GitHub Actions.

## Repository layout

```text
.github/workflows/tests.yml       Automated CI
configs.yaml                      Full dataset configuration
configs.synthetic.yaml            Local synthetic smoke-test configuration
scripts/download_data.sh          Download Kaggle data after authorization
scripts/make_synthetic_data.py    Generate synthetic Bosch-shaped data
scripts/run_pipeline.sh           Prepare and train
src/bosch_pipeline/config.py      Load configuration
src/bosch_pipeline/io.py          Data I/O
src/bosch_pipeline/numeric_selection.py  Streaming numeric feature ranking
src/bosch_pipeline/features.py    Station, timing, numeric and categorical features
src/bosch_pipeline/prepare.py     Build feature datasets
src/bosch_pipeline/metrics.py     MCC threshold optimization
src/bosch_pipeline/model.py       LightGBM fitting
src/bosch_pipeline/train.py       Model/report/submission pipeline
tests/                            Unit and end-to-end tests
PROJECT_REPORT.md                 Method, assumptions and limitations
```

## Setup

Requires Python 3.10+ (Python 3.11 recommended). Use a virtual environment.

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e . pytest kaggle
pytest -q
```

## Run the synthetic end-to-end test

```bash
python scripts/make_synthetic_data.py
python -m bosch_pipeline.prepare --config configs.synthetic.yaml
python -m bosch_pipeline.train --config configs.synthetic.yaml
```

The resulting synthetic-only outputs are in `artifacts_synthetic/`. This is a functional smoke test, **not evidence of prediction quality on Bosch**.

## Full Kaggle competition run

1. Open the [competition page](https://www.kaggle.com/competitions/bosch-production-line-performance/data), sign into Kaggle, and accept the data-access terms.
2. Configure the [Kaggle CLI](https://github.com/Kaggle/kaggle-api) for your account.
3. Download/extract the CSV files:

```bash
bash scripts/download_data.sh
```

Confirm `data/raw` includes:
```text
train_numeric.csv
test_numeric.csv
train_date.csv
test_date.csv
train_categorical.csv
test_categorical.csv
```

Then:

```bash
python -m bosch_pipeline.prepare --config configs.yaml
python -m bosch_pipeline.train --config configs.yaml
```

Outputs:
- `artifacts/model.txt`: fitted LightGBM model
- `artifacts/metrics.json`: holdout MCC, ROC AUC, average precision and threshold
- `artifacts/feature_importance.csv`: model feature importance
- `artifacts/submission.csv`: `Id,Response` competition predictions
- `data/processed/feature_metadata.json`: selected feature metadata

**Do not commit Kaggle data, trained binaries or credentials.** The `.gitignore` excludes local input/output directories.

## Evaluation and leakage considerations

The official metric is **Matthews Correlation Coefficient (MCC)**, rather than ordinary accuracy. The decision threshold is selected on the held-out set and then applied to the test set. Chronological validation is the default, to more closely resemble future production, but it is only a proxy for unknown production and competition split mechanisms.

The numeric feature ranking currently uses all training labels before validation, which can inflate the reported holdout estimate. For rigorous validation, fit the feature selector only on training folds, validate on untouched folds, and preferably use nested or out-of-fold threshold tuning. Combined train/test time-neighbor and category-frequency features are transductive and must be disclosed when evaluating external deployment performance. Production systems should restrict these features to legitimately available information.

The pipeline is **memory-conscious, not fully out-of-core**: it chunks raw CSV reads but collects engineered DataFrames in memory. Full production runs require adequate RAM, disk space and runtime. Begin with the synthetic test and reduce selected feature counts if necessary.

## Next steps for a publishable performance result

Run on the authenticated full dataset, record environment/hardware, retain holdout metrics, create class-conditional feature-selection within folds, run repeatable validation and model comparisons, and submit predictions to Kaggle only if the competition allows submissions. Update the report with measured results rather than fabricated scores.

## License

MIT. Competition dataset is governed by Kaggle/competition terms and is not redistributed here.
