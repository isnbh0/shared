---
name: layout-grounding
description: Ground layout in grouping, reading order, and shared spatial rules that remain legible as content and context change. Use only when explicitly requested.
disable-model-invocation: true
---

Honor every skill explicitly activated in the user's request exactly once. If another activated skill is not yet loaded and the host provides a skill-loading mechanism, load it through that mechanism. Do not reload an active skill.

When an artifact exists, start from its rendered layout where practical, using the implementation to understand what you see. Consider what appears grouped, what draws attention first, and which reading path the composition suggests. Look for unintended ambiguity in membership, hierarchy, and alignment, even when boxes share coordinates. For a new layout, begin with representative content and the reader's task.

Model the relationships before choosing distances. Identify content units, nested groups, comparable values, primary actions, and reading order. Give each group a clear spatial home. When proximity communicates membership, keep related parts closer than neighboring groups and preserve that distinction through nested levels. Choose spacing for the relationship and density at hand.

Define shared axes, baselines, tracks, and reading measures where they express a useful relationship. Align the parts readers compare: text baselines, value columns, or visible shapes may matter more than outer boxes. Use scale, spacing, and contrast together to establish hierarchy. Use optical corrections where visible alignment needs them; share them when the same visual role recurs.

Put repeated decisions in shared layout rules. Let a parent stack, row, grid, or equivalent constraint own the gaps and alignment among its children. Keep component anatomy, meaningful variants, and spacing tokens distinct: anatomy defines the parts and their relationships; variants describe supported differences; tokens supply values. Reuse the project's system where it expresses the intended relationship. Introduce a shared rule when representative cases establish its purpose.

Treat concerns that cross component boundaries as aspects with clear scope and ownership. Typography, density, theme, or interaction state may affect several components together. Clarify how overlapping rules combine and which takes precedence where they could conflict. For example, a compact-density setting should adjust spacing coherently across components while preserving membership and usable controls. Encode these rules where all affected components can follow them.

Preserve relationships as content and context change. Let wrapping, intrinsic sizing, flexible measures, and logical directions absorb variation. Change structure when those adjustments can no longer preserve grouping, reading order, comparison, or access to actions. Choose breakpoints from an observed failure with real content. Distinguish interface anchors from content flow. Keep navigation and controls stable across interaction states; let translated or enlarged content reflow naturally. Reserve space only when it preserves a meaningful comparison or reading relationship. Judge geometric stability by its benefit to the reader, including its cost to spacing, readability, and density.

Repair the rule that owns the broken relationship, sharing the fix when the same cause affects other contexts. When local adjustments accumulate, inspect the owning group, shared track, type metrics, and rule precedence. Use exceptions when they improve a specific reading or interaction need, and check that they preserve surrounding relationships. Remove superseded local patches after the shared repair.

Check the delivered layout in representative conditions likely to stress the relationships you changed. Useful cases include long content, empty states, zoom, supported writing directions, and widths around structural transitions. Confirm the relevant relationships: labels belong to their controls, comparison axes remain clear, actions remain reachable, and visual order agrees with reading and focus order. Include interacting aspects where they could expose a problem, such as compact density with large text or a wrapped error message. Use focused geometry or behavior checks when they can expose a concrete failure, and judge visible grouping and hierarchy directly.
