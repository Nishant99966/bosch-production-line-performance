"""Run SQL scripts, printing each statement's result without fabricated metrics."""
import argparse
from pathlib import Path
import duckdb

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", default="data/bosch.duckdb")
    args = parser.parse_args()
    connection = duckdb.connect(args.database, read_only=True)
    for filename in ("sql/02_quality_checks.sql", "sql/03_manufacturing_analysis.sql"):
        text = Path(filename).read_text(encoding="utf-8")
        # Statements have no quoted semicolons; scripts use regular SQL comments.
        for i, statement in enumerate(text.split(";"), 1):
            if not statement.strip():
                continue
            print(f"\n{filename} statement {i}")
            result = connection.execute(statement)
            columns = [item[0] for item in result.description]
            print(" | ".join(columns))
            for row in result.fetchall():
                print(" | ".join(str(value) for value in row))
    connection.close()

if __name__ == "__main__":
    main()
