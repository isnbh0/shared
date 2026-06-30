#!/usr/bin/env bash
# Real, dual-identity optimization of the `timestamp` skill.
#
# Starts from a deliberately BAD initial skill (initial_bad.md, which never
# mentions timestamps) so you can watch the frozen-val score climb 0 -> 1 as the
# loop learns the rule. Rollouts run on the Claude subscription; reflection runs
# on the codex / ChatGPT identity (dual identity).
#
# Requires a subscription-OAuth `claude` login and a ChatGPT-OAuth `codex` login.
# Spends real subscription tokens (~20 CLI calls, ~2 min). NO API keys are used:
# the executor scrubs *_API_KEY from the child env and fails closed unless an
# OAuth credential is confirmed.
#
# Usage:  ./run.sh [OUT_DIR]   (default OUT_DIR = ./run-out next to this script)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE/../.."                      # tooling/skillopt (package root)
OUT="${1:-$HERE/run-out}"
rm -rf "$OUT"; mkdir -p "$OUT"

uv run python -m skillopt_oauth.train \
  --env timestamp --epochs 1 --steps-per-epoch 2 \
  --batch-size 2 --n-samples 1 \
  --initial-skill "$HERE/initial_bad.md" \
  --rollout-provider claude --reflect-provider codex \
  --out-dir "$OUT"

echo
echo "== trajectory (frozen-val hard score per skill-doc hash) =="
OUT_DIR="$OUT" uv run python "$HERE/show_trajectory.py"
echo
echo "== best_skill.md (the learned skill) =="
cat "$OUT/best_skill.md"
