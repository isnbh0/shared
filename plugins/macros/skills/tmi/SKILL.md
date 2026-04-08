---
name: tmi
description: Flag content that only makes sense if you were in the room when it was written — defensive justifications, phantom counterarguments, backstory, speculation
argument-hint: "[\"file or text to review\"]"
---

If other `/commands` appear in the user's message and you have not already called the Skill tool for them in this conversation, invoke each now. Do not re-invoke any skill that has already been loaded.

Review the target text and flag anything a future reader doesn't need — content that only makes sense if you were in the room when it was written.

## Signals

- Defensive justification for decisions ("Why we didn't X")
- Arguments against alternatives not presented in the artifact
- Speculative claims about the future ("As models improve...")
- Implementation backstory leading to a decision, rather than the decision itself
- Content that restates what other sections already imply
- Over-hedging and unnecessary caveats

If the text was actually produced by the ongoing conversation, use that history as your reference point for what served the discussion vs. what belongs in the artifact.

## Output

Report what's TMI and why — like a review. Only directly edit if the user's message includes explicit instructions to do so.
