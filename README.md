# Shared Dotfiles & Configs

Personal collection of generalizable dotfiles, configurations, and Claude Code skills for reuse across projects.

## Contents

### Claude Code Skills

Located in `.claude/skills/`, these skills enhance Claude Code's capabilities:

- **interview**: Structured requirements discovery through conversational interviews
- **phaser**: Battle-tested patterns and best practices for Phaser 3 game development
- **report-writer**: Structured technical analysis and debugging reports
- **rigorous-debug**: Evidence-based debugging protocol using the scientific method (requires one-time initialization)
- **skill-writer**: Tools for creating effective Claude Code skills
- **spec-workflow**: Two-phase specification and implementation workflow with phased implementation support. Accepts `write`, `write-phased`, or `implement` as argument. Convenience aliases: `/write-spec`, `/write-spec-phased`, `/implement-spec`

## Spec-and-Report Development System

This repository includes a systematic approach to software development using two complementary workflows:

### 1. Spec Workflow (Two-Phase Development)

A disciplined approach that separates planning from execution. Supports both single-spec and phased implementations for complex multi-step features.

#### Phase 1: Writing Specifications
- Agent investigates and creates detailed technical specifications
- Specs are timestamped (`YYMMDD-HHMMSS-description.md`) and stored in `agent-workspace/specs/`
- Status starts as "Requires Implementation"
- Agent commits spec and **stops** - no implementation yet
- Forces thorough investigation before coding

#### Phase 2: Implementation
- Different agent (or same agent in new session) reads the spec
- Updates status to "In Progress"
- Implements according to specification
- Updates spec status to "Completed" with commit references
- Commits all changes together

**Why separate phases?**
- Ensures specifications are reviewed before implementation
- Fresh perspective catches overlooked issues
- Self-contained specs enable independent implementation
- Prevents rushing into solutions before understanding problems

**Spec Structure:**
```
agent-workspace/specs/
├── {timestamp}-name.md           # New specs (Requires Implementation)
├── active/                        # In progress specs
└── archive/
    ├── implemented/              # Completed specs
    └── deprecated/               # Obsolete specs
```

### 2. Report Writer (Post-Implementation Analysis)

Creates structured technical documentation after work is completed:

#### Report Types
- **Debugging Reports**: Problem investigation and resolution
- **Analysis Reports**: Technical comparisons and evaluations
- **Implementation Reports**: Completed work documentation

#### Report Structure
- Timestamped naming (`YYMMDD-HHMMSS-description.md`)
- Stored in `reports/`
- Standardized sections:
  - Executive Summary
  - Key Findings
  - Root Cause Analysis
  - Recommendations

**Benefits:**
- Evidence-based documentation with code references
- Captures lessons learned and decision rationale
- Creates searchable knowledge base
- Helps prevent repeating mistakes

### System Integration

The complete workflow:
1. **Spec Writing**: Investigate → Document → Commit spec
2. **Implementation**: Read spec → Code → Update spec → Commit
3. **Report**: Analyze results → Document findings → Archive

This creates a full audit trail from problem identification through implementation to post-mortem analysis.

## Usage

These configurations and skills can be:
- Symlinked into new projects
- Copied as starting templates
- Referenced for patterns and best practices

## Installation

```bash
# Clone to your preferred location
git clone <repo-url> ~/shared

# Symlink .claude directory into a project
ln -s ~/shared/.claude /path/to/project/.claude

# Or copy specific skills
cp -r ~/shared/.claude/skills/spec-workflow /path/to/project/.claude/skills/
```

## License

Personal use - adapt and modify as needed for your own projects.
