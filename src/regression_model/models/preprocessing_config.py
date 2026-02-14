"""Configuration for data preprocessing (validation, missing data, outliers)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PreprocessingConfig:
    """Controls how raw price data is validated and cleaned before regression."""

    # Missing data handling: "drop", "forward_fill", "interpolate"
    missing_data_handler: str = "drop"
    # Outlier handling: "none", "winsorize", "clip", "drop"
    outlier_method: str = "none"
    # Z-score threshold for outlier detection
    outlier_threshold: float = 3.0
    # Whether to validate that prices are positive with no duplicate dates
    validate_prices: bool = True
    # Minimum rows required after cleaning
    min_observations: int = 10
