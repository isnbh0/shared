# Running Alloy

Alloy needs Java and its distribution jar. These notes were checked against Alloy 6.2.0. Set `ALLOY_JAR` to the jar's path. If no jar is available, say so and use another check instead of installing anything. Use the jar rather than an `alloy` executable on the PATH, which may be a different program.

```
java -Djava.awt.headless=true -jar "$ALLOY_JAR" \
  exec -f -o <scratch-dir> -c '*' model.als
```

The `exec` subcommand is mandatory for this jar; invoking it bare launches the desktop GUI. `-f` overwrites the output directory, so point `-o` at a dedicated scratch directory. `-c '*'` selects every command in the model.

The output directory holds `receipt.json` and a rendered `.md` per solution found. In `receipt.json`, `commands` is keyed by command name. Each entry has `type` and `source`, and has `solution` only when the verdict is `SAT`. Stdout has one line per `run` or `check` command, ending in the verdict. The exit code is 0 even when a check finds a counterexample, so read the verdicts rather than the exit code.

## Reading verdicts

The polarity inverts between the two kinds of command. For a `run`, `SAT` means the scenario is constructible. For a `check`, `SAT` means **a counterexample was found and the assertion is false**, while `UNSAT` means the assertion held.

Decide the expected verdict for each command before running it:

| Command | Healthy verdict |
| --- | --- |
| `run` of a permitted scenario | `SAT` |
| `run` of a forbidden scenario | `UNSAT` |
| `check` of an assertion | `UNSAT` |

These expectations are worth asserting in a script. Compare the whole verdict, because `SAT` is a substring of `UNSAT`.

`UNSAT` is only ever evidence within the stated scope; a law that holds `for 3` is not thereby a law.

## Avoiding checks that cannot fail

- A law written as a `fact` and asserted again is `UNSAT` by construction. Check consequences and interactions between laws, not the laws restated.
- Contradictory facts make every check pass. Pair each check with a `run` that reaches the check's precondition.
- Weaken or remove a law and confirm that the check turns `SAT`.
