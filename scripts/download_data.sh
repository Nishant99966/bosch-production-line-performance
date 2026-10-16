#!/usr/bin/env bash
set -euo pipefail
mkdir -p data/raw
kaggle competitions download -c bosch-production-line-performance -p data/raw
python - <<'PY'
from pathlib import Path
import zipfile
root = Path("data/raw")
for z in root.glob("*.zip"):
    print("extracting", z.name)
    with zipfile.ZipFile(z) as f:
        f.extractall(root)
PY
