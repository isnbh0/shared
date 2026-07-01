"""Config-example regression tests for the pi backend.

Guards two invariants that a doc/config drift would silently break:
  1. `pi_exec_thinking` in the shipped default.yaml must be the STRING "off" -- a bare `off`
     becomes PyYAML `False` and would render as `--thinking false` (an invalid argv value).
  2. Every documented routing recipe that pins a metered provider must carry the
     `pi_allowed_metered_providers` opt-in line (the intended UX under skillopt-oauth).
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

_REPO = Path(__file__).resolve().parents[1]
_DEFAULT_YAML = _REPO / "vendor" / "skillopt" / "configs" / "_base_" / "default.yaml"


def test_default_yaml_pi_keys_present_and_thinking_is_quoted_off():
    data = yaml.safe_load(_DEFAULT_YAML.read_text(encoding="utf-8"))
    model = data["model"]
    assert model["pi_exec_path"] == "pi"
    assert model["pi_exec_provider"] == "openai-codex"
    assert model["pi_exec_use_sdk"] == "cli"
    # CRITICAL: the string "off", not the bool False (bare `off` -> PyYAML False).
    assert model["pi_exec_thinking"] == "off"
    assert model["pi_exec_thinking"] is not False
    assert isinstance(model["pi_exec_thinking"], str)
    # the guard opt-in key ships empty by default (block accidental; allow intentional).
    assert model["pi_allowed_metered_providers"] == []


# The three documented routing recipes (kept in lockstep with README.md).
_RECIPE_A = """
model:
  optimizer_backend: pi_chat
  target_backend: pi_exec
  optimizer: anthropic/claude-x
  target: zai/glm-5.2
  pi_allowed_metered_providers: [zai, anthropic]
"""

_RECIPE_B = """
model:
  optimizer_backend: pi_chat
  target_backend: pi_exec
  optimizer: zai/glm-5.2
  target: anthropic/claude-x
  pi_allowed_metered_providers: [zai, anthropic]
"""

_RECIPE_C = """
model:
  optimizer_backend: pi_chat
  target_backend: pi_exec
  optimizer: zai/glm-5.2
  target: zai/glm-5.2
  pi_allowed_metered_providers: [zai]
"""


def _metered_providers_in(recipe: dict) -> set[str]:
    """Providers pinned on either role that are NOT in the built-in subscription set."""
    subscription = {"openai-codex", "github-copilot"}
    out: set[str] = set()
    for role in ("optimizer", "target"):
        dep = str(recipe["model"].get(role) or "")
        if "/" in dep:
            prov = dep.split("/", 1)[0]
            if prov not in subscription:
                out.add(prov)
    return out


@pytest.mark.parametrize("raw", [_RECIPE_A, _RECIPE_B, _RECIPE_C])
def test_routing_recipes_opt_in_covers_every_metered_role(raw):
    recipe = yaml.safe_load(raw)
    # The opt-in key is nested under `model:` -- the resolver's real contract
    # (_resolve_pi_allowed_metered reads data["model"]["pi_allowed_metered_providers"],
    # matching default.yaml and config.py). Assert against that same path, NOT a top-level key.
    opted_in = set(recipe["model"].get("pi_allowed_metered_providers") or [])
    metered = _metered_providers_in(recipe)
    # every metered provider a role pins must be opted in (required under skillopt-oauth).
    assert metered <= opted_in, f"un-opted metered providers: {metered - opted_in}"


@pytest.mark.parametrize("raw", [_RECIPE_A, _RECIPE_B, _RECIPE_C])
def test_routing_recipes_use_pi_backends(raw):
    recipe = yaml.safe_load(raw)["model"]
    assert recipe["optimizer_backend"] == "pi_chat"
    assert recipe["target_backend"] in {"pi_chat", "pi_exec"}
