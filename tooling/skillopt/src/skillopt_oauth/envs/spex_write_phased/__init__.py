"""Registers the `spex_write_phased` benchmark env on import."""
from skillopt_oauth.registry import register_env
from skillopt_oauth.envs.spex_write_phased.adapter import SpexWritePhasedAdapter
from skillopt_oauth.envs.spex_write_phased.dataloader import SpexWritePhasedDataLoader

register_env(
    "spex_write_phased",
    adapter_cls=SpexWritePhasedAdapter,
    loader_cls=SpexWritePhasedDataLoader,
    default_config="configs/spex_write_phased/default.yaml",
)

__all__ = ["SpexWritePhasedAdapter", "SpexWritePhasedDataLoader"]
