---
name: skill-writer
description: Creates effective SKILL.md agent skills following best practices. Use when the user asks to create a skill, write a SKILL.md, or needs help authoring agent instructions.
---

# Skill Writing

## Quick Start

Every skill needs a `SKILL.md` file with YAML frontmatter and markdown body:

```markdown
---
name: task-name
description: What it does and when to use it (third person, specific)
---

# Task Name (display heading may use title case)

[Concise instructions here]
```

## Core Workflow

Copy and track your progress:

```
Skill Creation:
- [ ] Step 1: Identify the reusable pattern
- [ ] Step 2: Draft concise instructions
- [ ] Step 3: Add metadata (name, description)
- [ ] Step 4: Test with target model(s)
- [ ] Step 5: Iterate based on usage
```

**Step 1: Identify the reusable pattern**

What context do you repeatedly provide? What procedural knowledge is needed?

**Step 2: Draft concise instructions**

Start minimal. The target agent already has general reasoning ability - only add domain knowledge, workflow constraints, and tool-specific details it would not otherwise know.

Challenge each piece of information:
- Does the agent really need this explanation?
- Can I assume the target model knows this?
- Does this paragraph justify its token cost?

**Step 3: Add metadata**

Write description in third person, including:
- What the skill does
- When to use it (key terms and triggers)

```yaml
description: Extract text from PDFs, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.
```

**Step 4: Test with target agent(s) and model(s)**

- Fast/compact model: Does it provide enough guidance?
- Default coding model: Is it clear and efficient?
- High-reasoning model: Does it avoid over-explaining?

**Step 5: Iterate based on usage**

Observe how the agent uses the skill. Watch for:
- Unexpected exploration paths
- Missed connections
- Overreliance on certain sections
- Ignored content

## Set Appropriate Degrees of Freedom

Match specificity to task fragility:

**High freedom** (text instructions): Multiple approaches valid, context-dependent
**Medium freedom** (pseudocode/templates): Preferred pattern exists, variation acceptable
**Low freedom** (exact scripts): Operations fragile, consistency critical

## Progressive Disclosure

Keep SKILL.md body under 500 lines. Split into separate files:

```markdown
# SKILL.md

## Quick start
[Basic usage here]

## Advanced features
**Form filling**: See [FORMS.md](FORMS.md)
**API reference**: See [REFERENCE.md](REFERENCE.md)
```

Important:
- Keep references one level deep from SKILL.md
- Use forward slashes in paths (not backslashes)
- Add table of contents for files >100 lines

## Common Patterns

**Workflow pattern** (complex tasks):
```markdown
## Workflow
Copy this checklist:
- [ ] Step 1: Do first thing
- [ ] Step 2: Do second thing
[Detailed steps below]
```

**Feedback loop** (quality-critical):
```markdown
1. Create output
2. Validate: `python scripts/validate.py`
3. If validation fails, fix and repeat
4. Only proceed when validation passes
```

**Template pattern** (consistent output):
```markdown
ALWAYS use this exact structure:
[Template here]
```

## Anti-Patterns to Avoid

❌ Windows-style paths (`scripts\\helper.py`)
✓ Unix-style paths (`scripts/helper.py`)

❌ Too many options ("You can use X, or Y, or Z...")
✓ Provide default with escape hatch ("Use X. For special case, use Y instead.")

❌ Time-sensitive info ("Before August 2025...")
✓ Use "Current method" and "Old patterns" sections

❌ Inconsistent terminology (mix "field", "box", "element")
✓ Choose one term, use consistently

❌ Deeply nested references (SKILL.md → advanced.md → details.md)
✓ One level deep (SKILL.md → details.md)

## For Skills with Code

**Utility scripts**: Provide pre-made scripts rather than having the agent write them
- More reliable than generated code
- Save tokens and time
- Ensure consistency

**Package dependencies**: List required packages and verify availability

**Visual analysis**: Convert to images for the agent to analyze layouts

**Verifiable outputs**: Create plan files that get validated before execution

## Quick Reference

**Frontmatter name**: Use the lowercase hyphenated directory slug (`processing-pdfs`, `analyzing-data`).

**Display heading**: Use natural title case and gerund wording when helpful (`# Processing PDFs`).

**Description**: Third person, specific, includes when to use

**File limit**: Keep SKILL.md under 500 lines

**Structure**: YAML frontmatter + markdown body

**Testing**: Test with all target models

**Conciseness**: Assume the target agent can infer common knowledge; only add what's needed
