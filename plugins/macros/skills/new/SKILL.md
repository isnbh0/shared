---
name: new
description: Explicit-request macro. Activate only when the user directly requests this macro; never infer activation from task characteristics. Skill — Scaffold a custom macro for a project or user and selected agent hosts, with one source directory and the macros composition line.
---

Honor every skill explicitly activated in the user's request exactly once. If another activated skill is not yet loaded and the host provides a skill-loading mechanism, load it through that mechanism. Do not reload an active skill.

You are scaffolding a new custom macro for the user. A macro is not a special
object — it is a portable skill (`SKILL.md`) that carries the macros
**composition line**, which lets it participate when multiple skills are active
in the same request. Your job is to gather the macro's name, description, and
behavior, then write a correct skill file to the right scope.

## 1. Resolve scope and host coverage

Decide two things from what the user already said — do not ask if they are clear:

- **Scope:** user for "all my projects", "everywhere", "globally", or a
  personal working habit; project for "in this repo", "for the team", "commit
  it", or repo-specific behavior. Project skills are committed for the team.
- **Host coverage:** use the current host by default. Select named hosts when
  the user asks for them (for example, "Codex and Claude" or "both tools") or
  a standing user instruction requires them. An explicit host-only request
  overrides a standing multi-host preference. "All my projects" alone does
  not mean all agent hosts.

Resolve each selected host's root for the chosen scope from locally managed
configuration or current host documentation. The
[cross-platform root table](https://github.com/isnbh0/shared/blob/main/docs/cross-platform/README.md)
lists common roots; verify uncertain paths in current host docs. If scope,
coverage, or a root is genuinely ambiguous, ask once. Otherwise proceed and
state the selected scope and hosts.

## 2. Pick a non-colliding name

The name is a kebab-case slug. Refer to the standalone skill by its unqualified name, `<name>`.

**Default: prefix user-scope macros with `my-`.** So a user macro for avoiding
time estimates becomes `my-timeless`. This
reduces collisions with bundled or native skill names. The user can pick a
different prefix (`u-`, their initials, whatever) — honor it and keep it
consistent across every macro you scaffold for them. Project-scope macros are
unprefixed unless the user asks otherwise.

Before writing, check the name in every selected host's target root and in
its other discoverable roots for the current project. Resolve existing links.
If one target already contains the requested macro and its source fits the
chosen scope, use it as the source and link missing targets; if all targets
already resolve there, avoid a second copy. A project skill must resolve to
a source in the repository. A same-name skill with different behavior, or
targets pointing to different sources even when their text matches, is a
collision. Offer a distinct name or an explicit consolidation instead of
overwriting anything. Complete these checks before creating any files or links.

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

Choose one durable source directory. For project scope, keep the source in
the repository and link the whole skill directory from any other selected
project roots. For user scope, use the tracked source and update the install
map when the user's dotfiles or installer manages skill roots; otherwise use
one selected user root as the source. Link the whole directory into other
selected roots so supporting files and relative references keep working. Do
not maintain independent copies of `SKILL.md`.

Create the source directory and write `SKILL.md` with this exact shape. The
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

Validate the frontmatter and confirm every selected host path resolves to the
same readable `SKILL.md`. When a managed installer owns those links, run its
normal check. If the skill already existed at one source, edit that source if
the user requested changes and preserve its links.

Tell the user:

- the source and host paths, scope, and host coverage,
- its name (`<name>`), and
- that it composes with other explicitly activated skills, such as `macros:doubt`.

State whether each selected host discovers new skills immediately or requires
a new session or restart, when that behavior is known.
