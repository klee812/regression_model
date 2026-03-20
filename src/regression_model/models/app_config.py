"""Top-level application configuration combining all sub-configs."""

from __future__ import annotations

from dataclasses import dataclass, field

from regression_model.models.output_config import OutputConfig
from regression_model.models.preprocessing_config import PreprocessingConfig
from regression_model.models.regression_config import RegressionConfig


@dataclass
class AppConfig:
    """Root configuration object assembled from a YAML config file."""

    targets: list[str] | None  # None = all instruments in price data except drivers
    drivers: list[str]
    regression: RegressionConfig = field(default_factory=RegressionConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    preprocessing: PreprocessingConfig = field(default_factory=PreprocessingConfig)
    cache_path: str | None = None  # Parquet cache for pre-computed prices
