---
name: new
description: Explicit-request macro. Activate only when the user directly requests this macro; never infer activation from task characteristics. Skill — Scaffold a custom macro — an ordinary SKILL.md that behaves as a first-class member of the macros ecosystem. Writes to project scope (this repo) or user scope (all your projects) and pre-fills the composition line so the new macro composes with other skills.
---

Honor every skill explicitly activated in the user's request exactly once. If another activated skill is not yet loaded and the host provides a skill-loading mechanism, load it through that mechanism. Do not reload an active skill.

You are scaffolding a new custom macro for the user. A macro is not a special
object — it is a portable skill (`SKILL.md`) that carries the macros
**composition line**, which lets it participate when multiple skills are active
in the same request. Your job is to gather the macro's name, description, and
behavior, then write a correct skill file to the right scope.

## 1. Resolve scope

Decide where the macro lives from what the user already said — do not ask if
it is clear:

- **User scope** → the current host's documented user skill root. The macro is
  available in every project. Choose this when the user says things like "for
  all my projects", "everywhere", "globally", or is describing a personal
  working habit.
- **Project scope** → the current host's documented project skill root.
  Committed, shared with the team. Choose this when the user says "in this
  repo", "for the team", "commit it", or the behavior is repo-specific.

Resolve the concrete root from the current host's instructions or documented
configuration. Do not guess a provider-specific path. If either the scope or
root is genuinely ambiguous, ask once. Otherwise proceed and state which path
you picked.

## 2. Pick a non-colliding name

The name is a kebab-case slug. Refer to the standalone skill by its unqualified name, `<name>`.

**Default: prefix user-scope macros with `my-`.** So a user macro for avoiding
time estimates becomes `my-timeless`. This
reduces collisions with bundled or native skill names. The user can pick a
different prefix (`u-`, their initials, whatever) — honor it and keep it
consistent across every macro you scaffold for them. Project-scope macros are
unprefixed unless the user asks otherwise.

Before committing to a name, list the skills in the resolved user and project
roots so `<name>` is unambiguous.

Also avoid the bundled macro names (mapreduce, doubt, consensus, seq, rigor,
askme, delegate, timeless, chunked, orchestrate, dry-run, dredge, timestamp,
tmi, new). If the desired name collides, propose a distinct one and say why.

## 3. Gather name, purpose, and body

- **name** — from the user, or suggest one from their description.
- **purpose** — one concise sentence describing what the macro does. It follows
  the shared explicit-request gate in the generated skill description.
- **body** — the macro's actual instructions, written in the second person as
  a prompt to the agent ("Do not include time estimates…", "Spawn N blind
  agents…"). If the user gave you the behavior in prose, refine it into clear
  imperative instructions. If it is thin, ask for the specifics you need — do
  not invent behavior.

Keep the body self-contained: it must fully describe its own concern without
assuming which other macros are present. That self-containment is exactly what
makes it compose cleanly with the rest of the ecosystem.

## 4. Write the file

Create the directory and write `SKILL.md` with this exact shape. The
composition line must be copied **verbatim** and placed immediately after the
frontmatter — it is the one thing that makes the macro quasi-native:

```markdown
---
name: <name>
description: Explicit-request macro. Activate only when the user directly requests this macro; never infer activation from task characteristics. Skill — <one-line purpose>
---

Honor every skill explicitly activated in the user's request exactly once. If another activated skill is not yet loaded and the host provides a skill-loading mechanism, load it through that mechanism. Do not reload an active skill.

<body>
```

If the macro produces files or has configurable behavior, follow the layered
config convention (`.agents/skill-configs/<name>/` for project scope,
`~/.agents/skill-configs/<name>/` for user scope) and ship a
`config.example.yaml` next to the `SKILL.md`. Most macros are pure
behavior-modifiers and need none of this — skip it unless the behavior
actually reads config.

## 5. Confirm

Tell the user:

- the path written and the scope,
- its name (`<name>`), and
- that it composes with other explicitly activated skills, such as `macros:doubt`.

State whether the current host discovers new skills immediately or requires a
new session, when that behavior is known.
