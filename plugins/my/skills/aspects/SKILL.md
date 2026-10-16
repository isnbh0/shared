---
name: aspects
description: Design across overlapping concerns and make their composition explicit. Use only when explicitly requested.
disable-model-invocation: true
---

Honor every skill explicitly activated in the user's request exactly once. If another activated skill is not yet loaded and the host provides a skill-loading mechanism, load it through that mechanism. Do not reload an active skill.

Treat a design as the composition of concerns, not only as a tree of components. A concern may apply to many parts of a system at once, and one part may participate in several concerns. Look for those relationships before choosing file boundaries, selectors, abstractions, or tools.

When designing or changing an interface, identify the concerns that matter to the task: for example, content structure, typography, spacing, theme, interaction state, accessibility, input method, language direction, and viewport. State the design intent for each relevant concern and which regions it should affect. A language change may alter content height while leaving navigation geometry unchanged; define that boundary where the concerns compose. Do not force a crosscutting rule into each component merely because the DOM or component hierarchy is a tree.

In CSS, treat selectors as the places where rules attach and the cascade as the mechanism that combines them. Choose selectors, inheritance, custom properties, component styles, `@scope`, and cascade layers according to the job each must do. Cascade layers order precedence; they do not by themselves identify the concerns, express the intended scope, or resolve interactions among them. Do not translate a request for aspect-oriented design into `@layer` by default.

Make interactions visible. Ask which rules overlap, which combinations are intended, and what happens at the boundaries. A few deliberate exceptions can use local overrides. Repeated exceptions are evidence to inspect the design intent, selector, inheritance path, or composition rule. Check representative combinations that could reveal interference, especially when changing a shared rule. Prefer the smallest check that could expose the actual conflict.

Apply the same reasoning beyond CSS when a concern crosses structural boundaries. Keep the concern legible and give it a coherent place to be changed. Choose a composition mechanism that fits the system; do not add an aspect framework merely because the concern is crosscutting.

This principle draws on the author's notes [AOP and CSS](https://wiki.g15e.com/pages/AOP%20and%20CSS), [It is not a tree](https://wiki.g15e.com/pages/It%20is%20not%20a%20tree), [Tailwind](https://wiki.g15e.com/pages/Tailwind), and [Declarative design and design runtime](https://wiki.g15e.com/pages/Declarative%20design%20and%20design%20runtime). The instructions above stand on their own; use the notes when the task calls for deeper design reasoning.
