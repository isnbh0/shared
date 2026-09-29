# Editorial Standards for LLM-Assisted Writing

A style guide for content drafted or co-authored by large language models.

## Scope

**What this governs.** Expository and analytic English prose: articles, research notes, documentation, long-form argument, correspondence that carries an argument.

**What it does not.** Verse and lyrics, dialogue, quoted source material, code and comments, commit messages, structured reference text (tables, checklists, API docs), and anything whose register is deliberately performative. Section 3 catalogues symptoms of machine cadence in argumentative prose; in creative writing those same devices are the craft, and this file has no authority there.

**Language.** These rules are anchored to English syntax — trailing "not X" tags, subordinating connectives, em dashes, sentence length in words. Do not transliterate them onto Korean prose. The separate editorial-ko skill contains Korean standards; use it when explicitly requested.

## How to apply

These describe a target register, not a compliance surface. Section 3 names symptoms, not forbidden constructions: a device used once, deliberately, is not a violation, because the fault is the pattern as default cadence. This document uses several of the devices it warns about, which is the point.

When rules pull against each other, prefer what a reader who isn't looking for the rules would find better. Sections 1 and 2 govern; section 3 yields wherever a pattern is carrying meaning; format specifications yield to prose rules.

When reviewing existing prose, what you flag is a pattern. Four false-contrast pairs in a section is a finding; one is not. Where the author clearly chose a device, say so and leave it.

---

## 1. Voice and Tone

### 1.1 Objective Authority

Write as an informed analyst presenting evidence, not as a pundit delivering verdicts. The reader should trust the work because the reasoning is visible, not because the prose sounds confident.

### 1.2 Attribution of Value Judgments

Never assert a subjective ranking as objective fact. When a claim reflects someone's priorities, make the holder visible.

| Asserted as fact | Repaired |
|--------|-----------|
| They failed at the thing that matters more. | They failed at what the funding criteria weighted most heavily. |
| The real risk is choosing nothing. | *No one holds this yet — own it as your judgment or cut the sentence.* |

Three remedies, in order of preference. **Name the holder** when there is a real one. **Own it** when the judgment is yours: a piece framed as your analysis does not need to route every judgment through a third party, and "in my view" on every sentence is its own tic. **Cut it** when neither applies.

Never attach an attribution you cannot verify. An invented survey or an unnamed "experts say" is worse than the bare opinion it replaced, because it launders the opinion into evidence.

---

## 2. What Prose Should Be Doing

Most of this document describes what to avoid, which is a poor target on its own. Prose that breaks no rules is not thereby good, and a writer optimizing only against tells converges on something evenly paced, hedged, and forgettable. What to aim at instead:

**A paragraph carries one movement of the argument.** It should be possible to say what a given paragraph did. If the answer is "restated the previous one with different nouns," it goes.

**A sentence earns its place by adding an object, a number, a mechanism, or a consequence.** Sentences that only adjust the emotional temperature of the sentence before them are the first to cut.

**Concreteness beats generality at every scale.** The specific case, the actual figure, the named mechanism — these do the persuading. Abstraction is the fallback when you don't have them, and readers can tell.

**Rhythm should vary because the thinking varies**, not because a rule says to alternate lengths. A long sentence tracks a complicated relation; a short one lands something that is genuinely simple.

---

## 3. Machine Cadence

A recognizable tell of LLM-generated prose is staccato rhythm: short declarative sentences arranged in contrasting pairs or rapid-fire lists. Each pattern below is a legitimate move that becomes a tell through recurrence. One deliberate short closer in a piece is fine when the thought earned it; four are a habit.

**On the repair columns.** Each shows one way out, not the phrasing to reuse. Resyntaxing in place is often the weakest fix available — deleting the sentence, folding it into a neighbor, or reordering the paragraph so the contrast never needs stating are usually better. If "rather than," "whereas," and "without" start recurring in your output, you have acquired a new tell, and it is no improvement on the old one.

### 3.1 False-Contrast Pairs

The pattern: two short sentences where the first negates and the second asserts.

| Avoid | One repair |
|-------|-------------|
| This is not a theoretical argument. It is standard financial engineering. | Standard financial engineering covers this case, and nothing about it is novel. |
| The migration did not fail on throughput. It failed on schema drift. | The migration failed on schema drift, well before throughput became a concern. |
| It's not about speed. It's about survival. | Speed matters here only because the slower option doesn't survive contact with the market. |

**Fix**: Let the contrast land inside a sentence instead of across a full stop. Note that collapsing to "X, not Y" merely relocates the tell — see 3.6. The stronger move is usually to state what is true and let the negation drop out entirely.

### 3.2 Sentence-Fragment Lists

The pattern: three or more ultra-short declarative sentences in succession for rhythmic punch.

| Avoid | One repair |
|-------|-------------|
| Routers fail. Disks fail. TCP packets corrupt. | Routers fail, disks fail, and packets corrupt in transit. |
| The gap widens. The cost compounds. The window closes. | The gap widens as costs compound and the window closes. |

**Fix**: Join them — a comma series if they are genuinely a list, subordination if they form a causal chain. Where the run exists for rhythm rather than content, the real fix is often that two of the three items were never needed.

### 3.3 Dramatic One-Liner Closers

The pattern: a single punchy sentence ending a paragraph or section, designed as a mic-drop.

| Avoid | One repair |
|-------|-------------|
| Retention packages went out in March, but by then the damage was done. **Permanent resistance is a terminal diagnosis.** | Retention packages went out in March, by which point no compensation reverses damage that permanent resistance has already done. |
| Each customer can leave at any time. **The moat is zero.** | Each customer can leave at any time, so no individual account holds the company in place. |

**Fix**: Absorb the closer into the sentence before it. A thought important enough to keep is important enough to earn a clause with context, and a thought that works only as a standalone punch is usually not carrying the weight it appears to.

### 3.4 Parallel Structure Overuse

The pattern: back-to-back sentences with identical grammatical construction.

| Avoid | One repair |
|-------|-------------|
| Every dollar of cloud spend reduces EBITDA. Every dollar of GPU CapEx is invisible to EBITDA. | Cloud spend reduces EBITDA dollar for dollar, while GPU CapEx never touches the line at all. |
| They do not wait for the company to fail. They leave when they realize it will. | People leave as soon as they can see the failure coming, long before it arrives. |

**Fix**: Break the symmetry. Usually one of the two sentences is the real claim and the other is scaffolding, so promoting the real one and subordinating the rest beats balancing them.

### 3.5 The Dramatic Pivot

The pattern: a sentence existing solely to signal a reversal or hidden insight, often opening with "But here's the thing" or "The real question is," or headed "The X Nobody Talks About."

**Fix**: Cut the throat-clearing and state the point. Where the argument genuinely turns, mark the turn with content — name what changed — instead of with a suspense cue. Section headings should describe what a section contains, not tease it.

### 3.6 Compressed Negation Tags

The pattern: appending "not X" to the end of a clause as a punchy kicker.

| Avoid | One repair |
|-------|-------------|
| Export controls bought time, not advantage. | Export controls bought time; they did not produce an advantage. |
| The talent exodus is the leading indicator, not the lagging one. | Talent flight is what shows up first; competitive decline follows it. |

**Fix**: Expand the tag into its own clause, or drop it. The negated half is often already implied by the positive half and can go entirely.

---

## 4. General Prose Rules

### 4.1 Connected Phrases Over Sequential Declarations

A paragraph should flow through an argument, not stack assertions. Since you cannot literally read a draft aloud, use the mechanical equivalent: scan each paragraph's sentence lengths and sentence openings. A run of similar lengths starting the same way is the drumbeat.

### 4.2 Vary Sentence Length

Mix longer analytical sentences with shorter ones, and let the thinking set the variation; a quota produces its own monotony. A short sentence is never the problem; a run of them, all the same shape, is.

### 4.3 Earn Your Emphasis

Within prose, bold, italics, and short sentences all serve the same function. Use one at a time, sparingly. This does not govern document furniture — headings, table cells, and list labels take whatever emphasis the structure requires.

### 4.4 Lead with Evidence, Not Verdict

Within an analytical passage, present the observation or data before the interpretation, so the reader can reach a conclusion before you state yours. This operates inside a passage, not above it: documents and sections still open by saying what they are about, and documentation leads with the answer before the derivation.

### 4.5 Vague Quantifiers

A vague quantifier is a problem when it hides a number you have or could get, and correct when the imprecision is real.

Sharpen where you can — "roughly a third of the sample" beats "many." Where you cannot, keep the hedge and make the vagueness legible: "the filings don't break this out" is better than both a fabricated number and a bare "some." Never delete a qualifier you cannot replace with a fact, since that manufactures confidence the evidence does not support.

"Arguably" and "it is widely believed" are usually attribution problems rather than imprecision problems — see 1.2.

### 4.6 Cut Throat-Clearing

"It is worth noting that," "It is important to understand that," "The key takeaway here is." These carry no information and delay the substance. Unlike 4.5, this one has no exceptions worth preserving.

### 4.7 Avoid the Paradox Formula

"X did the opposite of what it intended" is a valid observation stated once. Repeating the ironic-reversal framing across several sections makes the piece feel like it has one rhetorical move.

---

## 5. Diagnostics

Prompts for a final read, not conditions to satisfy. Passing them is not evidence that the prose is good, and tripping one is not automatically a defect.

**Cadence.** Do negate-then-assert pairs, runs of very short sentences, or one repeated connector recur often enough to be audible as a pattern? Vary at the paragraph level if so; a single instance is not a finding.

**Connector variety.** If one device carries most of the joins in a passage — em dashes, semicolons, "while" — the fix is different sentence shapes, not different punctuation. Swapping em dashes for semicolons produces the same monotony in new clothes.

**Attribution.** Is every value judgment sourced, owned as yours, or cut? Is every attribution one you could actually verify?

**Closers.** Does any sentence exist only as a mic-drop?

**Hedges.** For each vague quantifier: do you have the number, or is the vagueness the true state of knowledge? Both are acceptable answers. Not having asked is not.

**Paragraph audit.** For each paragraph, can you say what it did? If the answer restates the paragraph before it, cut it.
