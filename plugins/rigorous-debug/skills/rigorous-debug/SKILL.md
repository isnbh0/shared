---
name: rigorous-debug
description: Evidence-based debugging protocol using the scientific method. Requires one-time project initialization before use. Use when standard debugging has failed and maximum rigor is needed.
---

# Rigorous Scientific Debugging Protocol

---

## Project Profile

Keep this installed skill immutable. Project-specific initialization belongs in one of these project-owned files, first match winning:

1. `.agents/skill-configs/rigorous-debug/config.local.yaml` — personal/local, gitignored
2. `.agents/skill-configs/rigorous-debug/config.yaml` — project-wide, committed
3. Legacy fallback: `.claude/skill-configs/rigorous-debug/config.local.yaml`, then `config.yaml`

If a profile exists only at a legacy path, use it and offer to move it. See `config.example.yaml` beside this skill for all fields.

If no profile exists, stop before debugging and ask whether the user wants to initialize one. If they agree, gather the project's domain, languages/frameworks, concrete definition of correctness, available measurement tools, preferred measurement method, measurable success criteria, and one representative bug. Write the answers to `.agents/skill-configs/rigorous-debug/config.yaml` (or `config.local.yaml` when the user wants personal settings), review them with the user, then begin debugging. Never edit or commit the installed `SKILL.md`.

Do not invent project tools, metrics, or placeholder values. Initialization matters because this protocol depends on objective measurements from the actual project.

---

## Universal Core Principles

**These principles apply to ALL debugging scenarios, regardless of domain.**

### 1. EVIDENCE-ONLY DECISION MAKING

- **NEVER** make claims without measurable, reproducible evidence
- **NEVER** assume anything works until objectively verified
- **NEVER** trust intuition, code review, or visual inspection over quantitative measurements
- **EVERY** hypothesis must be tested with before/after quantitative data

### 2. HYPOTHESIS-DRIVEN METHODOLOGY

- **FORMULATE** explicit hypotheses before making any changes
- **PREDICT** exact measurable outcomes if hypothesis is correct
- **TEST** one variable at a time with controlled conditions
- **MEASURE** actual results with objective tools
- **COMPARE** predictions vs. actual results to validate/reject hypothesis

### 3. SYSTEMATIC INVESTIGATION CHAIN

- **TRACE** problems from symptoms to root causes systematically
- **DOCUMENT** every step of investigation with evidence
- **ISOLATE** variables by testing minimal reproducible cases
- **VERIFY** each finding independently before proceeding

---

## 4-Phase Debugging Process

### Phase 1: Problem Definition

**CRITICAL**: Do NOT skip to writing code. Start here.

**1.1 Quantify the Issue**

Get exact measurements, not descriptions.

**Generic guidance:**
- Use objective measurement tools (see your project-specific tools below)
- Capture current state with hard numbers
- Document baseline state with exact values
- Create reproducible test case

**Project-specific approach (load from the resolved profile):**

```
DOMAIN: [profile `domain`]

MEASUREMENT TOOLS: [profile `measurement_tools`]

QUANTIFICATION METHOD: [profile `preferred_measurement_method`]
Example: "Run Playwright script to capture computed styles"
Example: "Enable debug logging and measure response times"
Example: "Run data validation suite and capture error counts"
```

**1.2 Establish Success Criteria**

Define exactly what "fixed" means.

**Generic guidance:**
- Specific numerical targets
- Measurable behavioral changes
- Clear pass/fail conditions

**Project-specific criteria:**

```
SUCCESS METRICS: [profile `success_metrics`]

Example format:
- Metric 1: [specific target value]
- Metric 2: [acceptable range]
- Metric 3: [pass/fail condition]
```

### Phase 2: Systematic Investigation

**2.1 Map the System**

Understand the complete relevant system.

**Generic guidance:**
- Trace architecture from problem area to relevant boundaries
- Document all relationships affecting the issue
- Identify all potential influence points

**Project-specific mapping:**

```
MAPPING APPROACH: [derive from the profile's domain and actual project architecture]

For web/UI: "Trace DOM hierarchy and CSS cascade"
For backend: "Trace request flow through services"
For data: "Map data lineage and transformations"
For performance: "Profile execution path and resource usage"
```

**2.2 Generate Hypotheses**

Create testable explanations.

**Requirements (universal):**
- Each hypothesis must make specific, measurable predictions
- Hypotheses must be falsifiable with objective tests
- Rank hypotheses by likelihood and testing cost
- Write down predictions BEFORE testing

**Format (universal):**

```
HYPOTHESIS: [specific claim about root cause]

PREDICTION: If this hypothesis is correct, then [specific measurable outcome]

FALSIFIABILITY: This hypothesis is FALSE if [specific measurable outcome]
```

### Phase 3: Controlled Testing

**3.1 The One Variable Rule** (SACRED - NEVER VIOLATE)

Test **ONLY ONE** change at a time.

**Process:**
1. Identify the single variable to test
2. Make ONLY that one change
3. Keep all other variables constant
4. Document exact change with file path and line number
5. Measure result
6. Revert or commit based on evidence
7. THEN test next variable

**❌ FORBIDDEN:**
- "Let me also fix this other thing while I'm here"
- "I'll make a few small changes together"
- "These two changes are related, I'll test them together"

**✅ REQUIRED:**
- One hypothesis → One change → One measurement → One conclusion

**3.2 Measurement Protocol**

Use consistent, objective measurement.

**Project-specific measurement approach:**

```
MEASUREMENT TOOL: [profile `measurement_tools`]

MEASUREMENT PROCEDURE:
[use the profile's preferred method and repository-defined commands]

Example for web:
1. Start dev server: npm run dev
2. Navigate to: http://localhost:5173/test-page
3. Open browser automation: npx playwright test measure.spec.ts
4. Capture: computed styles, element dimensions, screenshots
5. Record: exact numerical values

Example for backend:
1. Deploy change to test environment
2. Run load test: k6 run load-test.js
3. Capture: p50/p95/p99 latencies, error rates
4. Record: exact numerical values
```

**3.3 Hypothesis Validation**

Compare predictions to actual results.

**Decision criteria (universal):**
- Results match predictions → Hypothesis SUPPORTED (not "proven")
- Results contradict predictions → Hypothesis REJECTED
- Results unclear → Hypothesis INCONCLUSIVE, improve measurement
- No partial credit - hypothesis either works or doesn't

**Required documentation format:**

```
HYPOTHESIS: [your hypothesis]

PREDICTION: [specific measurable prediction]

TESTING: [exact change made with file:line reference]

MEASUREMENT BEFORE:
- [metric 1]: [exact value]
- [metric 2]: [exact value]
- [metric 3]: [exact value]

MEASUREMENT AFTER:
- [metric 1]: [exact value]
- [metric 2]: [exact value]
- [metric 3]: [exact value]

RESULT: [comparison - did predictions match?]

CONCLUSION: Hypothesis [SUPPORTED | REJECTED | INCONCLUSIVE] because [evidence-based reasoning]
```

### Phase 4: Verification and Documentation

**4.1 Independent Verification**

Confirm fix through multiple methods.

**Requirements (universal):**
- Repeat measurements to ensure consistency
- Test fix persistence (restart server, refresh page, rerun pipeline)
- Verify no unintended side effects
- Confirm success criteria from Phase 1 are met

**Project-specific verification:**

```
VERIFICATION CHECKLIST: [derive from profile `success_metrics`]

Example for web:
- [ ] Hard refresh browser (Cmd+Shift+R)
- [ ] Test in different browsers
- [ ] Verify no console errors
- [ ] Check for layout shifts
- [ ] Run full test suite

Example for backend:
- [ ] Restart service
- [ ] Verify metrics over 10-minute window
- [ ] Check no regression in other endpoints
- [ ] Review error logs
- [ ] Run integration tests
```

**4.2 Evidence Documentation**

Create permanent record.

**Required elements (universal):**
- Before/after measurements with exact values
- Code changes with file paths and line numbers
- Verification results from multiple methods
- Commit message documenting the evidence

---

## Prohibited Behaviors

### ❌ NEVER DO THESE THINGS:

These rules are **ABSOLUTE** and apply to **ALL** domains:

- **Claim "FOUND THE BUG"** without measurable before/after proof
- **Make multiple changes** simultaneously during testing phase
- **Trust intuition or code review** over objective measurements
- **Assume fix works** based on theory alone
- **Skip verification steps** even if confident
- **Use vague language** like "seems to work" or "looks better"
- **Move to next hypothesis** before fully testing current one
- **Cherry-pick evidence** that supports your preferred conclusion
- **Celebrate or conclude** before measurement verification

### ❌ FORBIDDEN PHRASES:

If you catch yourself thinking these thoughts, **STOP**:

- "This should fix it"
- "I think the problem is"
- "It looks like"
- "Probably caused by"
- "The fix appears to work"
- "I'm pretty sure"
- "Based on my experience"
- "This makes sense because"

### ✅ REQUIRED LANGUAGE PATTERNS:

**ALWAYS** use these patterns:

- "HYPOTHESIS: [specific, testable claim]"
- "PREDICTION: [exact measurable outcome]"
- "TESTING: [exact change with file:line]"
- "MEASUREMENT BEFORE: [numerical data]"
- "MEASUREMENT AFTER: [numerical data]"
- "RESULT: [objective comparison]"
- "CONCLUSION: Hypothesis [SUPPORTED|REJECTED] based on [evidence]"

---

## Project-Specific Customization

Load the resolved project profile before applying this protocol. Use its definition of correctness, available tools, measurement method, success metrics, and representative example instead of generic assumptions.

---

## Quality Control Checklist

Before claiming any bug is fixed, verify **ALL** items:

- [ ] Problem was measured objectively with exact values
- [ ] Hypothesis was stated explicitly with measurable predictions
- [ ] Only one variable was changed during testing
- [ ] Before/after measurements were taken under identical conditions
- [ ] Results were compared to predictions quantitatively
- [ ] Fix was verified through multiple independent methods
- [ ] No assumptions were made about code effectiveness without measurement
- [ ] All evidence is documented with file paths and line numbers
- [ ] Success criteria from Phase 1 are demonstrably met
- [ ] No regressions introduced (verified with project test suite)

---

## Escalation Protocol

If this rigorous protocol fails to solve the issue after exhaustive application:

1. **Document complete investigation**
   - List all hypotheses tested
   - Include all measurements taken
   - Show all evidence gathered

2. **Provide exact current state**
   - Latest measurements
   - Configuration details
   - Reproduction steps

3. **List all approaches attempted**
   - What was tried
   - What results were observed
   - Why each approach was rejected

4. **Recommend next steps**
   - External resources to consult
   - Different investigation approaches
   - Potential need for domain expert

---

## Usage Notes

### When to Use This Protocol

✅ Use when:
- Standard debugging has failed after multiple attempts
- The bug is critical and must be solved definitively
- Previous "fixes" haven't actually worked
- The problem is subtle, intermittent, or hard to reproduce
- You need maximum confidence in the solution
- The bug has expensive consequences if not fixed properly

❌ Don't use for:
- Trivial bugs with obvious fixes (typos, simple logic errors)
- Rapid prototyping or exploratory coding
- When speed is more important than certainty
- Initial investigation phases (use regular debugging first)

### Protocol Activation

When invoked (after initialization), you MUST:

1. **Acknowledge protocol activation** explicitly
2. **Commit to evidence-only methodology**
3. **Begin with Phase 1: Problem Quantification** before any code changes
4. **Follow all mandatory process steps** without exception
5. **Use only approved language patterns** for claims and conclusions
6. **Complete quality control checklist** before claiming success

---

## Remember

**This protocol exists because standard approaches have failed. The situation requires the highest level of scientific rigor possible. No exceptions, no shortcuts, no assumptions.**

The cost of following this protocol is **time and discipline**.

The benefit is **certainty that your fix actually works**.

Choose wisely when to apply it.

---

## Additional Resources

See also:
- [DOMAIN-EXAMPLES.md](DOMAIN-EXAMPLES.md) - Example applications across different domains
- [TEMPLATE-INITIALIZED.md](TEMPLATE-INITIALIZED.md) - Example project profile and protocol application
