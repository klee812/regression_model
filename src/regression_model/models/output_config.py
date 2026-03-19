"""Configuration for output format and destination."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class OutputConfig:
    """Controls how and where regression results are written."""

    format: str = "json"
    path: Path = Path("output/results.json")
