---
name: new
description: Scaffold a custom macro — an ordinary SKILL.md that behaves as a first-class member of the macros ecosystem. Writes to project scope (this repo) or user scope (all your projects) and pre-fills the composition line so the new macro chains with /doubt, /consensus, /seq, and the rest.
---

If other `/commands` appear in the user's message and you have not already called the Skill tool for them in this conversation, invoke each now. Do not re-invoke any skill that has already been loaded.

You are scaffolding a new custom macro for the user. A macro is not a special
object — it is a plain Claude Code skill (`SKILL.md`) that carries the macros
**composition line**, which is what lets it participate in chained invocations
like `/mymacro /doubt 3`. Your job is to gather the macro's name, description,
and behavior, then write a correct skill file to the right scope.

## 1. Resolve scope

Decide where the macro lives from what the user already said — do not ask if
it is clear:

- **User scope** → `~/.claude/skills/<name>/SKILL.md`. The macro is available
  in every project. Choose this when the user says things like "for all my
  projects", "everywhere", "globally", or is describing a personal working
  habit.
- **Project scope** → `.claude/skills/<name>/SKILL.md` (relative to the repo
  root). Committed, shared with the team. Choose this when the user says "in
  this repo", "for the team", "commit it", or the behavior is repo-specific.

If genuinely ambiguous, ask once. Otherwise proceed with the inferred scope
and state which you picked.

## 2. Pick a non-colliding name

The name is a kebab-case slug; the macro is invoked as `/<name>`.

**Default: prefix user-scope macros with `my-`.** So a user macro for avoiding
time estimates becomes `my-timeless`, invoked `/my-timeless`. This guarantees
they never collide with bundled or native skill names. The user can pick a
different prefix (`u-`, their initials, whatever) — honor it and keep it
consistent across every macro you scaffold for them. Project-scope macros are
unprefixed unless the user asks otherwise.

Before committing to a name, list existing skills so `/<name>` is unambiguous:

```
ls ~/.claude/skills .claude/skills 2>/dev/null
```

Also avoid the bundled macro names (mapreduce, doubt, consensus, seq, rigor,
askme, delegate, timeless, chunked, orchestrate, dry-run, dredge, timestamp,
tmi, new). If the desired name collides, propose a distinct one and say why.

## 3. Gather name, description, body

- **name** — from the user, or suggest one from their description.
- **description** — one line. This is what the agent sees in the skill list
  and uses to decide relevance, so make it say when to reach for the macro,
  not just what it does.
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
description: <one-line description>
---

If other `/commands` appear in the user's message and you have not already called the Skill tool for them in this conversation, invoke each now. Do not re-invoke any skill that has already been loaded.

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
- how to invoke it (`/<name>`), and
- that it composes — e.g. `/<name> /doubt` runs both.

New skills are picked up on the next session; note that if they try `/<name>`
immediately and it is not found yet.
