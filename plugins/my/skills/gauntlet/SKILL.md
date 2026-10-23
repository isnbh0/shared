---
name: gauntlet
description: Build a fast, blinded A/B choice page from rendered excerpts of the person's own material, to collect intuitive judgments they can't easily put into words. Use only when explicitly requested.
disable-model-invocation: true
---

A gauntlet collects intuitive data. The person picks one of two rendered alternatives, quickly and
without explaining. You build the page, check it, hand it over and take back the answers. What the
data is for belongs to the work that asked for it.

Only the person answers. Never fill in, infer or simulate their answers, except with a simulated
reader while checking a page.

## Building

Start from `assets/gauntlet.tpl.html`, or `assets/gauntlet-adaptive.tpl.html` when each pair
depends on the answers so far. `references/interface.md` describes the features to keep and how to
fill a template. You write the project side: snapshotting the material, generating the trials and
writing `srcdoc()`.

Use snapshots of the person's real material. Keep the key out of the page, and keep a page to a
short sitting. `references/techniques.md` is a menu of ways to shape pairs, check the data and
find edges.

## Handing over

Before the person sees the page, make sure it works. Pairs meant to differ must actually differ,
nulls must match, and the page must reach its done screen. A pair that quietly renders the same
wastes part of the sitting. `references/interface.md` has ways to check. Then give the person the
command to open the page, the pair count, the controls and the export filename, and wait for the
export.

## Taking back

Validate the export against what was built: the key and trial IDs for a fixed page, and the search
IDs for an adaptive one. Lead with anything that undermines the data, such as a count mismatch, a
null answered A or B, or a flipped repeat. Then give the choices. Read time and swaps can show
which calls were hard.
