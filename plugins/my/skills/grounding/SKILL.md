---
name: grounding
description: Derive the laws a system resolves by and make invalid states unrepresentable. Use only when explicitly requested.
disable-model-invocation: true
---

Grounding is a direction rather than a procedure. It applies wherever a system's behavior is being decided — a spec, a schema, a protocol, a refactor, a design argument. It carries three concerns. Each stands on its own and each is available without the others; the user's request and the situation decide which carry weight.

## Laws, not rules

Systems accrete. Handled one "this should happen" at a time, behavior becomes a pile of local decisions that each made sense alone and collectively contradict each other. The alternative is to stop adding cases and instead work out the small set of laws the system actually resolves by — obvious, deterministic, total, stated before the cases rather than induced from them. Every input lands somewhere those laws already describe. Everything else is built against them.

The word is physics and it is meant literally. These are not rules the system is supposed to follow, and enforcement is the wrong frame entirely — no validator, no lint, no review checklist, no comment saying don't do that. A law holds when the contradicting state cannot be constructed: the type does not admit it, the schema has no slot for it, the protocol offers no message that expresses it, the only constructor establishes the invariant. If someone *could* write the violating state and something *catches* them, that is legislation and policing, and the law is not yet a law. Treat that gap as the finding, and close it by changing what is representable.

Laws are worth stating even where they are dull. Dullness is the goal — a law that needs explaining is usually still a rule in disguise.

## Maximal valid change

The antithesis of minimum viable change. Ask what the most ideal and proper shape of this is, and go there within the user's authorized scope, accepting whatever churn that implies: refactor, reclass, re-architect, migrate the data, rewrite the call sites, throw away work. Size of the diff is not evidence against a change. The question worth asking out loud: what would an engineer look at and say *well, in an ideal world this would have happened first, but alas* — and then do that thing first, now, instead of routing around it again.

Code that merely happens to comply with a law is not the same as code that cannot violate it, and the delta-patch that leaves the first standing is the expensive option. Name the maximal valid change explicitly even when it will not be taken; scoping it down is the user's call, and they cannot make it without seeing what was scoped away.

## Grounding the laws

Laws stated in prose are a claim, not a fact. Once there are several and they interact, intuition stops being reliable about two things: whether they are mutually consistent, and whether the states meant to be unreachable actually are. Where the interactions are load-bearing or non-obvious, ground the claim in something that can fail.

Formal modeling is the prominent default when laws are structural — a small model of the states and relations, with the invariants asserted and the bad states checked for reachability. Alloy fits this well when its distribution jar is available. Set `ALLOY_JAR` to that jar's path before running:

```
java -Djava.awt.headless=true -jar "$ALLOY_JAR" \
  exec -f -o <output-dir> -c '*' model.als
```

The `exec` subcommand is mandatory for this jar; invoking it bare launches the desktop GUI. Pass `-o` explicitly so generated files do not land in the working directory. `-f` overwrites an existing output directory, and `-c '*'` selects every command in the model. The output directory holds `receipt.json`, keyed by command name with `type`, `source`, `scopes`, and `solution`, plus a rendered `.md` per solution found. Stdout is one line per `run` or `check` command.

Read the verdicts carefully, because the polarity inverts between the two kinds. For a `run`, `SAT` means the scenario is constructible, which is what you want when demonstrating a law permits something. For a `check`, `SAT` means **a counterexample was found and the assertion is false**, while `UNSAT` means the assertion held. So the healthy result for a model of laws is every `check` UNSAT and every `run` SAT — that pair is worth asserting directly in a script. `UNSAT` is only ever evidence within the stated scope; a law that holds `for 3` is not thereby a law.

Offer Alloy when the laws are relational or state-machine shaped and worth the modeling cost; say so plainly when they are not. Verify that any `alloy` executable found on the system is the intended analyzer before using it.

Formal modeling is one case of the general concern, not the whole of it. Property-based tests, exhaustive enumeration over a bounded space, a type-level encoding that fails to compile when violated, a decision table checked for totality and overlap, or a deliberate attempt to construct the forbidden state and observe it being impossible — any of these grounds a law. Pick the cheapest one that could actually falsify the claim. A check that cannot fail has grounded nothing.
