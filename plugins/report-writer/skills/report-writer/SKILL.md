---
name: Writing Technical Reports
description: Creates timestamped technical analysis and debugging reports following a standardized structure. Use when documenting completed work, analyzing technical issues, investigating bugs, or when the user requests a report.
argument-hint: "[topic] [--workspace <dir>]"
---

# Writing Technical Reports

Create structured technical analysis reports with timestamp-based naming and standardized sections.

## Invocation

```
/report-writer [topic] [--workspace <dir>]
```

- `[topic]`: Subject of the report
- `--workspace <dir>`: Override the workspace directory for this report

## Configuration

Config is resolved with the following precedence (first match wins):

1. **CLI flag** (`--workspace`) — one-off override
2. **Local config** (`.claude/skill-configs/report-writer/config.local.yaml`) — personal/local scope, gitignored
3. **Project config** (`.claude/skill-configs/report-writer/config.yaml`) — project scope, committed to repo

```yaml
workspace_dir: .agent-workspace/reports  # where report files are created
```

See `config.example.yaml` in the report-writer plugin for reference.

## Setup

1. Check if `$ARGUMENTS` contains `--workspace <dir>`. If so, use that directory and skip config lookup.
2. Check for config files (first match wins):
   - `.claude/skill-configs/report-writer/config.local.yaml` (local scope, gitignored)
   - `.claude/skill-configs/report-writer/config.yaml` (project scope, committed to repo)
3. **If no config found**: STOP and tell the user:
   > "No report-writer config found. I need a workspace directory to store report files.
   > You can either:
   > 1. Specify a custom path
   > 2. Use the default `.agent-workspace/reports`
   >
   > I'll create `.claude/skill-configs/report-writer/config.yaml` with your choice.
   > (See `config.example.yaml` in the report-writer plugin for reference.)"
   Wait for the user's response, then create the config file before continuing.
4. Set `${REPORTS_DIR}` to the resolved `workspace_dir`. All paths below use this variable.

## File Naming Convention

Format: `{timestamp}-{descriptive-kebab-case-name}.md`

Generate timestamp:
```bash
date +"%y%m%d-%H%M%S"
```

Example: `250919-143915-cli-popover-styling-analysis.md`

## Document Template

Use this structure for all reports:

```markdown
# [Analysis Title/Report Name]

**Date**: YYYY-MM-DD HH:MM:SS
**Commit Hash**: [git commit hash if applicable]
**Analysis Scope**: Brief description of what was analyzed

## Executive Summary

High-level overview of findings, key conclusions, critical issues, and overall assessment.

## Key Findings

1. [Major discovery with technical details]
2. [Observed behavior or issue]
3. [Comparative analysis or specific problem]

## Root Cause Analysis

Deep dive into underlying causes:
- Investigation methodology
- Code examples demonstrating issues
- Systematic breakdown of problem origins

## Recommendations

1. [Specific actionable step - highest priority]
2. [Implementation strategy]
3. [Preventive measures for future]
```

## Workflow

Copy this checklist when creating a report:

```
Report Progress:
- [ ] Step 1: Generate timestamp and get commit hash
- [ ] Step 2: Create file with proper naming
- [ ] Step 3: Add header metadata
- [ ] Step 4: Write executive summary
- [ ] Step 5: Document key findings
- [ ] Step 6: Analyze root causes
- [ ] Step 7: Provide recommendations
```

**Step 1: Generate timestamp and commit hash**

```bash
# Generate timestamp
date +"%y%m%d-%H%M%S"

# Get commit hash (if applicable)
git rev-parse HEAD
```

**Step 2: Create file**

Name the file using `{timestamp}-{descriptive-name}.md` and place in `${REPORTS_DIR}/` directory.

**Step 3: Add header metadata**

Use full ISO date format for the Date field. Include commit hash if analysis is tied to specific code state.

**Step 4: Write executive summary**

Start with the most important information. What should someone know if they only read this section?

**Step 5: Document key findings**

Number your findings. Include technical details, code examples with file paths, and specific observations.

**Step 6: Analyze root causes**

Explain why issues occurred. Include investigation process and evidence-based conclusions.

**Step 7: Provide recommendations**

List specific, actionable steps in priority order. Include implementation strategies.

## Report Types

**Debugging Reports**:
- Focus on problem investigation
- Include reproduction steps
- Document debugging process
- Provide clear resolution path

**Analysis Reports**:
- Compare different implementations
- Evaluate technical approaches
- Assess code quality or architecture
- Provide improvement recommendations

**Implementation Reports**:
- Document completed work
- Analyze implementation decisions
- Record lessons learned
- Evaluate success metrics

## Optional Sections

Add these sections when relevant:

- **Methodology**: How the analysis was conducted
- **Test Results**: Output from debugging or testing
- **Performance Impact**: Metrics or measurements
- **Risk Assessment**: Potential consequences of issues
- **Related Analysis**: Links to other relevant reports
- **Appendices**: Supporting data or detailed code examples

## Writing Guidelines

**Be evidence-based**: Support conclusions with specific observations, code references, and test results.

**Include context**: Reference file paths with line numbers (e.g., `src/components/Button.tsx:42`), function names, and component hierarchies.

**Show comparisons**: Use before/after examples when documenting changes or improvements.

**Stay objective**: Focus on facts and technical details rather than opinions or assumptions.

**Use consistent terminology**: Pick one term for each concept and use it throughout the report.
