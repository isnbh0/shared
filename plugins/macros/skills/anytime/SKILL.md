---
name: anytime
description: Explicit-request macro. Activate only when the user directly requests this macro; never infer activation from task characteristics. Skill — Run bulk work so partial results are usable at any moment and more time yields more results, with the stop condition set in conversation
---

Honor every skill explicitly activated in the user's request exactly once. If another activated skill is not yet loaded and the host provides a skill-loading mechanism, load it through that mechanism. Do not reload an active skill.

Run the work so it can stop at any moment and still leave a valid result, and so that result grows the longer it runs.

Whenever the run is stopped or checked:

- **Usable now.** What the user asked for exists in usable form from the first finished item onward: the finished files if they asked for files, the report so far if they asked for a report. No final step stands between the work and its value.
- **Nothing finished is lost.** Finished work survives whatever ends the run, and a later run can pick up without redoing it.
- **Honest count.** "How many so far?" has a true answer that is cheap to get. Only fully finished items count, all held to the same quality bar, and failed or skipped items are reported alongside them.

The conversation decides everything else, including what ends the run ("stop at 1000", "stop at 6:30am", "until the quota runs out"), where the work comes from, where it runs, and how much runs at once. Apart from the stop condition, choose what fits the job where the user has not said.

If no stop condition has been given, ask for one while starting on a bounded default that fits the job, such as the end of a finite list. Hold off starting only if even that default would spend something consequential. Make sure the run can actually reach the stop, or say up front that it can't: an in-session run won't reach 6:30am if the session closes first.

When some work is clearly worth more and nothing else sets the order, do it first, so that stopping early leaves the best of it done.
