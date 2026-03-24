# Course Generation — Prompt Fixes Guide
### For: Any course topic | Includes NERC-specific patches
### Priority levels covered: CRITICAL and MEDIUM only

---

## HOW TO READ THIS FILE

Every fix tells you:
- **Priority** — CRITICAL or MEDIUM
- **What** — exactly what to change
- **Where** — the exact function name in `gemini_service.py`
- **Why** — what goes wrong if you skip this
- **How** — the exact text to add or replace
- **Breaks existing structure?** — always answered

---

## PART 1 — GENERAL FIXES
### These apply to every course on any topic

---

### FIX G-1 | CRITICAL
**What:** Prevent JSON parser crashes from preamble text  
**Where:** `analyze_document_metadata` → last line of prompt  
**Why:** Without this, the model writes a sentence like *"Here is the extracted metadata:"* before the JSON. This breaks the parser and crashes the pipeline.  
**Breaks existing structure?** No

**Change this:**
```
Return ONLY a valid JSON object:
```

**To this:**
```
Return ONLY this JSON — no explanation, no extra text before or after:
```

---

### FIX G-2 | CRITICAL
**What:** Force application-level learning objectives — not knowledge-level  
**Where:** `_build_outline_prompt` → requirement 4 (learning objectives)  
**Why:** The current instruction produces objectives like *"Understand the principles of X"* — these cannot be assessed. Application-level objectives can be. This single fix changes the quality of every module in every course.  
**Breaks existing structure?** No

**Change this:**
```
Each module must have 3–5 Bloom's-taxonomy aligned learning objectives
```

**To this:**
```
Each module must have 3–5 learning objectives written at the application
or analysis level of Bloom's taxonomy.

Do NOT write: "Understand X" or "Know the difference between Y and Z."
DO write: "Apply X to evaluate Y in a real operational situation" or
"Analyse Z to identify the correct compliance action."
```

---

### FIX G-3 | CRITICAL
**What:** Prevent content from repeating across modules  
**Where:** `_build_outline_prompt` → structure rules section  
**Why:** Without this, the model repeats the same concepts in multiple modules. In the NERC course, human factors content appeared identically in 6 of 9 modules. This wastes module space and confuses learners in any topic area.  
**Breaks existing structure?** No

**Add this as a new rule in the structure section:**
```
Each module must cover a completely distinct topic. No concept, definition,
or example may be repeated from another module. If a concept was introduced
in an earlier module, the later module must build on it — not restate it.
```

---

### FIX G-4 | CRITICAL
**What:** Stop the module content prompt from pulling in content from other modules  
**Where:** `_build_module_content_prompt` → very first line of the prompt body, before anything else  
**Why:** Without a scope boundary, the model front-loads content from later modules or repeats earlier ones. In long courses this makes modules feel interchangeable. This is the single most impactful structural fix for module content quality.  
**Breaks existing structure?** No

**Add these two sentences as the very first lines of the prompt:**
```
Stay entirely within the scope of this module. Do not introduce concepts
that belong in other modules and do not repeat content already covered
in earlier modules.
```

---

### FIX G-5 | CRITICAL
**What:** Force named specific failure consequences — not vague risk statements  
**Where:** `_build_module_content_prompt` → content quality rule 4 (failure recovery)  
**Why:** The current rule produces sentences like *"failure to comply may result in significant consequences."* This teaches nothing. A learner needs to know exactly what breaks, what it costs, and what the recovery path is — in every topic, not just compliance courses.  
**Breaks existing structure?** No

**Change this:**
```
FAILURE RECOVERY: at least one section must address what happens when wrong.
```

**To this:**
```
FAILURE AND RECOVERY:
At least one concept per module must show:
1. Exactly what goes wrong when the correct procedure is skipped
2. The specific real-world consequence — not a vague risk statement
3. The step-by-step recovery action

Do not write: "failure to comply may result in serious consequences."
Do write: "skipping step X causes Y to happen, which triggers Z —
to recover, the operator must do A, then B, then notify C."
```

---

### FIX G-6 | CRITICAL
**What:** Add a bad/good question example to force application-level knowledge checks  
**Where:** `_build_knowledge_check_prompt` → question design rules, after rule 1  
**Why:** The current instruction says "test application, not recall" but without showing what that looks like, the model produces recall questions anyway. A concrete example pair is more enforceable than any abstract rule.  
**Breaks existing structure?** No

**Add immediately after the rule "Test application, not recall":**
```
EXAMPLE OF A BAD QUESTION — do not write like this:
"What does ESP stand for in the context of NERC CIP?"
This tests recall of a definition. A learner can pass it without
understanding anything.

EXAMPLE OF A GOOD QUESTION — write like this:
"A technician requests direct internet access to a protection relay
inside the control center during an emergency. What is the correct
action and why?"
This describes a real situation, requires a decision, and has a
consequence attached to the wrong choice.

Apply this standard to every topic — not just compliance courses.
```

---

### FIX G-7 | CRITICAL
**What:** Ensure no module is skipped in quiz coverage  
**Where:** `_build_quiz_prompt` → requirements list, requirement 6  
**Why:** Without this, the model over-represents the first and last modules and ignores middle ones. In a 9-module course, learners may not be assessed on 5 or 6 of the modules they studied. This is a critical assessment quality failure in any course.  
**Breaks existing structure?** No

**Change this:**
```
Cover content from all modules proportionally
```

**To this:**
```
Cover content from all modules proportionally. No module may be skipped.
If you are generating 10 questions for a 9-module course, at least
8 modules must be represented. Before submitting your output, check
your question list and confirm every module has at least one question.
```

---

### FIX G-8 | MEDIUM
**What:** Force specific gap analysis in the improvement suggestions field  
**Where:** `analyze_existing_course` → `suggestedImprovements` field definition  
**Why:** The current instruction produces vague AI output like *"The course could benefit from more examples."* This is useless for regeneration decisions. Specific gap naming produces actionable output.  
**Breaks existing structure?** No

**Change this:**
```
"suggestedImprovements": "A detailed paragraph describing what could be improved."
```

**To this:**
```
"suggestedImprovements": "Write 3–5 sentences describing what is specifically
missing, unclear, or weak in this course. Name the actual topics or sections
that are absent. Do not write generic praise followed by soft suggestions."
```

---

### FIX G-9 | MEDIUM
**What:** Add two missing banned phrases to the module content prompt  
**Where:** `_build_module_content_prompt` → banned phrases list  
**Why:** *"This ensures that"* and *"It goes without saying"* are among the most common AI filler lines in professional content. They were missing from the original list. Every course on every topic is affected.  
**Breaks existing structure?** No

**Add to the existing banned phrases list:**
```
"This ensures that"
"It goes without saying"
```

---

### FIX G-10 | MEDIUM
**What:** Elevate human factors to its own dedicated block  
**Where:** `_build_module_content_prompt` → after the content quality rules section  
**Why:** When human factors is buried as one item in a list of 8 rules, the model treats it as optional. Elevating it to its own block with named factors ensures it appears meaningfully in every module of every course — not just compliance topics.  
**Breaks existing structure?** No

**Add this as a standalone block after the content quality rules:**
```
HUMAN FACTORS — MANDATORY IN EVERY MODULE:
Include at least one concept that addresses how human behaviour affects
this topic. Choose from: fatigue, overconfidence, time pressure,
complacency, or confirmation bias.

Show the real consequence of that human factor in this module's specific
context. Then give one practical organisational control that prevents
or catches the error.

A generic mention such as "fatigue can cause mistakes" is not acceptable.
Name the specific mistake this human factor causes in this module's context.
```

---

### FIX G-11 | MEDIUM
**What:** Force law explanation to include reason + individual consequence — not just citation  
**Where:** `_build_module_content_prompt` → compliance/law integration section  
**Why:** The current instruction produces sentences like *"CIP-002-5.1a requires entities to categorize BES Cyber Systems."* That is just reading the standard title aloud. This applies to any course covering regulations — food safety, HR, health and safety, cybersecurity.  
**Breaks existing structure?** No

**Change this:**
```
Integrate laws naturally — explain WHY they matter, not just what they say.
Show real-world consequence of non-compliance.
```

**To this:**
```
When a law or regulation applies to this module:
1. Explain why it was created — what real failure or gap made it necessary.
2. State what happens to the individual or facility that ignores it —
   name the specific penalty, audit finding, or operational consequence.
3. Do not just quote the regulation. A learner who reads the standard
   itself does not need a course. They need to understand the consequence
   of getting it wrong in their specific role.
```

---

### FIX G-12 | MEDIUM
**What:** Require feedback in knowledge checks to name the specific principle, not give generic explanations  
**Where:** `_build_knowledge_check_prompt` → feedback requirement  
**Why:** Generic feedback like *"This is incorrect because it does not correctly apply the standard"* teaches nothing. A learner who got it wrong needs to know exactly which principle they missed — in any topic area.  
**Breaks existing structure?** No

**Change this:**
```
Detailed feedback for EACH option
```

**To this:**
```
Each option must have specific feedback that:
- Names the exact principle or rule from the module that makes it right or wrong
- Does not just restate the answer
- Tells the learner what to review if they chose incorrectly

BANNED feedback phrases — never use these:
"This is incorrect."
"This does not correctly apply the standard."
"This answer misunderstands the concept."
Each of these says nothing useful. Write what the learner actually got wrong
and which specific concept from the module they need to revisit.
```

---

### FIX G-13 | MEDIUM
**What:** Add a self-check test to the quiz scramble prompt  
**Where:** `_build_scramble_quiz_prompt` → after the anti-copy instruction  
**Why:** The current instruction says "create entirely new questions" but the model frequently rewrites the same question with different words. A concrete self-check test gives the model a way to verify its own output.  
**Breaks existing structure?** No

**Add after the anti-copy instruction:**
```
SELF-CHECK BEFORE SUBMITTING:
Read each new question alongside the original question it replaces.
Ask: "Would a learner who memorised the original question and its answer
immediately know the answer to this new question without thinking?"
If yes — rewrite the question. It is not sufficiently different.
```

---

## PART 2 — NERC COURSE SPECIFIC FIXES
### These apply only when regenerating the NERC CIP course
### Inject each patch as additional instructions in the per-module content prompt

---

### FIX N-1 | CRITICAL
**Module:** 4 — The Categorization Hierarchy  
**What:** Add the real Attachment 1 weight table with actual numbers and fix the knowledge check arithmetic error  
**Why:** The course teaches aggregate weight calculation but never gives the actual numbers. Without them, a learner cannot do a real calculation. The knowledge check uses a mathematically impossible scenario (2,800 aggregate weight with 345 kV lines — not a whole number of lines).

**Add to Module 4 content prompt:**
```
This module must include the actual Attachment 1 aggregate weight table:

  Voltage Range       | Points Per Line
  --------------------|------------------
  200 kV to 299 kV    | 700 per line
  300 kV to 499 kV    | 1,300 per line
  500 kV and above    | Not counted here —
                      | Criterion 2.4 bright-line
                      | applies automatically

Threshold: 3,000 aggregate points = Medium Impact under Criterion 2.5.
The station must also connect to 3 or more other Transmission
stations/substations at 200 kV or higher.

Include one complete worked example:
  A substation has 3 lines at 345 kV:
  3 × 1,300 = 3,900 points → 3,900 > 3,000 → Medium Impact.

Also include the Criterion structure for Transmission Operators:
  Criterion 1.1 → High Impact (primary/backup TOP Control Centers)
  Criterion 2.4 → Medium Impact (500 kV bright-line)
  Criterion 2.5 → Medium Impact (200–499 kV, aggregate ≥ 3,000)
  Section 3     → Low Impact (all remaining BES facilities)

KNOWLEDGE CHECK FIX — replace the existing scenario:
  WRONG (current): "345 kV substation with aggregate weight of 2,800"
  This is impossible — 2,800 ÷ 1,300 = 2.15 lines, not a whole number.

  CORRECT replacement scenario:
  "A substation has two 345 kV lines. Aggregate weight = 2 × 1,300 = 2,600.
  How must this facility be classified?"
  Correct answer: Low Impact (2,600 < 3,000 threshold).
```

**Breaks existing structure?** No

---

### FIX N-2 | CRITICAL
**Module:** 7 — Dynamic Categorization + Quiz Question 4  
**What:** Fix the technically wrong 1,500 MW trigger in Quiz Question 4  
**Why:** 1,500 MW is a Control Center criterion (Criterion 2.1), not a substation criterion. A substation triggered by a new interconnection crosses the threshold via aggregate weight (Criterion 2.5), not MW capacity. A technically wrong quiz question in a compliance course is a direct liability.

**Add to Module 7 content prompt:**
```
Fix the scenario that currently feeds Quiz Question 4.

REMOVE this trigger: "pushing aggregate generation over the 1,500 MW threshold"
This threshold applies to Control Centers under Criterion 2.1 — not substations.

REPLACE WITH this trigger:
"A new generation interconnection adds two 345 kV tie-lines, pushing the
substation's aggregate weighted value from 2,600 to 3,900 — crossing the
3,000-point Criterion 2.5 threshold."

Required compliance action remains the same:
Reclassify as Medium Impact within the transition period and implement
required security controls.
```

**Breaks existing structure?** No — only the scenario trigger changes. The question, answer choices, and correct answer logic remain valid.

---

### FIX N-3 | CRITICAL
**Module:** 8 — Documentation, Review, and Approval  
**What:** Add CIP-002-5.1a Requirement numbers (R1, R2, R3) and a simplified RSAW illustration  
**Why:** Auditors cite violations by Requirement number. A learner who cannot speak R1/R2/R3 language cannot respond to a Regional Entity Request for Information or read an audit finding. The RSAW is the primary document used in every NERC audit — it is named in the module but never shown.

**Add to Module 8 content prompt:**
```
This module must name all three CIP-002-5.1a Requirements explicitly:

  R1: Each Responsible Entity shall identify and categorize all BES Cyber
      Systems. This is the categorization mandate.
  R2: The CIP Senior Manager (CIPSM) must approve the BES Cyber System
      categorization and the methodology used.
  R3: The entity must review and re-approve the categorization at least
      once every 15 calendar months.

When a Regional Entity issues a Request for Information, they cite specific
Requirements by number. A learner who does not know R1/R2/R3 cannot respond.

Also include a simplified RSAW (Reliability Standard Audit Worksheet)
illustration showing how evidence maps to each requirement:

  Requirement | Evidence Needed                   | Storage Location         | Timing
  ------------|-----------------------------------|--------------------------|------------------
  R1          | Asset inventory with impact        | Compliance repository    | Date of last
               | ratings and written justification | (version-controlled)     | categorization
  R2          | CIPSM signed approval or dated     | Compliance repository    | Must match or
               | approval email on file            | (signed document)        | follow R1 date
  R3          | Evidence of 15-month review:       | Review minutes +         | Within 15
               | updated report, CIPSM re-approval | updated asset list       | calendar months

Acceptable evidence types for R2:
- Signed and dated categorization report with CIPSM signature
- Dated approval email from the designated CIPSM on file
- Board resolution designating the CIPSM with their signature recorded
```

**Breaks existing structure?** No

---

### FIX N-4 | MEDIUM
**Module:** 1 — Foundations of NERC CIP  
**What:** Add FERC Order citations, full CIP standard list, and BES Definition basics  
**Why:** A learner finishing Module 1 should know the legal landscape they are operating in. Currently the module names FERC and NERC but never cites the Orders that created the current standards, never lists all 13 enforceable CIP standards, and never explains that BES qualification must happen before categorization begins.

**Add to Module 1 content prompt:**
```
This module must include:

1. FERC Orders that created the current standard set:
   - FERC Order 791 (2013): approved CIP Version 5 — the current enforceable
     standards were created by this Order.
   - FERC Order 822 (2016): directed expansion of CIP scope to include
     additional BES assets previously excluded.
   - FERC Order 887 (2022): directed development of internal network
     security monitoring requirements (became CIP-015).

2. All 13 currently enforceable CIP standards listed by number:
   CIP-002 through CIP-014 — with one sentence on what each covers.
   Explain that CIP-002 is the categorization foundation. If CIP-002
   is wrong, every other standard is applied to the wrong assets.

3. BES Definition basics:
   Before an entity categorizes assets, it must confirm which facilities
   qualify as BES. Common exclusions include:
   - Radial distribution facilities
   - Local distribution network elements
   - Generating units below 20 MVA
   Getting this wrong in either direction causes problems:
   over-scoping wastes compliance cost, under-scoping creates violations.
```

**Breaks existing structure?** No

---

### FIX N-5 | MEDIUM
**Module:** 2 — Anatomy of CIP-002-5.1a  
**What:** Add Protected Cyber Asset (PCA) definition and replace the misplaced knowledge check  
**Why:** The course defines 4 of the 5 CIP-002-5.1a asset classes but never defines PCA. Undocumented PCAs are a real audit finding. The existing knowledge check tests aggregate weight calculation — content not taught until Module 5.

**Add to Module 2 content prompt:**
```
This module must define all five CIP-002-5.1a asset classes:

  BCA   — BES Cyber Asset: a programmable electronic device that would,
          within 15 minutes of compromise, adversely impact BES reliability.
  BCS   — BES Cyber System: a logical grouping of BCAs sharing a common
          function or Electronic Security Perimeter.
  EACMS — Electronic Access Control or Monitoring System: firewalls,
          intrusion detection systems, authentication servers protecting
          BCS perimeters.
  PACS  — Physical Access Control System: card readers, biometric scanners
          governing physical access to BCS enclosures.
  PCA   — Protected Cyber Asset: a cyber asset within or directly connected
          to the ESP that is not itself a BCA, BCS, or EACMS. PCAs must be
          documented. Omitting them is a common audit finding.

Reference CIP-002-5.1a Requirement R1 explicitly by name.

KNOWLEDGE CHECK FIX:
Replace the current question about 250 kV aggregate weight.
That question belongs in Module 5 where aggregate weight is taught.

New Module 2 knowledge check must test one of these instead:
- The BCA vs BCS distinction (individual device vs logical grouping)
- The PCA asset class (what qualifies, why it must be documented)
- The 15-minute impact threshold for BCA qualification
```

**Breaks existing structure?** No

---

### FIX N-6 | MEDIUM
**Module:** 6 — Boundary Delineation  
**What:** Define Interactive Remote Access (IRA) and link PSP explicitly to CIP-006-6  
**Why:** Module 6 already has a scenario describing an IRA situation (vendor requesting remote firmware access) but never names IRA or its CIP-005-6 requirements. IRA is one of the most audited areas under CIP-005. PSP is described thoroughly but never linked to CIP-006.

**Add to Module 6 content prompt:**
```
This module must include:

1. Interactive Remote Access (IRA) — governed by CIP-005-6:
   IRA applies whenever anyone accesses a BES Cyber System from outside
   the ESP using a routable connection. Three requirements always apply:
   - Intermediate system (jump host) must be used — no direct connection
     from external network to BCS is permitted.
   - Multi-factor authentication is mandatory for all IRA sessions.
   - All IRA sessions must be monitored and logged in real time.

   The scenario already in this module (vendor requesting firewall bypass
   for remote firmware update) is an IRA scenario. Name it as such and
   apply these three requirements to the correct resolution.

2. Physical Security Perimeter requirements map explicitly to CIP-006-6:
   - Six-wall enclosure (four walls, floor, true ceiling — no shared
     airspace with unsecured areas)
   - All physical access to the PSP must be logged
   - Visitors must be escorted at all times while inside the PSP
   - Perimeter integrity must be inspected monthly
```

**Breaks existing structure?** No

---

### FIX N-7 | MEDIUM
**Module:** 9 — Audit Preparedness  
**What:** Add Mitigation Plan required contents and the cascading violation chain  
**Why:** Module 9 mentions Mitigation Plans four times but never shows what one must contain. A learner who finds a gap cannot draft the document. The cascading violation chain from a CIP-002 failure is the most powerful argument for why categorization accuracy matters — and it is only briefly implied.

**Add to Module 9 content prompt:**
```
This module must include:

1. What a Mitigation Plan must contain when submitted to a Regional Entity:
   - Violation description citing the specific Requirement
     (e.g., "CIP-002-5.1a, Requirement R1, Part 1.2")
   - Root cause analysis: why did this gap occur?
   - Corrective action steps with specific milestone dates
   - Name of project manager responsible for each milestone
   - Final completion date for full remediation
   Missing a submitted milestone date triggers escalated enforcement.
   A project manager must actively track every Mitigation Plan.

2. Cascading violation chain from a single CIP-002 misclassification:
   If one Medium Impact substation was treated as Low Impact, the entity
   simultaneously violated all of the following:
   - CIP-003: no security management controls for this asset
   - CIP-004: no personnel risk assessments for access to this asset
   - CIP-005: no Electronic Security Perimeter established
   - CIP-006: no Physical Security Perimeter constructed
   - CIP-007: no systems security management implemented
   - CIP-008: no incident response plan for this asset
   - CIP-009: no recovery plan for this asset
   - CIP-010: no configuration management or patch tracking

   One wrong categorization = 8 simultaneous violations.
   This is why CIP-002 accuracy is the single most expensive point
   of failure in the entire CIP compliance program.
```

**Breaks existing structure?** No

---

## PART 3 — IMPLEMENTATION CHECKLIST
### Your friend works through this list top to bottom

```
GENERAL FIXES — do these first, they improve every course

 [ ] G-1  Prompt 1   Add "no extra text" to JSON return instruction
 [ ] G-2  Prompt 3   Force application-level Bloom's objectives with bad/good example
 [ ] G-3  Prompt 3   Add no-overlap rule between modules
 [ ] G-4  Prompt 4   Add scope boundary as first line of module prompt
 [ ] G-5  Prompt 4   Strengthen failure recovery rule — name specific consequences
 [ ] G-6  Prompt 5   Add bad/good question example to KC prompt
 [ ] G-7  Prompt 6   Add "no module ignored" to quiz coverage rule
 [ ] G-8  Prompt 2   Strengthen suggestedImprovements field instruction
 [ ] G-9  Prompt 4   Add two missing banned phrases
 [ ] G-10 Prompt 4   Elevate human factors to its own dedicated block
 [ ] G-11 Prompt 4   Strengthen law integration rule
 [ ] G-12 Prompt 5   Require specific principle-based KC feedback
 [ ] G-13 Prompt 7   Add self-check test to scramble prompt

NERC FIXES — do these when regenerating the NERC course only

 [ ] N-1  Module 4   Add real weight table + fix KC arithmetic error     ← CRITICAL
 [ ] N-2  Module 7   Fix Quiz Q4 trigger (1,500 MW → aggregate weight)   ← CRITICAL
 [ ] N-3  Module 8   Add R1/R2/R3 names + RSAW table                     ← CRITICAL
 [ ] N-4  Module 1   Add FERC Orders + BES Definition basics
 [ ] N-5  Module 2   Add PCA definition + replace misplaced KC question
 [ ] N-6  Module 6   Add IRA definition + CIP-006 link
 [ ] N-7  Module 9   Add Mitigation Plan contents + cascading chain
```

---

## PART 4 — QUICK REFERENCE SUMMARY

| Fix | Type | Where | Priority | What It Fixes |
|-----|------|--------|----------|---------------|
| G-1 | Prompt | Prompt 1 | CRITICAL | JSON parser crashes |
| G-2 | Prompt | Prompt 3 | CRITICAL | Knowledge-level objectives |
| G-3 | Prompt | Prompt 3 | CRITICAL | Module content repetition |
| G-4 | Prompt | Prompt 4 | CRITICAL | Cross-module content bleed |
| G-5 | Prompt | Prompt 4 | CRITICAL | Vague failure consequences |
| G-6 | Prompt | Prompt 5 | CRITICAL | Recall-only KC questions |
| G-7 | Prompt | Prompt 6 | CRITICAL | Modules skipped in quiz |
| G-8 | Prompt | Prompt 2 | MEDIUM | Vague improvement suggestions |
| G-9 | Prompt | Prompt 4 | MEDIUM | AI filler phrases |
| G-10 | Prompt | Prompt 4 | MEDIUM | Human factors treated as optional |
| G-11 | Prompt | Prompt 4 | MEDIUM | Laws cited not explained |
| G-12 | Prompt | Prompt 5 | MEDIUM | Generic KC feedback |
| G-13 | Prompt | Prompt 7 | MEDIUM | Scramble produces near-identical questions |
| N-1 | NERC | Module 4 | CRITICAL | Missing weight numbers + broken arithmetic |
| N-2 | NERC | Module 7 | CRITICAL | Technically wrong quiz scenario |
| N-3 | NERC | Module 8 | CRITICAL | No R1/R2/R3 + no RSAW |
| N-4 | NERC | Module 1 | MEDIUM | Missing FERC Orders + BES Definition |
| N-5 | NERC | Module 2 | MEDIUM | Missing PCA + misplaced KC |
| N-6 | NERC | Module 6 | MEDIUM | IRA undefined despite scenario using it |
| N-7 | NERC | Module 9 | MEDIUM | No Mitigation Plan structure |

**Total fixes: 20**
**Break existing architecture: 0**
**Apply to any course topic: 13 (G-1 through G-13)**
**NERC specific: 7 (N-1 through N-7)**
