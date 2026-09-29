---
name: grounding
description: Derive the laws a system resolves by and make invalid states unrepresentable. Use only when explicitly requested.
disable-model-invocation: true
---

Grounding is a direction rather than a procedure. It applies wherever a system's behavior is being decided — a spec, a schema, a protocol, a refactor, a design argument. It carries three concerns. Each stands on its own and each is available without the others; the user's request and the situation decide which carry weight.

## Laws, not rules

Derive a small set of deterministic, total laws before adding cases. Every input must have a defined outcome under those laws.

A law holds when a contradictory state cannot be constructed: the type does not admit it, the schema has no slot for it, the protocol offers no message that expresses it, or the only constructor establishes the invariant. A validator, lint rule, or review that catches a violation does not make it unrepresentable. Close that gap by changing what the system can express.

State the laws plainly, including the obvious ones.

## Maximal valid change

Identify the ideal change within the user's authorized scope, even if it requires a refactor, migration, or rewritten call sites. Do not use diff size alone to reject it.

Name the maximal valid change even when it will not be taken, so the user can decide whether to narrow the scope.

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
