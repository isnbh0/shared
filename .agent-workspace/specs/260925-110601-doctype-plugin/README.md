# Doctype Plugin

**Date:** 2026-09-25 11:06:01
**Issue:** `zoomdoc` is published alone while the mature tractatus viewer exists only as a personal dotfiles skill; users need one plugin offering both document formats.
**Priority:** Medium
**Status:** In Progress
**Started:** 2026-09-25

## Problem Statement

The marketplace lists `zoomdoc` at `plugins/zoomdoc/`, with one skill and its renderer and validator. The tractatus skill, template, embedding script, example, and tests are absent from this repository. Its personal instructions also assume an `inbox/` output directory. Publishing the original tractatus proposal as a separate plugin would leave two related document skills under separate installs. The target is a `doctype` marketplace plugin with independent `zoomdoc` and `tractatus` resident skills. The old standalone `zoomdoc` marketplace entry is deprecated and removed after the replacement package is verified. Existing zoomdoc document markup and behavior remain valid.

This spec includes a tracked snapshot in `reference/tractatus/`, copied from the personal skill at specification time. The original proposal was local and untracked; all implementation inputs needed from it are recorded here. The snapshot contains the tractatus skill, template, embed script, example Markdown, and viewer tests. The generated example HTML and its converter are absent; the Markdown is the example data.

The synthetic test fixture is named `fake-tractatus.txt` in the snapshot because it deliberately contains a blocked `javascript:` link that the repository Markdown-link checker would otherwise treat as a broken local link. Its content is unchanged, and the snapshot test harness reads the new name.

## Design Principles

1. **Separate document models** — Keep semantic zoom and numbered outline authoring as distinct skills within one plugin; preserve their individual invocation names and runtime formats.
2. **One source in shared** — The published package owns both skills. Tractatus tests live in repository development space and stay out of the plugin archive.
3. **Incremental delivery** — Every phase leaves the system working.
4. **Verified phases** — Every phase has runnable completion checks.

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Plugin and skill names | `doctype` plugin; `zoomdoc` and `tractatus` skills | One install, two distinct authoring models. |
| Initial version | `doctype` 1.0.0 | First release of the new plugin identity. |
| Zoomdoc migration | Move the existing skill directory without altering document syntax or validator behavior | Keeps generated documents and authoring guidance valid. |
| Tractatus source | Port the tracked snapshot under `reference/tractatus/` | A fresh clone contains the source; no machine-local dependency. |
| Tractatus output | User path wins; otherwise ask once for `output_dir` and save it in `.agents/skill-configs/tractatus/config.yaml` | Removes the personal `inbox/` assumption. |
| Tractatus tests | `tests/doctype/tractatus/`, outside `plugins/doctype/` | Retains regression coverage without adding tests to packaged agent context. |
| Marketplace transition | Publish `doctype`, replace the `zoomdoc` listing, remove `plugins/zoomdoc/` after checks | No duplicate marketplace skills after migration. |
| Math loading | Keep MathJax 3.2.2 CDN behavior and disclose it in documentation | Math pages fetch script and fonts online; TeX source remains visible offline. |

## Deferred Features

- Retiring the personal dotfiles `my-tractatus` source, symlink check, and `install.sh` entry requires a separate change in the dotfiles repository after `doctype` is published. Shared is the intended source of truth; the external cleanup must not be mistaken for a shared-repo file edit.
- Real iPhone and Android checks with VoiceOver and TalkBack are recommended follow-up validation; Playwright emulation remains the automated gate.
- Changing either document viewer's behavior or combining their formats is outside this migration.

## Phase Summary

| Phase | Name | Tests Required | Backward Compatible |
|-------|------|----------------|---------------------|
| 1 | Build and test the doctype package | Zoomdoc file parity and validator smoke; tractatus Python and browser regression suite; package archive audit | Yes |
| 2 | Switch marketplace and documentation | Repository checker, marketplace/package assertions, documentation search | Existing documents: yes; old plugin install identifier: deprecated |

## Phase Documents

1. [P1-build-doctype.md](./P1-build-doctype.md) — Create both resident skills and migrate tractatus tests.
2. [P2-publish-doctype.md](./P2-publish-doctype.md) — Publish `doctype`, remove the standalone listing, and update documentation.

## Progress Tracking

| Phase | Commit | Status |
|-------|--------|--------|
| 1 | — | Pending |
| 2 | — | Pending |

## Viewer Network Behavior

The viewer's CSP permits MathJax from `cdn.jsdelivr.net` and its font directory. Pages without math do not need MathJax; pages with math request it when online and show TeX source offline.

The configured spec workspace is ignored by `.gitignore`; this specification directory must be staged explicitly with `git add -f`. The implementation paths under `plugins/doctype/` and `tests/doctype/` are not ignored.
