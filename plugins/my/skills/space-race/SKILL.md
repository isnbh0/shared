---
name: space-race
description: Coordinate partially dependent work in parallel with integration checkpoints and independent review. Use only when explicitly requested.
disable-model-invocation: true
---

When the user invokes this macro for a multi-part effort, organize the work as a team whose members can advance partially dependent work at the same time. A member may be a person or an agent.

Identify the work nodes, their dependencies, and the assumptions that let downstream work begin before upstream work is settled. Start useful work in parallel by default. For code, give each work node its own branch and local worktree by default, including nodes in a dependency chain. Let downstream workers build against provisional assumptions and make those assumptions visible to the team.

Keep one lead accountable to the user for the overall goal, coordination, and integrated result. Workers check in as they reach useful checkpoints. Share upstream progress, bring settled changes into dependent work, and adjust implementations when assumptions change. The lead tracks the moving dependencies and resolves integration issues as the work converges.

Periodically, including before final integration, bring in a cold reviewer who has not participated in the implementation. Give them the original goal, current artifacts, and supporting evidence so they can independently look for drift, weak assumptions, gaps, and group reinforcement. The lead responds to findings with evidence or course corrections and brings consequential unresolved choices to the user.

Finish by integrating the work, checking the result against the user's goal, and reporting what remains uncertain. Choose team size, check-in rhythm, and review depth to fit the work.
