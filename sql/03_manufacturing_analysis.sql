-- Quality outcome only for labelled training parts, no target leakage from test.
SELECT response, COUNT(*) AS parts,
 ROUND(100.0*COUNT(*) / SUM(COUNT(*)) OVER (),2) AS share_pct
FROM parts WHERE dataset_split='train' AND response IS NOT NULL
GROUP BY response ORDER BY response;

-- Observed manufacturing time span, in encoded dataset time units.
WITH timing AS (
 SELECT part_id, MIN(timestamp_offset) AS first_observed,
 MAX(timestamp_offset) AS last_observed,
 COUNT(DISTINCT station_name) AS observed_stations
 FROM date_measurements GROUP BY part_id
)
SELECT p.response, COUNT(*) AS parts_with_timestamps,
 ROUND(AVG(t.last_observed-t.first_observed),4) AS mean_observed_span,
 ROUND(AVG(t.observed_stations),2) AS mean_observed_station_count
FROM timing t JOIN parts p ON p.part_id=t.part_id
WHERE p.dataset_split='train' AND p.response IS NOT NULL
GROUP BY p.response ORDER BY p.response;

-- Observed station coverage in selected timestamp features.
SELECT station_name, COUNT(DISTINCT part_id) AS observed_parts,
COUNT(*) AS nonnull_timestamp_readings
FROM date_measurements GROUP BY station_name
ORDER BY observed_parts DESC LIMIT 20;

-- Descriptive difference in reading means (NOT a causal defect explanation).
SELECT n.feature_name,
 COUNT(*) FILTER (WHERE p.response=0) AS passing_observations,
 COUNT(*) FILTER (WHERE p.response=1) AS failing_observations,
 ROUND(AVG(n.measured_value) FILTER (WHERE p.response=0),4) AS passing_mean,
 ROUND(AVG(n.measured_value) FILTER (WHERE p.response=1),4) AS failing_mean
FROM numeric_measurements n JOIN parts p ON p.part_id=n.part_id
WHERE p.dataset_split='train' AND p.response IS NOT NULL
GROUP BY n.feature_name
HAVING COUNT(*) FILTER (WHERE p.response=0) >= 10
 AND COUNT(*) FILTER (WHERE p.response=1) >= 10
ORDER BY n.feature_name LIMIT 50;
