# Bosch Production Line Performance — SQL Manufacturing Analytics

**Primary project: SQL + data engineering (DuckDB).** An earlier machine learning implementation is preserved on the [machine-learning branch](https://github.com/Nishant99966/bosch-production-line-performance/tree/machine-learning).

## Business problem

Bosch manufacturing records are spread across three files keyed by part `Id`: numeric sensor readings, timestamps, and categorical inspection/production data. Build a queryable database that connects the sources, audits missing measurements, reconstructs basic production timing and examines quality failures (`Response=1`).

**This project does not predict defects.** It creates trustworthy, repeatable manufacturing quality analytics using SQL. A missing sensor reading is **not automatically** a defect or a sensor malfunction; it may reflect a line/station that the part never visited.

## Dataset and grain

Source: [Bosch Production Line Performance (Kaggle)](https://www.kaggle.com/competitions/bosch-production-line-performance/data). Competition terms apply. Local CSV inputs are not committed.

- `train_numeric.csv`: `Id`, many numeric measurements, and labelled `Response` (0 = no failure; 1 = failure).
- `train_date.csv`: `Id` and many station-feature timestamp offsets (not necessarily wall-clock time).
- `train_categorical.csv`: `Id` and categorical readings.
- Test files are unlabelled; **never treat missing test labels as passing parts**.
- `Id` is the join key. Feature names encode line/station/feature patterns (e.g. `L0_S0_F0`); do not invent physical sensor meanings.

## Project architecture

```text
data/raw/train_*.csv (Kaggle, not committed)
  -> scripts/load_bosch.py (chunked, selected-column ingestion)
  -> DuckDB database
       parts                 one row per part, optional Response
       numeric_measurements  Id + feature + station + numeric value
       date_measurements     Id + feature + station + timestamp offset
       categorical_measurements  Id + feature + station + category
  -> sql/02_quality_checks.sql
  -> sql/03_manufacturing_analysis.sql
```

To prevent multi-billion-row accidental imports, long-form measurement ingestion defaults to the first **20** columns from each file (configurable). This is a **sample of features**, not a representative sample of parts. SQL results must disclose which features were loaded. Increase only after inspecting disk/RAM resources.

## Getting started

Requires Python 3.10+ and actual Kaggle training CSVs extracted to `data/raw/`.

```bash
pip install -r requirements.txt
python scripts/load_bosch.py --data-dir data/raw --database data/bosch.duckdb --max-features 20
python scripts/run_sql.py --database data/bosch.duckdb
```

On Windows PowerShell, use the same `python` commands. `--max-features 0` imports *all* measurement features: this may require significant disk and time. Use `--rows 10000` to dry-run a small subset of actual records without claiming full-data results.

The loader checks header columns, aligns the three files on `Id`, rejects duplicate part IDs and inconsistent labels, stores observed (non-null) measurements and records the selected-feature catalogue. It processes chunks; the SQL results are printed to your terminal.

## Questions answered by SQL

1. How many labelled parts passed or failed, and what is the failure rate?
2. Which features have the lowest coverage and the highest missingness?
3. How do observed part start/end timestamps and visit counts differ by quality outcome?
4. Which stations have measurements for the most parts?
5. Which readings differ between failed and passed parts? These are descriptive comparisons, **not causality**.
6. Which source IDs and measurements fail data quality constraints?

## Limitations

- No real-data benchmark has been completed in this environment. Counts and failure rates are intentionally **not fabricated**.
- Different file timestamps are relative encoded values; duration should be described as dataset time units without assuming seconds.
- Sparse observations may reflect different production paths. Never fill missing physical measurements with zero.
- Column selection defaults to a prefix and can bias feature-level comparisons; run full inventory for exhaustive analysis.
- No externally measured SQL run time or full dataset quality metrics are claimed.

## Repository structure

- `scripts/load_bosch.py` — load raw CSVs in chunks into DuckDB
- `scripts/run_sql.py` — run documented queries
- `sql/01_schema.sql` — normalized analytical table definitions
- `sql/02_quality_checks.sql` — validation queries
- `sql/03_manufacturing_analysis.sql` — business queries
- `docs/DATA_DICTIONARY.md` — dataset semantics and assumptions
- `machine-learning` branch — original LightGBM pipeline

**Status:** SQL foundation implemented. Actual data load and empirical validation pending access to full Bosch files.
