"""YAML configuration loading for the regression_model application."""

from __future__ import annotations

from pathlib import Path

import yaml

from regression_model.models import (
    AppConfig,
    DataConfig,
    OutputConfig,
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

    data_cfg = DataConfig(**raw["data"])
    regression_cfg = RegressionConfig(**raw.get("regression", {}))
    output_cfg = OutputConfig(**raw.get("output", {}))

    return AppConfig(
        data=data_cfg,
        targets=raw["targets"],
        drivers=raw["drivers"],
        regression=regression_cfg,
        output=output_cfg,
    )
