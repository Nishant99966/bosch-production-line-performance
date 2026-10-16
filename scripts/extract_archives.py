"""Safely extract Bosch training CSV archives, streaming to disk.

Usage: python scripts/extract_archives.py --archive-dir /path/to/downloads
"""
import argparse
import shutil
import zipfile
from pathlib import Path

NAMES = ("train_numeric.csv", "train_date.csv", "train_categorical.csv")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("data/raw"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for csv_name in NAMES:
        archive = args.archive_dir / (csv_name + ".zip")
        if not archive.is_file():
            parser.error(f"Missing archive {archive}")
        destination = args.output_dir / csv_name
        with zipfile.ZipFile(archive) as zf:
            members = [member for member in zf.infolist()
                       if not member.is_dir() and Path(member.filename).name == csv_name]
            if len(members) != 1:
                raise ValueError(f"{archive}: expected exactly one {csv_name}")
            with zf.open(members[0]) as source, destination.open("wb") as target:
                shutil.copyfileobj(source, target, length=1024 * 1024)
        print(f"Extracted {destination}")

if __name__ == "__main__":
    main()
