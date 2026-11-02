from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    config_path = Path(path) if path else PROJECT_ROOT / "configs" / "default.yaml"
    config_path = config_path.resolve()
    with config_path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    parent = config.pop("extends", None)
    if parent:
        parent_path = (config_path.parent / parent).resolve()
        return _deep_merge(load_config(parent_path), config)
    return config

