-- FINAL BOSCH SQL QUALITY REPORT
-- Run against the labelled training database. Missing readings are not zero.
-- Every denominator is explicitly defined in each query.

-- 1. Full labelled-training population and observed failure rate.
SELECT COUNT(*) AS labelled_parts,
       COUNT(*) FILTER (WHERE response = 0) AS passed_parts,
       COUNT(*) FILTER (WHERE response = 1) AS failed_parts,
       ROUND(100.0 * COUNT(*) FILTER (WHERE response = 1)
             / NULLIF(COUNT(*), 0), 4) AS failure_rate_pct
FROM parts WHERE dataset_split = 'train' AND response IS NOT NULL;

-- 2. Number of features imported versus the full CSV header inventory.
-- feature_catalog describes selected features actually staged into the database.
SELECT source_type, COUNT(*) AS imported_features
FROM feature_catalog GROUP BY source_type ORDER BY source_type;

-- 3. Measurement coverage by source, counting feature-part observations.
-- A missing value could mean the part did not visit that production path.
WITH observed AS (
 SELECT 'numeric' AS source_type, COUNT(*) AS observed_cells FROM numeric_measurements
 UNION ALL SELECT 'date', COUNT(*) FROM date_measurements
 UNION ALL SELECT 'categorical', COUNT(*) FROM categorical_measurements
), population AS (
 SELECT COUNT(*) AS part_count FROM parts WHERE dataset_split = 'train'
), features AS (
 SELECT source_type, COUNT(*) AS feature_count FROM feature_catalog GROUP BY source_type
)
SELECT f.source_type, p.part_count, f.feature_count, o.observed_cells,
       p.part_count * f.feature_count AS potential_cells,
       ROUND(100.0 * o.observed_cells /
             NULLIF(p.part_count * f.feature_count, 0), 4) AS nonnull_coverage_pct
FROM features f JOIN observed o USING(source_type) CROSS JOIN population p
ORDER BY f.source_type;

-- 4. Train-only production quality stratified by observation at a selected station.
-- This is a descriptive conditional rate, NOT a causal effect of visiting the station.
WITH station_parts AS (
 SELECT DISTINCT part_id, line_name, station_name FROM date_measurements
), outcomes AS (
 SELECT s.line_name, s.station_name, p.response
 FROM station_parts s JOIN parts p ON p.part_id = s.part_id
 WHERE p.dataset_split='train' AND p.response IS NOT NULL
)
SELECT line_name, station_name, COUNT(*) AS observed_parts,
       COUNT(*) FILTER (WHERE response=1) AS failed_parts,
       ROUND(100.0 * COUNT(*) FILTER (WHERE response=1)
             / NULLIF(COUNT(*), 0), 4) AS observed_failure_rate_pct
FROM outcomes GROUP BY line_name, station_name
ORDER BY line_name, station_name;

-- 5. Coverage per selected feature. Rounded percentages can hide rare observations.
WITH population AS (
 SELECT COUNT(*) AS n FROM parts WHERE dataset_split='train'
), obs AS (
 SELECT 'numeric' AS source_type, feature_name, COUNT(*) AS observed
 FROM numeric_measurements GROUP BY feature_name
 UNION ALL SELECT 'date', feature_name, COUNT(*) FROM date_measurements GROUP BY feature_name
 UNION ALL SELECT 'categorical', feature_name, COUNT(*) FROM categorical_measurements GROUP BY feature_name
)
SELECT f.source_type, f.feature_name, f.line_name, f.station_name,
       p.n AS population_parts, COALESCE(o.observed, 0) AS observed_parts,
       p.n - COALESCE(o.observed, 0) AS missing_parts,
       ROUND(100.0 * COALESCE(o.observed, 0) / NULLIF(p.n,0), 6) AS coverage_pct
FROM feature_catalog f CROSS JOIN population p
LEFT JOIN obs o ON o.source_type=f.source_type AND o.feature_name=f.feature_name
ORDER BY coverage_pct, f.source_type, f.feature_name;
