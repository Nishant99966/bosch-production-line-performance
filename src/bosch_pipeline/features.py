from __future__ import annotations
import re
from pathlib import Path
import numpy as np
import pandas as pd
from .io import read_header

STATION_RE = re.compile(r"(L\d+_S\d+)_")

def build_date_features(path: str | Path, chunk_size: int) -> pd.DataFrame:
    station_map: dict[str, list[str]] = {}
    for col in read_header(path):
        match = STATION_RE.search(col)
        if match:
            station_map.setdefault(match.group(1), []).append(col)
    frames = []
    for chunk in pd.read_csv(path, chunksize=chunk_size, low_memory=False):
        out = {"Id": chunk["Id"].to_numpy()}
        mins, maxs, names = [], [], []
        for station, cols in station_map.items():
            vals = chunk[cols]
            smin = vals.min(axis=1, skipna=True).to_numpy(dtype=np.float32)
            smax = vals.max(axis=1, skipna=True).to_numpy(dtype=np.float32)
            out[f"date_{station}_min"] = smin
            out[f"date_{station}_max"] = smax
            out[f"date_{station}_span"] = (smax - smin).astype(np.float32)
            mins.append(smin)
            maxs.append(smax)
            names.append(station)
        low = np.column_stack(mins) if mins else np.empty((len(chunk), 0))
        high = np.column_stack(maxs) if maxs else np.empty((len(chunk), 0))
        if low.shape[1]:
            with np.errstate(all="ignore"):
                out["start_time"] = np.nanmin(low, axis=1).astype(np.float32)
                out["end_time"] = np.nanmax(high, axis=1).astype(np.float32)
            out["production_duration"] = (out["end_time"] - out["start_time"]).astype(np.float32)
            visited = np.isfinite(low)
            out["stations_visited"] = visited.sum(axis=1).astype(np.int16)
            out["date_missing_fraction"] = (1.0 - visited.mean(axis=1)).astype(np.float32)
            for line in sorted({name.split("_")[0] for name in names}):
                idx = [i for i, station in enumerate(names) if station.startswith(f"{line}_")]
                out[f"stations_visited_{line}"] = visited[:, idx].sum(axis=1).astype(np.int16)
        frames.append(pd.DataFrame(out))
    return pd.concat(frames, ignore_index=True)

def add_temporal_order_features(train_dates: pd.DataFrame,
                                test_dates: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    tr, te = train_dates.copy(), test_dates.copy()
    tr["__split"], te["__split"] = 0, 1
    both = pd.concat([tr, te], ignore_index=True)
    order = np.lexsort((both["Id"].to_numpy(),
                        both["start_time"].fillna(np.inf).to_numpy()))
    ordered = both.iloc[order].copy()
    ordered["prev_start_gap"] = ordered["start_time"].diff().astype(np.float32)
    ordered["next_start_gap"] = (-ordered["start_time"].diff(-1)).astype(np.float32)
    ordered["prev_id_gap_time_order"] = ordered["Id"].diff().astype(np.float32)
    ordered["next_id_gap_time_order"] = (-ordered["Id"].diff(-1)).astype(np.float32)
    grouped = ordered.groupby("start_time", dropna=False, sort=False)
    ordered["same_start_count"] = grouped["Id"].transform("size").astype(np.int32)
    ordered["same_start_rank"] = grouped.cumcount().astype(np.int32)
    denominator = np.maximum(ordered["same_start_count"].to_numpy() - 1, 1)
    ordered["same_start_rank_frac"] = (
        ordered["same_start_rank"].to_numpy() / denominator).astype(np.float32)
    restored = ordered.sort_index()
    return (restored[restored["__split"] == 0].drop(columns="__split").reset_index(drop=True),
            restored[restored["__split"] == 1].drop(columns="__split").reset_index(drop=True))

def build_numeric_features(path: str | Path, selected: list[str],
                           chunk_size: int, is_train: bool) -> pd.DataFrame:
    usecols = ["Id", *selected] + (["Response"] if is_train else [])
    frames = []
    for chunk in pd.read_csv(path, usecols=usecols, chunksize=chunk_size, low_memory=False):
        out = pd.DataFrame({"Id": chunk["Id"].to_numpy()})
        if is_train:
            out["Response"] = chunk["Response"].astype(np.int8).to_numpy()
        selected_frame = chunk[selected].apply(pd.to_numeric, errors="coerce")
        for col in selected:
            out[f"num_{col}"] = selected_frame[col].astype(np.float32)
        arr = selected_frame.to_numpy(dtype=np.float32, copy=False)
        finite = np.isfinite(arr)
        out["numeric_selected_present"] = finite.sum(axis=1).astype(np.int16)
        out["numeric_selected_missing"] = (~finite).sum(axis=1).astype(np.int16)
        with np.errstate(all="ignore"):
            out["numeric_selected_mean"] = np.nanmean(arr, axis=1).astype(np.float32)
            out["numeric_selected_std"] = np.nanstd(arr, axis=1).astype(np.float32)
            out["numeric_selected_min"] = np.nanmin(arr, axis=1).astype(np.float32)
            out["numeric_selected_max"] = np.nanmax(arr, axis=1).astype(np.float32)
        frames.append(out)
    return pd.concat(frames, ignore_index=True)

def select_categorical_columns(train_path: str | Path, top_k: int,
                               min_coverage: float, chunk_size: int) -> list[str]:
    cols = [c for c in read_header(train_path) if c != "Id"]
    nonnull = np.zeros(len(cols), dtype=np.int64)
    rows = 0
    for chunk in pd.read_csv(train_path, usecols=cols, chunksize=chunk_size,
                             dtype="string", low_memory=False):
        nonnull += chunk.notna().sum(axis=0).to_numpy(dtype=np.int64)
        rows += len(chunk)
    coverage = nonnull / max(rows, 1)
    idx = np.where(coverage >= min_coverage)[0]
    idx = idx[np.argsort(-coverage[idx], kind="stable")]
    return [cols[i] for i in idx[:top_k]]

def build_categorical_features(train_path: str | Path, test_path: str | Path,
                               selected: list[str], chunk_size: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not selected:
        return (pd.read_csv(train_path, usecols=["Id"]),
                pd.read_csv(test_path, usecols=["Id"]))
    def read_selected(path: str | Path) -> pd.DataFrame:
        frames = []
        for chunk in pd.read_csv(path, usecols=["Id", *selected],
                                 chunksize=chunk_size,
                                 dtype={c: "string" for c in selected}, low_memory=False):
            frames.append(chunk)
        return pd.concat(frames, ignore_index=True)
    train, test = read_selected(train_path), read_selected(test_path)
    n_train = len(train)
    combined = pd.concat([train, test], ignore_index=True)
    out = pd.DataFrame({"Id": combined["Id"].to_numpy()})
    for col in selected:
        codes, _ = pd.factorize(combined[col].fillna("__MISSING__"), sort=False)
        out[f"cat_{col}"] = codes.astype(np.int32)
        counts = pd.Series(codes).value_counts(dropna=False)
        out[f"catfreq_{col}"] = pd.Series(codes).map(counts).to_numpy(dtype=np.int32)
    return out.iloc[:n_train].reset_index(drop=True), out.iloc[n_train:].reset_index(drop=True)
