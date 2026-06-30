# Vendored upstream: Microsoft SkillOpt

This tree is a **trimmed, pinned snapshot** of upstream
[microsoft/SkillOpt](https://github.com/microsoft/SkillOpt), vendored so we can
add a `codex_chat` optimizer backend (a CLI-backed optimizer that runs on the
ChatGPT/codex OAuth subscription) without an upstream release.

- **Pinned ref:** `v0.1.0` (commit `25da7cb2ddc26eb67eb6cb386915f269d7ee42cf`)
- **Vendored subset:** `skillopt/`, `scripts/`, `configs/`, `data/`,
  `pyproject.toml`, `requirements.txt`, `README.md`, `LICENSE`, `SECURITY.md`.
  Dropped (not imported by the runtime package): `skillopt-assets/`,
  `skillopt_webui/`, `docs/`, `ckpt/`, `*.html`, `mkdocs.yml`, upstream `tests/`.
- **Install:** editable path source from `tooling/skillopt/pyproject.toml`
  (`[tool.uv.sources] skillopt = { path = "vendor/skillopt", editable = true }`),
  so `uv sync` builds this tree and provides the `skillopt-train` console script.

## Local delta vs. upstream

Our changes live in a single follow-up commit on top of the pristine snapshot, so
`git log`/`git show` on the patch commit is the full diff. Summary:

- `skillopt/model/__init__.py` — dispatch `codex_chat` optimizer to
  `codex_backend`; wire its deployment/reasoning-effort setters.
- `skillopt/model/backend_config.py` — allow `codex_chat` as an optimizer backend.
- `skillopt/model/common.py` — `codex_chat` default model.

## Re-vendoring / rebasing onto a newer upstream

1. `git clone --depth 1 --branch <new-tag> https://github.com/microsoft/SkillOpt`.
2. Re-copy the vendored subset over this tree (same item list as above).
3. Re-apply the local delta (cherry-pick the patch commit, or replay the
   `skillopt/model/` edits — they are small and self-contained).
4. Update the pinned ref above and run `uv sync` + the test suite.
