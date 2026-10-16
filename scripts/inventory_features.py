"""Inventory every Bosch training feature from CSV headers (no full data read).

Usage:
    python scripts/inventory_features.py --data-dir data/raw
Writes data/processed/feature_inventory.csv and station_inventory.csv.
"""
import argparse
import csv
import re
from collections import Counter
from pathlib import Path

SOURCES = {
    "numeric": "train_numeric.csv",
    "date": "train_date.csv",
    "categorical": "train_categorical.csv",
}
PATTERN = re.compile(r"^(L\d+)_(S\d+)_([A-Z])(\d+)$")


def inventory(data_dir: Path, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    feature_path = output_dir / "feature_inventory.csv"
    station_path = output_dir / "station_inventory.csv"
    station_counts = Counter()
    source_counts = Counter()
    unknown = 0

    with feature_path.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.writer(destination)
        writer.writerow(["source_type", "feature_name", "line_name",
                         "station_name", "feature_kind", "feature_number"])
        for source_type, filename in SOURCES.items():
            path = data_dir / filename
            if not path.is_file():
                raise FileNotFoundError(f"Missing {path}")
            with path.open("r", newline="", encoding="utf-8") as input_file:
                columns = next(csv.reader(input_file))
            if "Id" not in columns or len(columns) != len(set(columns)):
                raise ValueError(f"Invalid or duplicated column names in {path}")
            if source_type == "numeric" and "Response" not in columns:
                raise ValueError("train_numeric.csv requires the Response column")
            for name in columns:
                if name in ("Id", "Response"):
                    continue
                match = PATTERN.fullmatch(name)
                line, station, kind, number = (
                    match.groups() if match else ("", "", "", "")
                )
                if not match:
                    unknown += 1
                station_counts[(source_type, line, station)] += 1
                source_counts[source_type] += 1
                writer.writerow([source_type, name, line, station, kind, number])

    with station_path.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.writer(destination)
        writer.writerow(["source_type", "line_name", "station_name", "feature_count"])
        for (source, line, station), count in sorted(station_counts.items()):
            writer.writerow([source, line, station, count])

    for source, count in source_counts.items():
        print(f"{source}: {count:,} feature columns")
    print(f"Unrecognized feature names: {unknown}")
    print(f"Features: {feature_path}")
    print(f"Station summary: {station_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed"))
    args = parser.parse_args()
    inventory(args.data_dir, args.output_dir)


if __name__ == "__main__":
    main()
