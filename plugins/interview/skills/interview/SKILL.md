---
name: interview
description: Conducts structured interviews to explore any topic through conversational discovery — from software requirements to personal decisions, creative projects, or life planning. Use when the user invokes /interview or needs to think through something via guided conversation.
---

# Interview

Conduct one-on-one interviews to help the user think through any topic — extracting insights, constraints, decisions, and clarity through conversational discovery.

## Invocation

```
/interview <topic> [--ref <path>] [--workspace <dir>]
```

- `<topic>`: Short kebab-case name for the interview (e.g., `career-change`, `auth-system`, `family-dynamics`)
- `--ref <path>`: Optional reference file to anchor discussion
- `--workspace <dir>`: Override the workspace directory for this interview

## Configuration

Config is resolved with layered precedence:

1. **Project config** (`.claude/skill-configs/interview/config.yaml`) — project-specific overrides
2. **User config** (`~/.claude/skills/interview/config.yaml`) — user defaults
3. **CLI flag** (`--workspace`) — one-off override

```yaml
workspace_dir: .agent-workspace/interviews  # where interview folders are created
```

## Setup

1. Resolve configuration (check in order, use first found):
   - `.claude/skill-configs/interview/config.yaml` (project-level override)
   - `~/.claude/skills/interview/config.yaml` (user defaults)
   - Use `--workspace` CLI flag to override either

2. Generate timestamp and create workspace:

```bash
TIMESTAMP=$(date +"%y%m%d-%H%M%S")
mkdir -p ${WORKSPACE_DIR}/${TIMESTAMP}-<topic>
```

3. Create SCRATCHPAD.md from [SCRATCHPAD.template.md](SCRATCHPAD.template.md)

4. If reference provided, read it first to anchor discussion

## Interview Methodology

**Format**: Conversational, one question per turn

**Goal**: Help the user think clearly — extract insights, constraints, decisions, and rationale on any topic

### Interviewer Approach

- **One focused question per exchange** — never bundle questions
- Listen for implicit needs, concerns, and constraints
- Dig into "why" 2-3 times when you sense deeper reasoning
- Follow unexpected threads — often the best insights emerge tangentially
- Reference specific context from prior answers to show you're tracking
- Watch for tensions between stated goals or competing values
- Meet the user where they are emotionally — some topics are personal

### Question Flow

Adapt these categories to the topic at hand. Not all categories apply to every interview — use judgment.

**Opening**
- What's on your mind? / What are we exploring?
- What does a good outcome look like?
- Who else is involved or affected?

**Situation**
- What's the current state of things?
- How did we get here?
- What's been tried before?

**Constraints & Boundaries**
- What's non-negotiable?
- What resources, time, or energy exist?
- What can we set aside for now?

**Feelings & Values**
- What matters most to you here?
- What are you worried about?
- What would you regret not doing?

**Decisions**
- What have you already decided?
- What are you uncertain about?
- What trade-offs are you willing to make?

**Priorities**
- What's most important right now?
- What's nice-to-have?
- What's explicitly out of scope?

## Scratchpad Protocol

Update SCRATCHPAD.md after **every exchange**:

- Add emerging themes as patterns surface
- Capture decisions and key insights verbatim
- Note tensions and trade-offs
- Track areas needing deeper exploration
- Record key quotes worth preserving

The scratchpad is your working memory across the conversation.

## Closing the Interview

When 5-7 meaningful threads have been explored:

1. Summarize key themes back to the user
2. Confirm any ambiguous points
3. Offer to synthesize findings

## Output

Create these files in the interview workspace:

1. **SCRATCHPAD.md** — Live notes (updated throughout)
2. **SYNTHESIS.md** — Polished summary (created at end). Use [SYNTHESIS.template.md](SYNTHESIS.template.md)
3. **JUST_IN_CASE.md** — Context that might help future agents (optional). Use [JUST_IN_CASE.template.md](JUST_IN_CASE.template.md)

## Language Adaptation

Detect the user's language from their first response and conduct the interview in that language throughout.

- If the user responds in Korean, ask all questions in Korean
- If the user responds in English, continue in English
- Match the user's formality level (e.g., 존댓말 vs 반말 in Korean)
- Use natural, conversational phrasing in the detected language
- Write scratchpad and synthesis documents in the same language as the interview

## Key Behaviors

- Never ask multiple questions at once
- Update scratchpad after every exchange
- Dig into tensions and trade-offs
- Capture quotes verbatim when they're insightful
- Stay curious — follow the user's energy
- Adapt tone to the topic — warm for personal, crisp for technical
