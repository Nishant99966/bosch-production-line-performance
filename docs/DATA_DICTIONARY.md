# Data dictionary

| Table | Column | Meaning |
|---|---|---|
| parts | part_id | Kaggle Id; join key between three source files |
| parts | response | Train-only quality label: 0 = pass, 1 = fail. NULL if unlabelled |
| parts | dataset_split | 'train' or 'test'; initial loader imports train only |
| feature_catalog | source_type | numeric / date / categorical |
| feature_catalog | feature_name | Original Kaggle column name, unmodified |
| feature_catalog | line_name | Parsed `L<number>` prefix where available |
| feature_catalog | station_name | Parsed `S<number>` station where available |
| numeric_measurements | measured_value | Observed numeric reading; missing entries absent, not zero |
| date_measurements | timestamp_offset | Observed relative timing code; units not assumed seconds |
| categorical_measurements | category_value | Categorical code stored as source text |

**Grain:** `parts` has one row per part; each measurement table has one row per (part, selected feature) with non-missing value. `feature_catalog` includes even selected features with zero observations, enabling missingness audits.

**Critical:** Stations and feature codes are anonymous. Neither a code nor a correlated mean difference identifies the physical root cause of a defect. Interpret absence of readings with production routing in mind. Test data does not contain a trustworthy Response.
