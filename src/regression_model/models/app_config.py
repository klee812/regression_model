"""Top-level application configuration combining all sub-configs."""

from __future__ import annotations

from dataclasses import dataclass, field

from regression_model.models.data_config import DataConfig
from regression_model.models.output_config import OutputConfig
from regression_model.models.regression_config import RegressionConfig


@dataclass
class AppConfig:
    """Root configuration object assembled from a YAML config file."""

    data: DataConfig
    targets: list[str]
    drivers: list[str]
    regression: RegressionConfig = field(default_factory=RegressionConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
