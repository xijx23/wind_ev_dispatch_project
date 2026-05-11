"""Small IO helpers used by every module."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.common.config_loader import project_path


def ensure_parent(path: str | Path) -> Path:
    resolved = project_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def ensure_dir(path: str | Path) -> Path:
    resolved = project_path(path)
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def read_csv(path: str | Path, **kwargs: Any) -> pd.DataFrame:
    return pd.read_csv(project_path(path), **kwargs)


def write_csv(df: pd.DataFrame, path: str | Path, **kwargs: Any) -> Path:
    resolved = ensure_parent(path)
    df.to_csv(resolved, index=False, encoding=kwargs.pop("encoding", "utf-8-sig"), **kwargs)
    return resolved


def write_json(data: dict[str, Any], path: str | Path) -> Path:
    resolved = ensure_parent(path)
    with resolved.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return resolved


def read_json(path: str | Path) -> dict[str, Any]:
    with project_path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def write_npz(path: str | Path, **arrays: Any) -> Path:
    resolved = ensure_parent(path)
    np.savez_compressed(resolved, **arrays)
    return resolved


def require_columns(df: pd.DataFrame, columns: list[str], name: str = "DataFrame") -> None:
    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")
