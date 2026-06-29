"""Training entrypoint for SkillOpt-OAuth.

STUB STATE (Phase 1): only `--dry-run` is wired — it loads config and lists registered
environments without running any training or making any LLM calls.
FUTURE: Phases 2-5 fill in the actual epoch/step training loop behind the default
(non-dry-run) path: build the executor, register the oauth_cli backend, run
rollouts/reflection through the scheduler, gate candidates, and checkpoint each step.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import asdict

from .config import Config, load_config
from .registry import list_envs  # registration is triggered by the package __init__


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skillopt-oauth",
        description="OAuth-CLI fork of Microsoft SkillOpt.",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="path to a YAML config file; defaults are used when omitted",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="list registered environments and the loaded config, then exit",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    config = load_config(args.config) if args.config else Config()

    if args.dry_run:
        envs = list_envs()
        print("SkillOpt-OAuth dry run")
        print(f"registered environments ({len(envs)}): {envs}")
        print("config:")
        for key, value in asdict(config).items():
            print(f"  {key} = {value!r}")
        return 0

    parser.error("training loop is implemented in later phases; use --dry-run for now")
    return 2  # unreachable: parser.error() exits with status 2


if __name__ == "__main__":
    sys.exit(main())
