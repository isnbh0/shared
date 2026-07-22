---
name: clone
description: Copies a skill or plugin into a local project for adaptation without installing it. Use when the user wants to clone, fork, or locally customize a skill or plugin from an identifier, path, or GitHub URL.
---

# Clone a Skill or Plugin

Copy a skill or plugin into a user-controlled project directory. Do not install,
activate, register, or modify the source.

## Resolve the source

Accept a local identifier or path, or a GitHub URL. Inspect the source enough to
identify the available skill or plugin directories. If it contains more than one
plausible thing to copy, show the choices and ask the user which one they want.
If an identifier cannot be resolved in the current runtime, say so and ask for a
source the runtime can resolve.

## Confirm the copy

Preserve the complete selected directory, including supporting files. Propose a
project-local destination that fits the current project's layout, then ask the
user to confirm it. If the destination exists, do not overwrite it; ask the
user to choose another name or location.

## Copy and report

Copy only after confirmation. Verify that the copied skill contains `SKILL.md`
or that the copied plugin contains its skill directories. Report the source and
local destination. The result remains an ordinary local copy for the user to
adapt.
