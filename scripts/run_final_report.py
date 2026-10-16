"""Run the final SQL report and export all query results to CSV, without pandas."""
import argparse
import csv
from pathlib import Path
import duckdb

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", default="data/bosch.duckdb")
    parser.add_argument("--output-dir", default="data/processed/final_sql_report")
    args = parser.parse_args()
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    statements = Path(__file__).resolve().parents[1].joinpath("sql/04_final_quality_report.sql").read_text(encoding="utf-8")
    connection = duckdb.connect(args.database, read_only=True)
    # Comments contain no semicolons; keep SQL statements portable.
    try:
        for idx, statement in enumerate(statements.split(";"), start=1):
            if not statement.strip():
                continue
            result = connection.execute(statement)
            if result.description is None:
                continue
            file = output / f"report_{idx:02d}.csv"
            with file.open("w", newline="", encoding="utf-8") as target:
                writer = csv.writer(target)
                writer.writerow([column[0] for column in result.description])
                total = 0
                while True:
                    rows = result.fetchmany(10000)
                    if not rows:
                        break
                    writer.writerows(rows)
                    total += len(rows)
            print(f"{file}: {total:,} rows")
    finally:
        connection.close()

if __name__ == "__main__":
    main()
