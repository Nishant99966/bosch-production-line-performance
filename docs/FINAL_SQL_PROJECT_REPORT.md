# Bosch Manufacturing Data Integration & Quality Analytics (SQL)

## Project aim and boundary

This is a **SQL/data-engineering portfolio adaptation** of the [Kaggle Bosch Production Line Performance competition](https://www.kaggle.com/competitions/bosch-production-line-performance), **not** a submission to its ML prediction task. The original predictive pipeline is preserved on the `machine-learning` branch.

**Business question:** Can three fragmented, extremely wide manufacturing data sources be integrated correctly and queried to describe measured production quality and data completeness?

### Deliverables
1. DuckDB schema storing part-level labels and normalized observed feature values.
2. Python loader for CSV data and SQL for quality checks and manufacturing reporting.
3. Complete header-only feature and station inventory.
4. Reproducible real-training-data validation and final SQL report.

## Data pipeline

`train_numeric.csv` + `train_date.csv` + `train_categorical.csv`
→ validate matching `Id` and labels
→ `parts`, `numeric_measurements`, `date_measurements`, `categorical_measurements`
→ SQL validation → analytical reporting.

`Response=0` denotes pass and `Response=1` failure. Missing measurement records are not imputed, and do not automatically indicate sensor faults. Time columns hold encoded offsets; no conversion to seconds is asserted.

## Observed real-data outcomes

The user ran the importer and SQL report using Python 3.11.9 and DuckDB 1.5.6 on Windows.

| Measure | Verified output |
|---|---:|
| Labelled training parts | 1,183,747 |
| Passing parts | 1,176,868 (99.42%) |
| Failed parts | 6,879 (0.58%) |
| Duplicate part IDs | 0 |
| Orphan measurements (numeric/date/categorical) | 0 / 0 / 0 |
| Numeric source columns | 968 |
| Date source columns | 1,156 |
| Categorical source columns | 2,140 |
| Total source feature columns | 4,264 |
| Parsed lines / stations | 4 / 52 |

**Important scope:** The entire labelled training *population* was loaded, but **only the first 20 features from each source**, i.e. 60 of 4,264 features, were imported as observations. The independent header inventory identifies all feature names without reading their values. Results that refer to stations, timestamps and missingness reflect the **selected 60 features only**, not all Bosch stations.

## Example selected-feature findings

- Selected date feature `L0_S2_D34` observed for 339,774 parts; 71.30% are missing in the 1,183,747 part population.
- Categorical `L0_S1_F25` and `L0_S1_F27` have 25 non-null readings each. Their displayed 100.0% missingness is rounding, not zero coverage.
- Selected-feature timestamps observed at S0 for 673,862 distinct parts; S1 for 673,904, S2 for 339,774.
- Measured sample mean for numeric `L0_S0_F4`: pass group 0.0002 over 670,254 observations, fail group -0.0309 over 3,608 observations. No significance or causality is established.

## SQL skills demonstrated

Relational keys and table design; schema constraints; imported-source validation; multi-source joins by part ID; `GROUP BY` aggregations, window functions, anti joins, `DISTINCT` station-presence views, conditional aggregates (`FILTER`), CTEs, explicit denominators and careful interpretation of missingness.

## Running the reproducible SQL analysis

From the project directory with the DuckDB environment active:

```powershell
python scripts/inventory_features.py --data-dir data/raw
python scripts/load_bosch.py --data-dir data/raw --database data/bosch.duckdb --max-features 20
python scripts/run_sql.py --database data/bosch.duckdb
python scripts/run_final_report.py --database data/bosch.duckdb
```

The last command runs `sql/04_final_quality_report.sql` and saves the entire results as a CSV report in `data/processed/final_sql_report/`. It does not modify the database.

## Limitations and completion criteria

The three raw inputs are Kaggle training files; no `test_*` CSVs have been used. A source-feature header inventory is not the same as a full column-by-column non-null scan. The dataset is anonymized; production path and physical root-cause claims cannot be verified from feature names alone.

**Status:** Core SQL project achieved: real-data integration, quality checks and documented first-pass manufacturing analytics. The extended final SQL report is implemented and awaits execution on the user's local DuckDB database. Do not claim that new report outputs have been validated until it is run.
