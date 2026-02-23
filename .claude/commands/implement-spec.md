---
description: Implement a specification using the spec-workflow skill
---

You are implementing a technical specification using the spec-workflow skill in IMPLEMENTATION phase.

## Step 1: Determine Spec File

Check if the user provided a spec file mention (e.g., `@agent-workspace/specs/some-spec.md`):

- **If a spec file was mentioned**: Use that file path directly
- **If no spec file was mentioned**: Find the latest non-future spec from `agent-workspace/specs/` directory using this Python command:

```bash
python3 -c "
import os
import re
from datetime import datetime

specs_dir = 'agent-workspace/specs'
now = datetime.now()
pattern = re.compile(r'^(\d{6})-(\d{6})-.*\.md$')

valid_specs = []
for filename in os.listdir(specs_dir):
    match = pattern.match(filename)
    if match:
        date_part, time_part = match.groups()
        year = int('20' + date_part[0:2])
        month = int(date_part[2:4])
        day = int(date_part[4:6])
        hour = int(time_part[0:2])
        minute = int(time_part[2:4])
        second = int(time_part[4:6])
        try:
            spec_dt = datetime(year, month, day, hour, minute, second)
            if spec_dt <= now:
                valid_specs.append((spec_dt, filename))
        except ValueError:
            continue

if valid_specs:
    latest = sorted(valid_specs, key=lambda x: x[0], reverse=True)[0]
    print(latest[1])
"
```

This command will output the filename of the latest spec with a timestamp not exceeding the current time. Construct the full path as `agent-workspace/specs/{filename}`.

## Step 2: Invoke Spec Workflow

Once you have identified the spec file path:

1. Tell the user which spec you're implementing: "I'll implement the specification from `{spec_file_path}`"
2. Use the Skill tool to invoke the spec-workflow: `skill: "spec-workflow"`
3. The skill will expand and provide instructions - follow them to complete the IMPLEMENTATION phase
4. Provide the spec file path when the skill prompts for it

## Important Notes

- The spec-workflow skill handles the entire implementation process
- It will read the spec, implement changes, update spec status, and commit all changes
- You should let the skill orchestrate the work - just provide it with the correct spec file path
- Do not attempt to implement the spec yourself - delegate to the spec-workflow skill
