---
name: proofread-ko
description: Proofread Korean text through repeated, independent cold passes for editorial-ko, hemingway, and TMI, ending with a fresh-reader check. Use only when explicitly requested.
disable-model-invocation: true
---

Proofread the target Korean text until a reader with no context can read it once and understand it. One careful read of a style guide does not get there. Run independent passes, and check each pass against the previous version.

## Standards

Read these in full before the first pass. Give the same files to every pass.

- `../editorial-ko/references/editorial-ko.md`, the Korean editorial standard in this plugin
- `../hemingway/SKILL.md`: write plainly with concrete nouns and active verbs, and spell out compressed phrases
- the TMI rule below
- any genre or register rules the user gives (format, 개조식, ㅂ니다체, audience). These override the general standards.

If a standards file cannot be read, say so and do not claim the text was proofread.

**TMI.** Cut anything that only makes sense to someone who was there when the text was written:
- defensive justification of decisions
- arguments against alternatives the text does not present
- unsolicited hedges, caveats, and disclaimers
- backstory of incidents already resolved
- speculation
- restatement of what other parts already say
- internal ids, hashes, paths, and process detail the reader cannot use

Keep uncertainty that changes what the reader would conclude, and state it once.

## Passes

1. **Save the original** as version 0.
2. **Run each pass as a fresh agent, never a fork.** Each pass sees only the current
   version, the standards, and any source facts needed to check that the meaning is
   unchanged. It never sees the drafting conversation. Each pass:
   - fixes every issue it finds
   - writes the next version
   - lists what it changed
3. **Use at least three passes, one per lens, in this order:**
   1. editorial-ko in full
   2. hemingway
   3. TMI and audience relevance

   When the user asks for more passes, run more.
4. **Finish with a cold read.** A further fresh agent reads the latest version as the
   intended reader would. It lists every sentence it could not parse on first reading,
   every remaining pattern the standards forbid, and every compressed phrase it had to
   unpack. If it lists anything, run another fix pass and another cold read. Stop only
   when a cold read comes back clean.
5. **Check the result against version 0 and the source facts.** No pass may change a
   number, add a claim, strengthen certainty, or drop a needed qualification. Restore
   anything lost.
6. **Grep for the forbidden patterns** the standards name, then read each hit in
   context. A hit means rewrite the sentence for what it says. Do not substitute a
   fixed replacement: the same replacement repeated across the text becomes the next
   tic.

If the host cannot start fresh agents, run each pass as a separate full rereading that starts from the saved previous version. Tell the user that the passes were not independent.

## Output

Deliver the final text. Report the number of passes, what each pass changed in a line or two, and whether the last cold read was clean. When the user asks, keep the versions and the pass log next to the text.
