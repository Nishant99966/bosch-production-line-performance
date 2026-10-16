from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd

def make_split(n: int, start_id: int, rng: np.random.Generator, with_target: bool):
    ids = np.arange(start_id, start_id + n)
    base_time = np.sort(rng.integers(0, 2000, size=n)).astype(float) / 10.0
    latent = rng.normal(size=n)
    y = ((latent + 0.8 * (base_time % 7 < 0.5) +
          rng.normal(scale=0.8, size=n)) > 2.1).astype(int)
    numeric = {"Id": ids}
    for j in range(18):
        x = rng.normal(size=n) + y * (0.20 if j < 5 else 0.0)
        missing = rng.random(n) < (0.35 + 0.12 * y if j < 4 else 0.45)
        x[missing] = np.nan
        numeric[f"L{j%4}_S{j%9}_F{100+j}"] = x
    if with_target:
        numeric["Response"] = y
    date = {"Id": ids}
    for line in range(4):
        for station in range(line * 2, line * 2 + 2):
            entered = base_time + station * 0.05 + rng.normal(scale=0.01, size=n)
            seen = rng.random(n) > 0.30
            entered[~seen] = np.nan
            date[f"L{line}_S{station}_D{line*100+station}"] = entered
            date[f"L{line}_S{station}_D{line*100+station+50}"] = (
                entered + rng.uniform(0, 0.08, size=n))
    cat = {"Id": ids}
    for j in range(8):
        values = rng.choice(["T1", "T2", "T3", None], size=n,
                            p=[0.2, 0.2, 0.1, 0.5])
        if j < 2 and with_target:
            values = values.astype(object)
            values[y == 1] = rng.choice(["T1", "T2"], size=(y == 1).sum())
        cat[f"L{j%4}_S{j%8}_F{500+j}"] = values
    return pd.DataFrame(numeric), pd.DataFrame(date), pd.DataFrame(cat)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="data/raw_synthetic")
    parser.add_argument("--rows", type=int, default=3000)
    args = parser.parse_args()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(42)
    train = make_split(args.rows, 1, rng, True)
    test = make_split(max(1000, args.rows // 2), 2_000_001, rng, False)
    for name, tr, te in zip(["numeric", "date", "categorical"], train, test):
        tr.to_csv(out / f"train_{name}.csv", index=False)
        te.to_csv(out / f"test_{name}.csv", index=False)
    pd.DataFrame({"Id": test[0]["Id"], "Response": 0}).to_csv(
        out / "sample_submission.csv", index=False)
    print(f"Synthetic Bosch-shaped data written to {out}")

if __name__ == "__main__":
    main()
