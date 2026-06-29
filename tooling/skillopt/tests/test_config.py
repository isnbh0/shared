import textwrap

import pytest

from skillopt_oauth.config import Config, load_config


def test_defaults_match_spec():
    cfg = Config()
    assert cfg.batch_size == 40
    assert cfg.minibatch_size == 8
    assert cfg.lr == 4
    assert cfg.min_lr == 2
    assert cfg.lr_schedule == "cosine"
    assert cfg.slow_update_samples == 20
    assert cfg.claude_pool == 6
    assert cfg.codex_pool == 6
    assert cfg.rate_per_min == 60.0
    assert cfg.gate_mode == "variance"
    assert cfg.reflection_mode == "parallel"
    assert cfg.n_samples == 3
    assert cfg.model_claude is None
    assert cfg.model_codex is None
    assert cfg.reasoning_effort == "xhigh"
    assert cfg.forbid_api_keys is True


def test_load_empty_yaml_yields_defaults(tmp_path):
    p = tmp_path / "empty.yaml"
    p.write_text("", encoding="utf-8")
    assert load_config(p) == Config()


def test_load_overrides(tmp_path):
    p = tmp_path / "cfg.yaml"
    p.write_text(
        textwrap.dedent(
            """
            batch_size: 8
            n_samples: 5
            model_claude: claude-x
            gate_mode: strict
            """
        ),
        encoding="utf-8",
    )
    cfg = load_config(p)
    assert cfg.batch_size == 8
    assert cfg.n_samples == 5
    assert cfg.model_claude == "claude-x"
    assert cfg.gate_mode == "strict"
    # untouched fields keep their defaults
    assert cfg.minibatch_size == 8
    assert cfg.lr == 4


def test_unknown_keys_ignored(tmp_path):
    # Env-specific YAML (Phase 4) may carry extra sections; they must not break loading.
    p = tmp_path / "cfg.yaml"
    p.write_text("tasks_dir: ./tasks\nbatch_size: 12\n", encoding="utf-8")
    cfg = load_config(p)
    assert cfg.batch_size == 12


def test_non_mapping_root_raises(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text("- a\n- b\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_config(p)
