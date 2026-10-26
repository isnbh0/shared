---
name: complexity-panel
description: >-
  Review a codebase's accidental complexity through independent design lenses,
  verify consequential findings, and propose cleanup priorities.
  Use only when explicitly requested.
disable-model-invocation: true
---

Honor every skill explicitly activated in the user's request exactly once. If another activated skill is not yet loaded and the host provides a skill-loading mechanism, load it through that mechanism. Do not reload an active skill.

You lead a panel review of accidental complexity: brief the reviewers, check what they claim, and synthesize. Nobody changes code or state during the run. The user wants an honest lay of the land, not reassurance.

## 1. Intake

Read defaults from config, merged per key. `.agents/skill-configs/complexity-panel/config.local.yaml` in the project overrides `.agents/skill-configs/complexity-panel/config.yaml`, which overrides `~/.agents/skill-configs/complexity-panel/config.local.yaml`, which overrides `~/.agents/skill-configs/complexity-panel/config.yaml`. Explicit user instructions take precedence over config. See `config.example.yaml` next to this file. With no config, use the lenses in section 3.

Resolve these from the request and the repository, asking only what you cannot resolve:

- **Target:** the repository or paths to review; by default the current repository.
- **Lenses:** the configured set, adjusted by the user. A lens named after a person gets a paragraph in that person's terms.
- **Principles:** Use any stated design or maintenance principles. Skip this lens if none are available.
- **Since:** an optional commit or tag; reviewers then weigh what changed since it.

Tell the user the panel you are launching, then launch.

## 2. Orientation

Read enough to brief strangers: the agent instructions and docs index, the entry points or composition root, and the top-level layout. Write a short project description (what it is, who uses it, its main moving parts) and a list of pointers to docs, entry points, main directories and tests. Leave out your own suspicions: reviewers must arrive cold, not primed to confirm a hypothesis.

Note any project rule about what subagents may run, such as read-only command limits or forbidden command strings. It goes verbatim into every reviewer prompt.

## 3. The panel

Launch the reviewers in parallel as fresh agents with no shared context, one lens each, on the configured model if one is set. The default panel:

1. **Owner's principles.** Read the principles and agent instructions in full first. Judge where the code honors them, where it drifts, and where the rules themselves cause complexity.
2. **Ousterhout** (*A Philosophy of Software Design*). Complexity is dependencies plus obscurity, showing up as change amplification, cognitive load and unknown unknowns. Look for deep vs shallow modules; information leakage, temporal decomposition and pass-through methods; special cases that could be defined out of existence; configuration pushed upward. Gauge change amplification by tracing what recent features had to touch.
3. **Hickey** ("Simple Made Easy", "The Value of Values"). Find what is complected: state and identity, time and order, policy and mechanism, data and behavior, who is asking and what is done. Look at mutable state, implicit ordering, rich objects vs plain values, and whether decisions are pure functions of facts.
4. **Parnas and Brooks** (information hiding, designing for change; essential vs accidental complexity, conceptual integrity). What decision does each module hide, and is it likely to change? Do the boundaries hide the right secrets, or are they ceremony? Is there one coherent model of the core concepts, or several overlapping ones? How many modules would a few plausible next changes touch?
5. **Beck, Fowler and Metz.** The four rules of simple design and YAGNI; Fowler's code smells by name; "duplication is far cheaper than the wrong abstraction". For each smell, act now or wait? Read the tests as design feedback: do they test behavior through stable seams, or pin implementation?
6. **Nygard and the Unix tradition** (*Release It!*). Examine runtime, deployment and recovery complexity wherever it lives. Are responsibilities and interfaces clear? Does composition simplify the system or add coordination costs? Are failure modes (restart, crash mid-operation, full disk, out of memory, dependency outages) handled by design or by scattered special cases? Is state on disk easy to back up and restore? Are the checks proportionate? Skip this lens when there is no operational surface.
7. **Metrics analyst.** Quantitative evidence, interpreted in context: size per area and the largest files, test-to-source ratio, growth across evenly spaced points in history with the features that landed between them, churn hot spots, imports in and out of the largest files, and files and lines touched per recent feature by area. End with a few observations drawn from the data.

Each reviewer prompt contains:

- **Framing:** a cold, independent review of this codebase's accidental complexity; the project description; and that the owner wants an honest lay of the land, not reassurance.
- **The lens,** in its authors' own terms.
- **Orientation:** the pointers from section 2.
- **Rules:** read-only. Use only file reads, searches, and read-only shell such as `cat`, `sed -n`, `grep`, `ls`, `wc` and `git log/show/diff`. Never modify, create or delete files. Do not run tests, builds, package managers, network or remote commands, or the repository's scripts, and never execute fragments of scripts you read. Add the project's subagent rules from section 2, verbatim.
- **Return,** within the configured word cap (about 700 by default) and without preamble: a short verdict in the lens's terms; findings, most important first, each with `path:line`, the problem in the lens's vocabulary, severity (structural, local or cosmetic), and essential vs accidental; what is genuinely well done; and the top simplifications with their expected payoff. Be evidence-based, and write "not checked" rather than guess. Adapt the shape where a lens calls for it, such as a module/secret table for Parnas and Brooks or tables for the metrics.

## 4. Check before you synthesize

Verify against the code yourself every finding you will rank near the top, every claim of a bug, data loss, security or permission gap or missing safeguard, and every factual conflict between reviewers. Mark each as **verified**, **refuted** (with the evidence) or **unverified**.

## 5. Synthesis

Report to the user:

1. **Verdict.** Answer the question asked ("is it spaghetti?") briefly, on the grounds of where the panel agrees it is sound and where complexity concentrates and whether it is growing, per the metrics.
2. **Hotspots.** A table of hotspot, what's wrong (with `path:line`), and how many reviewers raised it. Prioritize verified impact and expected simplification payoff; treat agreement as supporting context, since lenses can overlap.
3. **Disagreements.** Where lenses conflict, such as act now vs wait: each side and who holds it, then your recommendation, noting where the owner's stated rules settle it.
4. **More than tidiness.** Correctness, data-loss, security and operational-safety findings, each with its verification status.
5. **Corrections.** Reviewer claims that proved wrong.
6. **Ranked cleanup proposal.** Each item with its payoff, whether it is mechanical or a restructuring, its rough size in hours, and what it depends on. Name what you would leave alone and why.

Change no code. End by asking which items to turn into work.
