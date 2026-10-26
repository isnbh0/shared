<!-- Generated from isnbh0/my-sandbox:projects/principles/clean.md
Source revision: 00f6875bce86c4ab044e443b81ab1116f875302d
-->

# Principles for building projects

Build what the present work calls for. Give the rules that matter a clear home. Make the result usable, testable, and easy to change.

- 1 Begin with a real need, and let the project grow from what the work reveals.
  - 1.1 Build one complete path before a general system.
    - 1.1.1 Start with the person, task, and stage in front of you. Give an existing product the structure its users need; give a new idea only enough structure to learn from it.
    - 1.1.4 Ask when purpose or policy is undecided. Once it is decided, carry the ordinary implementation choices forward.
    - 1.1.5 A small first step may leave a known repair. Name it where the next worker will see it. When the defect and its cause are already clear, make the full repair.
  - 1.2 Make recurring work easy to run and understand.
    - 1.2.1 Give repeated work a named command. Building, checking, and releasing should not depend on remembering a private sequence of steps.
    - 1.2.2 A command should do the preparation and checks its result needs. Its name and output should make its promise clear.
    - 1.2.3 Let each document do its own job: introduce the product, guide contributors, or define a contract close to the thing it governs.
    - 1.2.4 Use project tools to change generated files. Keep durable work, user data, and temporary work in places suited to their owners; commit completed work and clear away its debris.
  - 1.3 Keep the project's rules findable and true.
    - 1.3.1 A new person or agent should be able to follow the project entry point to the guidance needed for the task.
    - 1.3.2 When behavior changes, change the guides and contracts that describe it in the same piece of work.

- 2 Give data, behavior, and constraints clear owners.
  - 2.1 Let the project speak in its own model.
    - 2.1.1 Translate outside data at the boundary. The core should describe the project's work in terms it owns.
    - 2.1.3 Keep core decisions checkable without starting every external service. Make the contract at each boundary explicit.
    - 2.1.4 Preserve compatibility for people and data that exist. Choose migration, fallback, or a clean cutover from the actual state of the product.
  - 2.2 Put each lasting rule where the system can uphold it.
    - 2.2.1 Express an invariant in the type, schema, protocol, or component that owns it. Prefer a valid state by construction to a warning after the damage is done.
    - 2.2.2 When several symptoms share a cause, repair their common source.
    - 2.2.3 A sound repair reaches every model, caller, datum, and test that depends on the broken shape.
    - 2.2.4 Test interacting rules with a check that could reveal a counterexample. State the bounds of what the check established.
  - 2.3 Expand what people can do through features they can combine.
    - 2.3.1 Count the tasks a person can finish, not merely the controls the product contains.
    - 2.3.2 Give each feature a distinct purpose. Let useful combinations carry more work than any single feature alone.
    - 2.3.3 Watch how people work. Add a new feature when the existing ones cannot serve a real workflow well enough to justify another choice to learn.

- 3 Make design rules serve the person using the product.
  - 3.1 Compose shared rules deliberately.
    - 3.1.1 Layout, type, color, theme, and state cross component boundaries. Give each rule an owner and make its interactions predictable.
    - 3.1.4 Put repeated alignment and spacing in shared structure. When people compare views, keep the frame stable and emphasize what changed.
    - 3.1.5 Express the intent of a design so it survives different screens, writing modes, and content lengths.
  - 3.2 Make meaning and access part of the interface.
    - 3.2.1 Use elements that already express the right meaning and behavior.
    - 3.2.2 Check the real path through the interface: keyboard use, focus, labels, contrast, and feedback.
    - 3.2.3 What a control says, shows, and saves must describe the same state.
    - 3.2.4 Every visual distinction should help someone read, compare, decide, or act.
  - 3.3 Give complex tasks a guided path.
    - 3.3.1 When a task needs local context and several decisions, a person can use their own agent to do it. Make that path visible and optional.
    - 3.3.2 Prepare instructions with the real context and show what will be passed along.
    - 3.3.3 Give the agent a contract for the result and a way to check it.
    - 3.3.4 Design the path around the task a person wants to finish, not around a menu of every possible setting.

- 4 Keep conclusions honest and the next change affordable.
  - 4.1 Make a local change quick to verify.
    - 4.1.1 Check what the change can affect. If every small change needs the whole system to run, create a boundary that can be checked on its own.
    - 4.1.2 Check a user-facing claim through the closest available product path, with realistic inputs and neighboring interactions.
    - 4.1.3 Say exactly what each check established. A skipped check and an experiment that missed its target establish nothing about that target.
  - 4.2 Invite an independent reading of the work.
    - 4.2.1 Give the reviewer the goal, artifact, constraints, and original question before giving them your answer.
    - 4.2.2 Ask for a concrete failure, missing case, or competing interpretation.
    - 4.2.3 Agreement from someone who has already seen your answer is useful feedback; seek a fresh reading when independence matters.
  - 4.3 Revisit complexity when it begins to slow the work.
    - 4.3.1 Look for duplicate paths, speculative layers, ceremony, and partial repairs after substantial change.
    - 4.3.2 Remove accidental complexity while keeping boundaries, tests, and promises that serve a real purpose.
    - 4.3.3 End a review with an owned change or a clear next action. Keep the written account current and state what remains uncertain.
