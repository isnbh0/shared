import pytest

from skillopt_oauth import registry


class _Adapter:  # stand-ins for the EnvAdapter / SplitDataLoader classes (Phase 4)
    pass


class _Loader:
    pass


@pytest.fixture(autouse=True)
def _clean_registry():
    """Snapshot and restore the module-global registry so tests don't leak state."""
    snapshot = dict(registry._ENV_REGISTRY)
    try:
        yield
    finally:
        registry._ENV_REGISTRY.clear()
        registry._ENV_REGISTRY.update(snapshot)


def test_starts_empty():
    assert registry.list_envs() == []


def test_register_and_get_round_trip():
    registry.register_env("dummy", adapter_cls=_Adapter, loader_cls=_Loader,
                          default_config="configs/dummy/default.yaml")
    assert registry.list_envs() == ["dummy"]
    spec = registry.get_env("dummy")
    assert spec.adapter_cls is _Adapter
    assert spec.loader_cls is _Loader
    assert spec.default_config == "configs/dummy/default.yaml"


def test_list_envs_is_sorted():
    registry.register_env("b_env", adapter_cls=_Adapter, loader_cls=_Loader)
    registry.register_env("a_env", adapter_cls=_Adapter, loader_cls=_Loader)
    assert registry.list_envs() == ["a_env", "b_env"]


def test_duplicate_registration_raises():
    registry.register_env("dup", adapter_cls=_Adapter, loader_cls=_Loader)
    with pytest.raises(ValueError):
        registry.register_env("dup", adapter_cls=_Adapter, loader_cls=_Loader)


def test_get_unknown_env_raises():
    with pytest.raises(KeyError):
        registry.get_env("nope")
