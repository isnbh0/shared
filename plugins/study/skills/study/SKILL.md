---
name: study
description: Conducts Socratic study sessions grounded in a URL or local document. Calibrates to user familiarity, persists session notes to markdown files, and supports resumption across sittings. Use when the user invokes /study or wants to study a specific document or article.
---

# Study

Lead Socratic study sessions grounded in a document or URL, persisting all progress to flat markdown files.

## Invocation

```
/study <uri>
```

- `<uri>`: A URL (e.g., `https://web.dev/learn/html/forms`) or a local file path (e.g., `~/notes/rfc9110.md`)

## Setup

### 1. Resolve Config

Load config with the following precedence (first match wins):

1. `.claude/skill-configs/study/config.local.yaml` — personal/local scope, gitignored
2. `.claude/skill-configs/study/config.yaml` — project scope, committed to repo

If no config is found, stop and ask the user:

> "No study config found. Where should I store session files?
> You can specify a custom path or use the default `.agent-workspace/study/sessions`.
> I'll create `.claude/skill-configs/study/config.yaml` with your choice."

Wait for the user's response, then create the config file before continuing.

Resolved fields:
- `sessions_dir` — directory for session files
- `instructions` — optional freeform behavior/persona instructions (inject into context if present)

### 2. Inject Custom Instructions

If `instructions` is set in config, treat it as additional behavioral context for the entire session. Apply it throughout — it may affect tone, depth, language, or teaching style.

## Flow

### 1. Content Acquisition

**URL**: Fetch using WebFetch. If fetch fails (dynamic content, network issues), tell the user:
> "I couldn't fetch that URL. Can you provide a local file path with the content?"

**Local file**: Read directly using the file read tool.

Digest the content into a working summary to drive the session.

### 2. Session Resumption Check

Search `sessions_dir` for session files whose frontmatter `uri` matches the provided URI.

- **Exact match found**: Read the session file. Show a brief summary of prior progress (topic, familiarity level, where the discussion left off). Say "Let's pick up where we left off." Continue from where it ended.
- **No exact match, basename match(es) found**: Show the matches and ask:
  > "I found session(s) with a similar filename — want to resume one of these, or start fresh?"
  Wait for the user's choice.
- **No match**: Proceed to familiarity calibration.

### 3. Familiarity Calibration (New Sessions Only)

Ask the user how familiar they are with this topic. Based on their response, set the session depth:

<!-- PEDAGOGY: This section defines the default teaching strategy.
     To customize lanes or add variants, replace or extend this section. -->

| User says | Lane | Behavior |
|-----------|------|----------|
| "Never heard of it" | `full-study` | Teach from the ground up using the document content. Socratic questions to build understanding step by step. |
| "Know some" / "Used it but don't understand why" | `guided-study` | Walk through the content focusing on the "why" behind concepts. Skip basics, probe for gaps. |
| "Pretty confident" / "Just check me" | `gap-check` | Ask targeted questions to test understanding. Surface gaps. Record assessment. |

The three lanes are guidelines, not rigid modes. Let the session flow naturally.

Create the session file:

```bash
TIMESTAMP=$(date +"%y%m%d-%H%M%S")
# Derive a kebab-case slug from the topic
# e.g., "HTTP Semantics" -> "http-semantics"
```

Session file format:

```markdown
---
uri: <the source URI — URL or absolute file path>
topic: <human-readable topic name derived from the content>
started: <ISO timestamp>
last_updated: <ISO timestamp>
familiarity: <full-study|guided-study|gap-check>
status: in-progress
---

## Session Notes

```

### 4. Socratic Session

Lead the discussion:

- Ask one focused question at a time (never bundle questions)
- Draw out the user's understanding before providing information
- Use the document content as the backbone — teach through questions, not summaries
- When the user demonstrates understanding, note it and move on
- When a gap is found, explore it — ask follow-up questions, provide context, then verify understanding
- For `gap-check` sessions: probe understanding with questions, record judgment on each area ("solid", "shaky", "gap found"), and note what was covered

### 5. Continuous Filesystem Writes

Update the session file after **every exchange**:

- Update `last_updated` in frontmatter to current time
- Append a brief record under `## Session Notes`
- Each record captures: the question/topic discussed, the user's response quality (demonstrated understanding vs. gap found), and key takeaways
- Keep notes concise — they are a byproduct of conversation, not a separate writing activity
- Goal: a future reader can reconstruct the learning journey from these notes

No explicit close ceremony. When the user stops responding, the session is already persisted.

### 6. Marking Complete

When all major topics in the document have been covered:

- Update frontmatter `status` to `completed`
- Add a brief summary note at the end

## Language Adaptation

Detect the user's language from their first response and conduct the session in that language throughout.

- Match the user's formality level
- Write session notes in the same language as the session

## Key Behaviors

- Never ask multiple questions at once
- Update session file after every exchange
- One session file per URI — multiple sittings append to the same file
- Always check for existing sessions before creating new ones
- Follow the document content but teach through questions, not summaries
- Apply any `instructions` from config throughout the session
