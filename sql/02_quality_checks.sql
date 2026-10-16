-- Data integrity and sparsity audit. A zero count is expected for primary-key violations.
SELECT 'parts_total' AS check_name, COUNT(*) AS result FROM parts
UNION ALL SELECT 'labelled_train_parts', COUNT(*) FROM parts WHERE dataset_split='train' AND response IS NOT NULL
UNION ALL SELECT 'unlabelled_train_parts', COUNT(*) FROM parts WHERE dataset_split='train' AND response IS NULL
UNION ALL SELECT 'duplicate_part_ids', COUNT(*) FROM (SELECT part_id FROM parts GROUP BY part_id HAVING COUNT(*) > 1)
UNION ALL SELECT 'orphan_numeric_measurements', COUNT(*) FROM numeric_measurements n ANTI JOIN parts p ON n.part_id=p.part_id
UNION ALL SELECT 'orphan_date_measurements', COUNT(*) FROM date_measurements d ANTI JOIN parts p ON d.part_id=p.part_id
UNION ALL SELECT 'orphan_categorical_measurements', COUNT(*) FROM categorical_measurements c ANTI JOIN parts p ON c.part_id=p.part_id;

-- Coverage is per loaded feature across the number of loaded parts.
WITH totals AS (SELECT COUNT(*) AS n FROM parts),
observations AS (
 SELECT 'numeric' AS kind, feature_name, COUNT(DISTINCT part_id) AS observed FROM numeric_measurements GROUP BY feature_name
 UNION ALL SELECT 'date', feature_name, COUNT(DISTINCT part_id) FROM date_measurements GROUP BY feature_name
 UNION ALL SELECT 'categorical', feature_name, COUNT(DISTINCT part_id) FROM categorical_measurements GROUP BY feature_name
)
SELECT c.source_type, c.feature_name, COALESCE(o.observed,0) AS observed_parts,
  t.n AS total_parts,
  ROUND(100.0 * (t.n - COALESCE(o.observed,0)) / NULLIF(t.n,0),2) AS missing_pct
FROM feature_catalog c CROSS JOIN totals t
LEFT JOIN observations o ON o.kind=c.source_type AND o.feature_name=c.feature_name
ORDER BY missing_pct DESC, c.source_type, c.feature_name
LIMIT 25;
