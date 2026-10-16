"""Chunked CSV loader for a selected set of Bosch features.

Run: python scripts/load_bosch.py --data-dir data/raw --database data/bosch.duckdb
Works on the training split; unlabeled test ingestion is intentionally deferred.
"""
import argparse
import csv
import re
from pathlib import Path
import duckdb

PATTERN = re.compile(r"^(L\d+)_(S\d+)_")
SOURCES = (("numeric", "train_numeric.csv", "numeric_measurements", "measured_value"),
           ("date", "train_date.csv", "date_measurements", "timestamp_offset"),
           ("categorical", "train_categorical.csv", "categorical_measurements", "category_value"))

def quote_identifier(value):
    return '"' + value.replace('"', '""') + '"'

def headers(path):
    with path.open(newline="", encoding="utf-8") as source:
        return next(csv.reader(source))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--database", type=Path, default=Path("data/bosch.duckdb"))
    parser.add_argument("--max-features", type=int, default=20,
                        help="Number of feature columns from each CSV (0 = all)")
    parser.add_argument("--rows", type=int, default=0, help="Optional maximum parts for test loading")
    args = parser.parse_args()
    if args.max_features < 0 or args.rows < 0:
        parser.error("--max-features and --rows must be >= 0")
    paths = [(kind, args.data_dir / filename, table, valuecol) for kind, filename, table, valuecol in SOURCES]
    for _, path, _, _ in paths:
        if not path.is_file():
            parser.error(f"Missing {path}. Extract the Kaggle training CSVs first.")
    args.database.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(str(args.database))
    schema = Path(__file__).resolve().parents[1] / "sql" / "01_schema.sql"
    connection.execute(schema.read_text(encoding="utf-8"))
    # A complete fresh import is atomic: any error reverts all DELETE/INSERT work.
    connection.execute("BEGIN TRANSACTION")
    try:
        for table in ("numeric_measurements","date_measurements","categorical_measurements",
                      "feature_catalog","parts"):
            connection.execute(f"DELETE FROM {table}")
        for kind, path, table, valuecol in paths:
            header = headers(path)
            expected = {"Id", "Response"} if kind == "numeric" else {"Id"}
            if not expected.issubset(set(header)) or len(header) != len(set(header)):
                raise ValueError(f"Invalid or duplicated CSV header: {path}")
            features = [x for x in header if x not in ("Id", "Response")]
            if args.max_features:
                features = features[:args.max_features]
            for feature in features:
                match = PATTERN.match(feature)
                line, station = match.groups() if match else (None, None)
                connection.execute("INSERT INTO feature_catalog VALUES (?,?,?,?)",
                                   [kind, feature, line, station])
            fields = ["Id"] + (["Response"] if kind == "numeric" else []) + features
            projection = ", ".join(quote_identifier(x) for x in fields)
            # DuckDB CSV reader supports projection pushdown and direct SQL ingestion.
            raw = str(path).replace("'", "''")
            query = f"SELECT {projection} FROM read_csv_auto('{raw}', header=true, all_varchar=true)"
            if args.rows:
                query += f" LIMIT {args.rows}"
            connection.execute(f"CREATE OR REPLACE TEMP VIEW input_source AS {query}")
            connection.execute("CREATE OR REPLACE TEMP TABLE staged AS SELECT * FROM input_source")
            connection.execute('''CREATE OR REPLACE TEMP TABLE staged_ids AS
                SELECT TRY_CAST("Id" AS BIGINT) AS part_id, COUNT(*) OVER (PARTITION BY "Id") AS n
                FROM staged''')
            nbad = connection.execute("SELECT COUNT(*) FROM staged_ids WHERE part_id IS NULL OR n>1").fetchone()[0]
            if nbad:
                raise ValueError(f"{kind}: {nbad} invalid or duplicate Id rows")
            if kind == "numeric":
                bad = connection.execute('''SELECT COUNT(*) FROM staged
                  WHERE "Response" IS NULL OR TRIM("Response") NOT IN ('0','1')''').fetchone()[0]
                if bad:
                    raise ValueError(f"Invalid or missing Response values: {bad}")
                connection.execute('''INSERT INTO parts SELECT CAST("Id" AS BIGINT),
                  CAST(TRIM("Response") AS SMALLINT), 'train' FROM staged''')
            else:
                # The three input CSVs must describe the same sample of part IDs.
                extra = connection.execute('''SELECT COUNT(*) FROM
                  (SELECT CAST("Id" AS BIGINT) id FROM staged EXCEPT SELECT part_id FROM parts)''').fetchone()[0]
                absent = connection.execute('''SELECT COUNT(*) FROM
                  (SELECT part_id FROM parts EXCEPT SELECT CAST("Id" AS BIGINT) FROM staged)''').fetchone()[0]
                if extra or absent:
                    raise ValueError(f"{kind}: source Id mismatch ({extra} extra; {absent} absent)")
            # Feature-specific inserts avoid materializing a huge N x feature unpivot in RAM.
            for feature in features:
                match = PATTERN.match(feature)
                line, station = match.groups() if match else (None, None)
                expression = f"TRY_CAST({quote_identifier(feature)} AS DOUBLE)" if kind != "categorical" else quote_identifier(feature)
                numeric_filter = f"{quote_identifier(feature)} IS NOT NULL AND TRIM({quote_identifier(feature)}) <> ''"
                if kind != "categorical":
                    invalid = connection.execute(f"""SELECT COUNT(*) FROM staged WHERE {numeric_filter}
                    AND {expression} IS NULL""").fetchone()[0]
                    if invalid:
                        raise ValueError(f"{kind}.{feature}: {invalid} non-numeric values")
                connection.execute(f"""INSERT INTO {table}
                  SELECT CAST("Id" AS BIGINT), ?, ?, ?, {expression}
                  FROM staged WHERE {numeric_filter}""", [feature, line, station])
            print(f"Loaded {kind}: {len(features)} features")
        connection.execute("COMMIT")
        print(f"Database ready: {args.database}")
        print("Parts:", connection.execute("SELECT COUNT(*) FROM parts").fetchone()[0])
    except Exception:
        connection.execute("ROLLBACK")
        raise
    finally:
        connection.close()

if __name__ == "__main__":
    main()
