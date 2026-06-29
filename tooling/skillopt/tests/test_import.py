import importlib


def test_package_imports():
    mod = importlib.import_module("skillopt_oauth")
    assert hasattr(mod, "__version__")
    assert isinstance(mod.__version__, str)


def test_top_level_reexports():
    import skillopt_oauth

    assert hasattr(skillopt_oauth, "Config")
    assert hasattr(skillopt_oauth, "load_config")
    assert hasattr(skillopt_oauth, "register_env")
    assert hasattr(skillopt_oauth, "list_envs")


def test_submodules_import_cleanly():
    # Stub modules must import without triggering any behavior (NotImplementedError
    # only fires on instantiation/call, never at import time).
    for name in (
        "config",
        "registry",
        "base",
        "envs",
        "executor",
        "scheduler",
        "backends",
        "reflect",
        "gate",
        "checkpoint",
        "train",
    ):
        importlib.import_module(f"skillopt_oauth.{name}")
