---
name: debrief-manifesto
description: Report work from the reader's viewpoint, with a fixed opening and labeled claims. Use only when explicitly requested.
disable-model-invocation: true
---

Debrief-manifesto is a posture, and it holds whether you adopt it before the work or apply it to a report you have already given. What follows is what the reader must come away holding. The opening is fixed; past the opening, the arrangement that serves them is decided each time.

## Who is reading

The reader commissioned the work and decides what happens next. They carry whatever it sets in motion and they live with whatever was left undone. Their question is the state of their system, so a report ordered by the sequence you worked in and weighted by what was interesting to solve leaves them to do the translation themselves.

Include implementation where their next move depends on it, and otherwise let it sit behind the claim as a handle they can pull.

## The opening

Distrust your sense of what should lead: at the end of a session, the item that feels significant is the one you touched last. So the first lines are fixed.

1. **Where the request stands.** One line, naming the request as you understood it and its state: done, done by a different route, partly done, blocked, abandoned. State the understanding; do not leave it implied.
2. **What you need from them, and what you would do.** Give the options, name the one you would take and why, and say what you will default to if no answer comes.
3. **What cannot be undone**, where it reaches past this machine or past what was authorized: data migrated, files deleted, commits pushed, messages sent, credentials written. Each carries what reversal would cost, or a statement that there is none.

Where the request failed and a decision now hangs on it, those go in one sentence, since the decision is unintelligible without the premise that broke.

## What else the reader must come away holding

- **What moved**, and in which part of their system. The region carries the claim and the concrete handle rides with it — path, symbol, command, commit — because their usual next act is to go look.
- **The means to check you.** Name the one thing they could run to falsify your main claim, and what it should show: the command that reproduces the result, the commit that carries it.
- **What you settled on their behalf.** The choices they would plausibly have made differently: anything touching scope, cost, reversibility, or a preference they had already stated.
- **How the stakes changed**, in every direction that applies: situations that can no longer occur, situations that will occur if nothing further happens, and the conditional ones — if this signal appears, it is that cause and not the other.
- **What they should not yet build on.** The most likely way this work is wrong, paired with the cheapest check that would settle it. Add a claim resting on inference or a path left unexercised only where the reader would otherwise act on it as settled.

Promote to the top level only what changes what the reader does. Where that is one item, the report is one line. Where there is more than fits a scan, push detail down a level under claims that hold on their own, and refuse the grouping that would bury the item they would have acted on.

## Consequences, where they are real

A change is worth more to the reader as the situation it creates or removes than as the edit that produced it. "The retry loop backs off exponentially" describes your work; "a downstream outage no longer leaves you draining the job queue by hand" describes what they gained.

Only assert a consequence you have grounds for. Where you infer an effect without having observed it, either state the change and stop, or mark the inference as one. Housekeeping with nothing attached to it — a lint fix, a version bump — gets reported as housekeeping.

## Detail that earns its place

A number belongs when it changes what the reader does with it, and that test cuts both ways. "Forty-three errors fixed" during a refactor is texture from your side of the work. "Forty-seven of the fifty-one type errors are gone; the remaining four wait on a decision about collation" is the completion state and the blocker in one line. Give load-bearing figures in the units the decision gets made in, and leave out the ones that only show effort.

## Written in expectation of follow-up

The reader's next act is to open one of these items, so the report does not have to stand alone. Drop justification of a choice nobody questioned, reasoning laid out against anticipated doubt, and background supplied for self-sufficiency. What survives are claims you could expand on the spot with specifics, so that what reads short is compressed and never vague.

Compress an explanation freely. Keep every item, since the reader cannot ask about something they have not been told exists.

## Labels

Give every claim and item a label printed with it — (1), (2), (3) — flat across the report, in the order they appear. Numbering restarts at (1) in every report.

Labels replace deixis. Write (3) wherever you would have written "this fix" or "that one", the closing question included, so the reader never has to scroll back to resolve a pronoun. They are also the reader's address for a follow-up: "expand (4)" costs them less than quoting your own text back at you.

Label what can be reached into — a claim, a decision, an item waiting on them. Leave headings and the report's own furniture unlabeled.

## The closing question

End with one question on its own line, bolded, ending in a question mark. It is the last thing in the report and there is always one.

Make it the question whose answer most changes what happens next. Where you need a decision, this is that decision put directly, not a second question set beside it. Where you need nothing, it is the most likely place they would reach in: the next step you would take, or the item worth opening first.

One question, answerable as asked. "Let me know if you have any questions" is not one.

## Register

Plain documentary prose, the register of good technical writing about what a system does. Where the user's editorial standards are available as their own skill, they govern.
