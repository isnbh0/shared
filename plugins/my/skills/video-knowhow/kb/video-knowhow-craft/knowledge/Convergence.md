# Convergence in revision

A revision process converges when its rounds stop finding new defects and its repairs stop creating them. This page records how SLASH_MY, the production John endorses, went through eleven rounds of whole-film review. A weekly usage limit on the agent service ended the record during round eleven. That round never reached a whole-film snapshot, and the record holds no sign-off. The code shelf covers what a round runs on: snapshot assembly, resumable renders, and judged output that can be reproduced ([iteration and parameterization](../../video-knowhow-code/knowledge/Iteration%20and%20parameterization.md), [deterministic rendering](../../video-knowhow-code/knowledge/Deterministic%20rendering.md), [verification](../../video-knowhow-code/knowledge/Verification.md)). This page covers the judgment: what a round may reopen, what stays frozen, and when the rounds stop.

The evidence is recorded revision. Each claim below gives a before, an after, and the reason recorded for the change, read from the production's session records and commit log, which are held in John's workspace. That record of working practice from one endorsed production is better evidence than this shelf's interpretations, but it comes from a single film, and the general lessons are what the shelf took from it.

## Review in rounds, on the whole film

Each round reviewed all of SLASH_MY from scratch, through the same set of lenses every time: typography, motion, color and material, writing, sound, seams, and accessibility. Ten or eleven reviewers ran in parallel, and the round sent each fix to an owner working in a separate copy. A round ended in a named snapshot, and the next round reviewed that snapshot. When only the sound had changed, the round paired the unchanged picture with the new mix, so the audio judgment was made against picture that had not moved. Each round used new reviewers so that every verdict described the snapshot in front of them. Comparing snapshots across rounds was left to a separate meta-review.

## The meta-review separates closed from circling

After several rounds, one review read the earlier reviews. It compared successive snapshots and sorted every finding still on the table into two lists. **Closed defects** stay closed unless new evidence reopens them; examples are the peak moved back onto its beat, strikes no longer buried, and one-frame flash pairs brought to zero. **Oscillating taste** lists the judgments that reversed between rounds with no new evidence. On this production it held echo carry, the reveal's top end, wall styling, the level of the writing section's whoosh, and paper and grain. The same meta-review named the regressions a repair had caused elsewhere, such as a peak that moved or a surface defect that grew, and those went back into the next round as defects. Its recorded verdict: the film was mostly converging, one narrow round was recommended, and then a freeze.

## Freeze taste, record declines, answer evidence

The oscillating list was frozen. Its items stopped taking review time, and when a round proposed one again, the round declined it and wrote it onto a **declined list** with the idea and the reason. A freeze is a decision about evidence, and the production recorded it answering evidence in both directions. A frozen item came back when inspection showed a real defect: the reveal's strikes, first set aside as taste, returned once measurement showed each stroke was visible for only a few frames, and one coordinated repair served them all. A proposal with no new evidence was declined: one round suggested a progress-bar echo at the throw beats, and the recorded reason for declining it was that the brief freezes picture echoes at the throws, because earlier rounds had swung them back and forth. The declined list records what was rejected and why. Without it, a declined idea comes back in new wording and costs another round.

## Stop on a locality rule

The production's recorded stop rule, stated in round seven: "The film is done when a full review finds no new defect, and no fix creates a seam problem within two beats of where it was made." The first clause asks for a full review because a spot check does not find new defects. The second clause has each fix inspected in its neighborhood because, in SLASH_MY, repairs did cause problems nearby: one round's fix to the reveal left new labels piling onto their neighbors on the wall ten frames away, and a later level repair weakened the slam next to it, the impact sound that ends a slot. Two beats is the recorded window in which a repair has to be judged again before the round can close.

Round eight did not meet the rule, so round nine ran, and the rounds continued to eleven. The record does not show the rule met. During round eleven a weekly usage limit on the agent service ended the round structure. The last recorded film commit, `fd543f2a`, is an audio snapshot. John's verdict on the whole film dates from 2026-10-02, during round seven, the day of the picture snapshot `32dec413` ([what it covers](../cases/SLASH_MY.md#what-this-case-is)).

## Run it

These are the steps as SLASH_MY ran them; adapt the shape to the piece:

1. Review the whole piece each round through the same lenses, and send out each fix with an owner and a scope.
2. Take a snapshot each round. When one craft changes, review it against neighbors that did not change.
3. Every few rounds, run a meta-review that lists closed defects, oscillating taste, and regressions.
4. Freeze the oscillating list, record each decline with its reason, and re-admit an item when evidence demonstrates a defect.
5. Stop when a full review finds no new defect and no fix disturbs the two beats around it.

Questions about how the tooling works, such as snapshot assembly, resumable chunks, a resume that reproduces the same bytes, and review tools that check themselves, belong on the code shelf's [iteration](../../video-knowhow-code/knowledge/Iteration%20and%20parameterization.md) and [verification](../../video-knowhow-code/knowledge/Verification.md) pages.

## Inspect

- Is a returning finding new evidence, or an old judgment in new wording? Check the declined list.
- Does each closed item name the check that closed it?
- Has anyone looked at the two beats around each fix since the fix went in?
- What would reopen this freeze? A defect that evidence has demonstrated, named in the record.

[Direction and critique](Direction%20and%20critique.md) · [Defect to repair](../patterns/Defect%20to%20repair.md) · [Home](../Home.md)
