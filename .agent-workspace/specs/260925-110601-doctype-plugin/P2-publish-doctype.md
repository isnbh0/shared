## Phase 2: Switch marketplace and documentation to doctype

**Goal:** Publish one `doctype` plugin containing `zoomdoc` and `tractatus`, and retire the standalone `zoomdoc` marketplace package.
**Entry state:** Phase 1 committed a working `plugins/doctype/` with both skills and `tests/doctype/tractatus/`; `plugins/zoomdoc/` remains published.
**Exit state:** The marketplace lists `doctype` and not `zoomdoc`; public docs describe both skills under doctype; `plugins/zoomdoc/` is removed; all repository and package checks pass. Existing zoomdoc HTML documents still use the same markup and runtime behavior.

### Implementation Checklist

- [ ] Replace the `zoomdoc` entry with `doctype` in `.claude-plugin/marketplace.json`, pointing to `./plugins/doctype`.
- [ ] Remove `plugins/zoomdoc/` after verifying the copied zoomdoc skill in `plugins/doctype/skills/zoomdoc/` remains equivalent except for the attribution URL.
- [ ] Update `README.md`, `README.ko.md`, and `llms.txt`: marketplace and direct-install blocks, plugin list/count, published skills, source paths, file tree, workspace config note, and guidance to use the `doctype` package. Describe the old `zoomdoc` install identifier as deprecated in migration guidance; describe `zoomdoc` as a continuing skill.
- [ ] In the README entries disclose that tractatus pages containing math request MathJax 3.2.2 and fonts from `cdn.jsdelivr.net` when online, with visible TeX source offline.
- [ ] Update any other tracked references discovered by `rg -n 'plugins/zoomdoc|zoomdoc@|zoomdoc-latest'` so they point to the current package, except explicit migration notes.
- [ ] Add or update tests described below.
- [ ] Run the verification commands below.
- [ ] Commit: `feat(doctype): publish document skills and retire zoomdoc plugin`

### Code

Keep the skill names `zoomdoc` and `tractatus`; the package name alone changes to `doctype`. Direct installers now copy `plugins/doctype/skills/zoomdoc/` or `plugins/doctype/skills/tractatus/`. Claude marketplace users install `doctype` to receive both. The old standalone package is removed from the catalog and repository, but already-generated zoomdoc HTML stays usable because the markup and runtime are preserved. Do not claim that the former marketplace identifier remains installable.

The `README.md`, `README.ko.md`, and `llms.txt` publishing sections already include `zoomdoc` in install commands, one-shot archive URLs, the published plugin enumeration, and skill descriptions. `llms.txt` also has a file tree and Notes for LLMs entry. Update those locations as current truth. Check `docs/cross-platform/README.md` only if a concrete stale source path appears. Do not duplicate provider-specific install roots in portable skill content.

Shared is the authoritative source after this phase. Retirement of the personal dotfiles skill and its links is a separate repository change, recorded as follow-up in the overview. No path to a personal checkout is required to implement this phase.

### Required Tests

**Files:** `tests/doctype/tractatus/test_skill_package.py` (UPDATE if package assertions need final marketplace state); `scripts/check-repo.rb` (UPDATE only if an existing checker misses a concrete packaging error).

Assert that the marketplace entry resolves to a manifest named `doctype` at version `1.0.0`, that its archive contains both `skills/zoomdoc/` and `skills/tractatus/`, and that it contains no `tests/`. Verify the old `plugins/zoomdoc/` path and standalone marketplace entry are gone. Rerun the tractatus behavioral suite after relocation and confirm the zoomdoc validator still accepts a valid document. Existing repository checks should remain the main publishing gate; do not add redundant test code if the current checker and a small archive assertion cover these facts.

### Example Workflow

```sh
uv run --with pytest --with pytest-playwright --with hypothesis pytest tests/doctype -q
doctype_tmp_dir="$(mktemp -d)"
bash scripts/pack-plugin.sh doctype "$doctype_tmp_dir"
unzip -l "$doctype_tmp_dir/doctype.zip"
rg -n 'plugins/zoomdoc|zoomdoc@|zoomdoc-latest' .claude-plugin README.md README.ko.md llms.txt docs scripts
ruby scripts/check-repo.rb
git status --short
```

The browser suite and repository checker pass. The archive includes the two skill trees and excludes tests. The reference search finds only intentional migration prose, if any. The working tree is clean after the phase commit.
