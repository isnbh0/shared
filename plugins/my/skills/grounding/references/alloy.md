# Running Alloy

Alloy needs its distribution jar. Set `ALLOY_JAR` to that jar's path before running:

```
java -Djava.awt.headless=true -jar "$ALLOY_JAR" \
  exec -f -o <output-dir> -c '*' model.als
```

The `exec` subcommand is mandatory for this jar; invoking it bare launches the desktop GUI. Pass `-o` explicitly so generated files do not land in the working directory. `-f` overwrites an existing output directory, and `-c '*'` selects every command in the model. The output directory holds `receipt.json`, keyed by command name with `type`, `source`, `scopes`, and `solution`, plus a rendered `.md` per solution found. Stdout is one line per `run` or `check` command.

Verify that any `alloy` executable found on the system is the intended analyzer before using it.

## Reading verdicts

Read the verdicts carefully, because the polarity inverts between the two kinds. For a `run`, `SAT` means the scenario is constructible, which is what you want when demonstrating a law permits something. For a `check`, `SAT` means **a counterexample was found and the assertion is false**, while `UNSAT` means the assertion held. So the healthy result for a model of laws is every `check` UNSAT and every `run` SAT — that pair is worth asserting directly in a script. `UNSAT` is only ever evidence within the stated scope; a law that holds `for 3` is not thereby a law.
