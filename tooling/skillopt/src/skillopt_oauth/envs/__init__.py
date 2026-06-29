"""Benchmark environments. Importing this package registers every env."""
from __future__ import annotations

from skillopt_oauth.envs import timestamp as _timestamp  # noqa: F401  (registers env)
from skillopt_oauth.envs import spex_write_phased as _spex  # noqa: F401  (registers env)

__all__ = ["timestamp", "spex_write_phased"]
