"""Configuration loading helpers."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.yaml"


def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load YAML config and resolve known project paths to ``Path`` objects."""
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    data["_config_path"] = str(path)
    data["_project_root"] = str(PROJECT_ROOT)
    return data


def get_project_root(config: dict[str, Any] | None = None) -> Path:
    if config and "_project_root" in config:
        return Path(config["_project_root"])
    return PROJECT_ROOT


def project_path(*parts: str | Path, config: dict[str, Any] | None = None) -> Path:
    """Return an absolute path under the project root."""
    if len(parts) == 1:
        candidate = Path(parts[0])
    else:
        candidate = Path(*parts)
    if candidate.is_absolute():
        return candidate
    return get_project_root(config) / candidate


def output_path(key: str, config: dict[str, Any] | None = None) -> Path:
    cfg = config or load_config()
    try:
        return project_path(cfg["outputs"][key], config=cfg)
    except KeyError as exc:
        raise KeyError(f"Unknown output key in config.outputs: {key}") from exc


def raw_path(key: str, config: dict[str, Any] | None = None) -> Path:
    cfg = config or load_config()
    try:
        return project_path(cfg["paths"]["raw_data_dir"], cfg["raw_files"][key], config=cfg)
    except KeyError as exc:
        raise KeyError(f"Unknown raw file key in config.raw_files: {key}") from exc


def merged_config(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """Load config and recursively merge a small override dictionary."""
    cfg = load_config()
    if not overrides:
        return cfg

    def merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
        for key, value in patch.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                merge(base[key], value)
            else:
                base[key] = deepcopy(value)
        return base

    return merge(cfg, overrides)
