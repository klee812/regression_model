"""YAML configuration loading for the regression_model application."""

from __future__ import annotations

from pathlib import Path

import yaml

from regression_model.models import (
    AppConfig,
    OutputConfig,
    PreprocessingConfig,
    RegressionConfig,
)


def load_config(path: str | Path) -> AppConfig:
    """Parse a YAML config file and return an ``AppConfig``.

    Args:
        path: Filesystem path to the YAML configuration file.

    Returns:
        A fully populated ``AppConfig`` instance.
    """
    with open(path) as f:
        raw = yaml.safe_load(f)

    return AppConfig(
        targets=raw.get("targets"),  # None if omitted — means all instruments except drivers
        drivers=raw["drivers"],
        regression=RegressionConfig(**raw.get("regression", {})),
        output=OutputConfig(**raw.get("output", {})),
        preprocessing=PreprocessingConfig(**raw.get("preprocessing", {})),
        cache_path=raw.get("cache_path"),
    )
