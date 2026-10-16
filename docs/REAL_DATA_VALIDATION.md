# Bosch SQL Manufacturing Analytics — Real Data Validation

Validation run: 2026-10-17 (user-executed on Windows, Python 3.11.9, DuckDB 1.5.6).

## Scope
- Source: real Kaggle Bosch *training* CSVs (numeric, date, categorical).
- Imported **all 1,183,747 training parts**, but only **20 feature columns per source** (60 feature columns total), using `--max-features 20`.
- Thus this is a *full-part / partial-feature* analysis, **not** a comprehensive inventory of the Bosch sensors and stations.
- No held-out test records imported; those do not have observed Response labels.

## Verified structural quality checks

| Check | Observed |
|---|---:|
| Total parts | 1,183,747 |
| Labelled train | 1,183,747 |
| Unlabelled train | 0 |
| Duplicate part IDs | 0 |
| Orphan numeric/date/categorical observations | 0 / 0 / 0 |

## Outcomes

| Response | Parts | Share |
|---|---:|---:|
| 0 (pass) | 1,176,868 | 99.42% |
| 1 (fail) | 6,879 | 0.58% |

## Selected-feature date observations

| Station | Distinct parts with observed timestamps | Non-null timestamp observations |
|---|---:|---:|
| S0 | 673,862 | 8,086,344 |
| S1 | 673,904 | 1,347,806 |
| S2 | 339,774 | 2,038,644 |

For parts with observations among the selected date columns: 671,097 passing parts and 3,610 failing parts; mean *observed selected-feature* spans 0.0050 and 0.0052 in encoded dataset time units, respectively. These are **not validated machine-cycle times**.

## Missingness

- Categorical L0_S1_F25 and L0_S1_F27 observed in 25/1,183,747 parts; shown as 100.0% missing after rounding, but actually not fully missing.
- Selected date feature L0_S2_D34 observed in 339,774 parts (71.30% missing).
- Lack of a value may reflect production routing, not sensor failure. Avoid treating null as zero.

## Example descriptive comparison

Numeric `L0_S0_F4`: pass mean 0.0002 (670,254 observed), fail mean -0.0309 (3,608 observed). The observation is associative, without causality or a formal significance assessment.

## What has and has not been validated

**Validated:** successful import and execution of quality/manufacturing SQL statements against actual training data, primary key/foreign-key integrity as checked by SQL.

**Not yet validated:** entire original feature inventory, type/range distribution checks, full station coverage, chronological routing interpretation, physical meaning of anonymized sensors, timestamp units, or robustness benchmarks. No root-cause attribution or predictive accuracy claim.

## Next steps

1. Audit all source feature headers and per-feature coverage *without loading all billions of long-form observations*.
2. Improve station-level routing and missingness SQL analyses with appropriate denominators.
3. Add reproducible SQL test fixtures and record actual results and hardware limits.
