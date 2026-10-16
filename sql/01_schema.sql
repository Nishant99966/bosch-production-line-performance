CREATE TABLE IF NOT EXISTS parts (
  part_id BIGINT PRIMARY KEY,
  response SMALLINT CHECK (response IN (0, 1) OR response IS NULL),
  dataset_split VARCHAR NOT NULL CHECK (dataset_split IN ('train','test'))
);
CREATE TABLE IF NOT EXISTS feature_catalog (
  source_type VARCHAR NOT NULL,
  feature_name VARCHAR NOT NULL,
  line_name VARCHAR,
  station_name VARCHAR,
  PRIMARY KEY (source_type, feature_name)
);
CREATE TABLE IF NOT EXISTS numeric_measurements (
  part_id BIGINT NOT NULL,
  feature_name VARCHAR NOT NULL,
  line_name VARCHAR,
  station_name VARCHAR,
  measured_value DOUBLE NOT NULL,
  PRIMARY KEY (part_id, feature_name)
);
CREATE TABLE IF NOT EXISTS date_measurements (
  part_id BIGINT NOT NULL,
  feature_name VARCHAR NOT NULL,
  line_name VARCHAR,
  station_name VARCHAR,
  timestamp_offset DOUBLE NOT NULL,
  PRIMARY KEY (part_id, feature_name)
);
CREATE TABLE IF NOT EXISTS categorical_measurements (
  part_id BIGINT NOT NULL,
  feature_name VARCHAR NOT NULL,
  line_name VARCHAR,
  station_name VARCHAR,
  category_value VARCHAR NOT NULL,
  PRIMARY KEY (part_id, feature_name)
);
