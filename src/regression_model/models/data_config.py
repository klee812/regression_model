"""Data configuration for specifying input file paths."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DataConfig:
    """Paths to the target and driver price CSV files."""

    targets_path: str
    drivers_path: str
