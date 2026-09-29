---
name: tightloop
description: Keep checks proportional to the reach of a change. Use only when explicitly requested.
disable-model-invocation: true
---

Tight loops are a direction rather than a procedure.

A feedback loop should cost about as much as the change it checks. The measure is how far the change can reach, not how many lines it touches. A one-line edit to a shared type can reach far. A large rewrite inside one module may not.

Running every check after every edit does not make the work more careful. A check the change cannot affect tells you nothing new. Each run still takes time, and over many edits that time adds up to hours of waiting.

A good check covers what the change can reach, and it fails if the change is wrong. Often that is one test, a typecheck, an assertion, or a short script that runs the one path in question.

A change can affect code that depends on it. Clear boundaries, and units that can be tested at those boundaries, let you check a local change locally and trust the result. If the only honest way to check a small change is to run everything, the code around it has no boundary where it can be checked alone. Point that out instead of running everything each time.
