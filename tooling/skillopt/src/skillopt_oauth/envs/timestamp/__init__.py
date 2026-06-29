"""Registers the `timestamp` benchmark env on import."""
from skillopt_oauth.registry import register_env
from skillopt_oauth.envs.timestamp.adapter import TimestampAdapter
from skillopt_oauth.envs.timestamp.dataloader import TimestampDataLoader

register_env(
    "timestamp",
    adapter_cls=TimestampAdapter,
    loader_cls=TimestampDataLoader,
    default_config="configs/timestamp/default.yaml",
)

__all__ = ["TimestampAdapter", "TimestampDataLoader"]
