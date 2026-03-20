"""Application-level constants and default paths."""

from __future__ import annotations

# Default path to config.yaml on the Windows deployment machine.
# Override by passing a path explicitly to the CLI:
#   python -m regression_model prepare path/to/config.yaml
DEFAULT_CONFIG_PATH = r"C:\inav_data\regression_model\input\config.yaml"
