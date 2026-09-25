## Phase 1: Build and test the doctype package

**Goal:** Create a working, unpublished `doctype` package with both resident skills and repository-local tests.
**Entry state:** `plugins/zoomdoc/skills/zoomdoc/` is the published zoomdoc skill; `reference/tractatus/` in this spec is the tracked tractatus source; `doctype` does not exist.
**Exit state:** `plugins/doctype/` packages working `zoomdoc` and `tractatus` skills; the original zoomdoc marketplace entry still works; tractatus tests run from `tests/doctype/tractatus/` and are absent from the plugin archive.

### Implementation Checklist

- [x] Create `plugins/doctype/.claude-plugin/plugin.json` with name `doctype`, version `1.0.0`, author `isnbh0`, and a description covering both document formats.
- [x] Copy `plugins/zoomdoc/skills/zoomdoc/` to `plugins/doctype/skills/zoomdoc/` without changing renderer or validator semantics. Keep its `config.example.yaml`.
- [x] Copy `reference/tractatus/template.html`, `embed.py`, and `examples/tractatus.md` to `plugins/doctype/skills/tractatus/`. Port `reference/tractatus/SKILL.md` with frontmatter name `tractatus`, portable names, config-driven output, and accurate example paths. Add `config.example.yaml` documenting `output_dir`.
- [x] Copy `reference/tractatus/tests/` into `tests/doctype/tractatus/` and put `pytest.ini` at the appropriate test root. Change paths and personal-install assertions needed by the new layout; replace the symlink and installer checks in `test_skill_package.py` with package, config, and example checks. Keep viewer behavioral coverage.
- [x] Update the zoomdoc template attribution link from `plugins/zoomdoc` to `plugins/doctype/skills/zoomdoc` in the copied template.
- [x] Add or update tests described below.
- [x] Run the verification commands below.
- [x] Commit: `feat(doctype): package zoomdoc and tractatus skills with tests`

### Code

The two skill directories are `plugins/doctype/skills/zoomdoc/` and `plugins/doctype/skills/tractatus/`. Do not rename `data-zoomdoc-*` attributes, change the zoomdoc document model, or merge the two templates. The tractatus template, `embed.py`, and Markdown example come from the snapshot exactly, except for paths or attribution that must change for publication. `embed.py` is a dependency-free PEP 723 script requiring Python 3.13 or newer; keep `uv run` as the documented command and mention `python3` as a fallback when uv is unavailable. It already requires an explicit `-o` path; the skill instructions resolve the default from config before invoking it. Do not add config parsing to `embed.py` solely for this migration.

The tractatus skill first uses a user-provided output path. Otherwise it reads `.agents/skill-configs/tractatus/config.local.yaml`, then `config.yaml`, relative to the working project. If neither exists, ask for an output directory, write `.agents/skill-configs/tractatus/config.yaml`, and use its `output_dir`; do not silently choose `inbox/`. Keep the skill's Markdown syntax, extraction workflow, deep-link behavior, and the help dialog guidance. Generate example HTML from the shipped Markdown with `embed.py` when a test needs it.

The snapshot's `tests/conftest.py` derives `SKILL_DIR` from its old location and needs a direct path to `plugins/doctype/skills/tractatus/`. `test_skill_package.py` asserts personal links and installer entries; replace those assertions. `test_spacing_panel.py` reads a committed example HTML that is not shipped; generate it in a temporary fixture from the shipped Markdown and template. Add an example smoke test that opens this generated page and checks its title, root items, and a deep link. The template's `my-tractatus:*` local-storage keys are a runtime compatibility contract; keep them unless a separately tested migration is explicitly chosen. Leave `tests/doctype/tractatus/` outside the plugin directory because `scripts/pack-plugin.sh` archives all files beneath a plugin except cache patterns. The existing `plugins/zoomdoc/` remains during this phase, so current marketplace installation continues to work.

### Required Tests

**Files:** `tests/doctype/tractatus/` (NEW, ported from `reference/tractatus/tests/`); `tests/doctype/tractatus/test_skill_package.py` and `test_spacing_panel.py` (UPDATE during port); `tests/doctype/tractatus/test_example.py` and `tests/doctype/test_zoomdoc.py` (NEW).

Preserve parse, rendering, selection, zoom, filter, deep-link, keyboard, touch, layout, math, CSP, embed/extract, and example coverage. Replace personal symlink/install assertions with: both `doctype` skill directories contain a matching frontmatter name; tractatus's documented heredoc and Markdown example render; the output configuration instructions and shipped example are present; the package archive contains both skills and excludes `tests/`. Update `conftest.py` path derivation and any other test assumptions exposed by relocation. Keep marked network tests opt-in using `TRACTATUS_NETWORK=1`.

Zoomdoc needs a parity check: the copied `SKILL.md`, `config.example.yaml`, and `validate.py` match the original files; its template differs only in the attribution link. In `tests/doctype/test_zoomdoc.py`, use a minimal valid semantic zoom HTML fixture to assert the moved validator returns no errors and confirm its command-line exit status is zero. Compile both Python scripts.

### Example Workflow

```sh
git diff --no-index plugins/zoomdoc/skills/zoomdoc/SKILL.md plugins/doctype/skills/zoomdoc/SKILL.md
uv run --with pytest --with pytest-playwright --with hypothesis pytest tests/doctype -q
doctype_tmp_dir="$(mktemp -d)"
uv run plugins/doctype/skills/tractatus/embed.py plugins/doctype/skills/tractatus/examples/tractatus.md -o "$doctype_tmp_dir/tractatus.html"
uv run plugins/doctype/skills/tractatus/embed.py --extract "$doctype_tmp_dir/tractatus.html" > "$doctype_tmp_dir/tractatus.md"
cmp plugins/doctype/skills/tractatus/examples/tractatus.md "$doctype_tmp_dir/tractatus.md"
bash scripts/pack-plugin.sh doctype "$doctype_tmp_dir"
unzip -l "$doctype_tmp_dir/doctype.zip"
ruby scripts/check-repo.rb
```

The first diff and `cmp` return zero; the browser suite and repository checker pass; the archive lists both skill directories and no tests. Install Chromium and WebKit for the browser suite if they are not already installed. The new plugin is still absent from `.claude-plugin/marketplace.json` at phase exit.
