# Project report — Bosch Production Line Performance

## Objective

Predict the binary quality response of manufactured parts from extremely sparse, high-dimensional production-line records. The Kaggle benchmark evaluates binary predictions using Matthews Correlation Coefficient (MCC).

## Available data

The challenge separates raw fields into numeric sensor measurements, categorical inspection values, and production dates. Identifiers associate the same part across files. The train numeric file carries the response target. Raw Kaggle data are not stored in this GitHub repository.

## Implemented pipeline

1. **Input checks:** validate the presence of train/test numeric/date CSVs and optional categorical CSVs.
2. **Streaming feature ranking:** accumulate class-conditional means, variances and missing-value rates in chunks; retain top ranked numeric columns.
3. **Numeric engineering:** selected sensor signals, counts of observed/missing values, and per-part summary statistics.
4. **Date compression:** group date columns by line/station; derive station minimum, maximum, dwell spans, start/end, duration and visited-line counts.
5. **Production order:** combine unlabeled train/test timing metadata to compute previous/next gaps and same-time group position.
6. **Categorical engineering:** select frequently observed categories; factorize and compute frequency encodings on unlabeled union.
7. **Train/validation:** chronological holdout by default, LightGBM binary classification with class imbalance weighting and early stopping.
8. **Threshold selection:** maximize holdout MCC using a probability threshold search.
9. **Final fit and prediction:** train a final classifier on all labeled samples with the chosen iteration count; generate \`Id,Response\` CSV and feature-importance report.

## Validation and scientific limitations

- A synthetic end-to-end smoke test verifies the executable pipeline; it does not assess generalization to Bosch data.
- Full-dataset model fitting and Kaggle leaderboard evaluation were **not performed** in the provided execution environment. Hence no authentic Bosch MCC, confusion matrix or leaderboard rank is available.
- Numeric ranking runs before train/validation separation. This is label leakage into feature selection and can bias validation upward. For publication-grade results, rank features within each training fold.
- Threshold selection on the same holdout used to report MCC may be optimistic. Use a separate calibration fold, nested validation or out-of-fold predictions for defensible reporting.
- Test-set timing and frequency encodings are **transductive**; they use unlabeled test data but not test labels. This must be noted when designing an online deployment setting.
- The full feature tables are materialized in memory after chunked CSV processing. This is not a fully out-of-core solution and may require substantial RAM.
- The current CSV extraction helper assumes Kaggle download archives contain the raw CSVs; inspect nested archives or decompress in stages if needed.

## Intended future experiments

- Feature selection within training folds and several temporal blocked folds.
- Compare baseline Logistic Regression / HistGradientBoosting versus LightGBM.
- Add station-route patterns, rolling defect counts computed strictly using historical labels, and robust time-distance features.
- Report uncertainty from repeated folds, confusion matrices, MCC, PR-AUC and model drift by time slice.
- Profile memory peak, runtime, dataset sizes and reproducibility of submitted artifacts.

## Reproduction

See README.md for environment setup, authenticated Kaggle download, \`prepare\`, \`train\`, and synthetic smoke-test commands.

**Reproducibility statement:** Implementation is available; reported benchmark results must be collected after a real full-data run.
