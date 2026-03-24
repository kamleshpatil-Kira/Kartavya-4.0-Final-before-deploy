# Course Generation — Round 3 Prompt Fixes (FINAL)
### For: ANY NERC CIP course — any role, any USA entity type
### Round: 3 — All fixes verified by direct JSON inspection
### March 2026

---

## HOW TO READ THIS FILE

Same format as previous fix files. Every fix has:
- **Priority** — CRITICAL or MEDIUM
- **Fix ID** — continues from previous rounds
- **What / Where / Why / How / Breaks existing structure?**

**Do NOT remove or replace any fix from:**
- Round 1: G-1 to G-13, N-1 to N-7 — stay in `gemini_service.py` permanently
- Round 2: L-1 to L-6, C-1 to C-3 — stay in NERC-specific prompts

**All fixes in this file are additive. Zero existing prompt instructions are removed.**

**Scope of each fix is labeled:**
- `[ANY NERC]` — apply whenever generating ANY NERC CIP course for any role
- `[TOP ONLY]` — apply only for Transmission Operator courses
- `[SETTINGS]` — not a prompt change, a generation settings action

---

## PART 1 — LAW AND REGULATION FIXES (L-7 to L-10)

---

### FIX L-7 | CRITICAL | [ANY NERC]
**What:** Module covering CIP-003-8 assigns R2 through R7 to topics that do not belong to that standard
**Where:** `_build_module_content_prompt` → module covering CIP-003-8 security management
**Why:** CIP-003-8 has exactly 3 requirements. The course invents R4, R5, R6, R7 and assigns them to Personnel, Physical Security, System Security, and Recovery Plans — which all live in separate dedicated standards. A learner citing "CIP-003-8 R4" in a real audit will be immediately corrected. This error applies to ANY NERC course that covers CIP-003-8, regardless of which role is being trained.

**Confirmed in course JSON:**
CIP-003-8 R1 = Policy Framework (correct)
CIP-003-8 R2 = CSIRP (WRONG — R2 is CIP Senior Manager designation)
CIP-003-8 R3 = Information Protection (WRONG — R3 is Low Impact security plan)
CIP-003-8 R4 = Personnel and Training (WRONG — does not exist)
CIP-003-8 R5 = Physical Security (WRONG — does not exist)
CIP-003-8 R6 = System Security Management (WRONG — does not exist)
CIP-003-8 R7 = Recovery Plan (WRONG — does not exist)

**Add to the CIP-003-8 module content prompt:**
```
CRITICAL — CIP-003-8 REQUIREMENT NUMBERS (3 requirements only):

  R1: Cybersecurity policies for High and Medium Impact BES Cyber Systems.
      The entity must have documented policies that ADDRESS (not contain)
      the following topics: personnel and training, electronic security
      perimeters, physical security, systems security management, incident
      reporting, recovery plans, and configuration management.
      CIP-003-8 R1 is the policy mandate. The detailed requirements for
      each topic live in their own dedicated standards (see table below).

  R2: Designation of a CIP Senior Manager (CIPSM) responsible for
      leading and overseeing the entity's CIP compliance program.
      R2 is a LEADERSHIP requirement — NOT incident response.

  R3: For entities with Low Impact BES Cyber Systems only — a documented
      security plan covering physical security, electronic access controls,
      and cyber security awareness training.

CIP-003-8 R4, R5, R6, and R7 DO NOT EXIST. Never use these labels.

CORRECT STANDARD FOR EACH TOPIC:
  Incident Response (CSIRP)          → CIP-008-6 R1
  BES Cyber System Information (BCSI)→ CIP-011-3 R1
  Personnel and Training             → CIP-004-7
  Physical Security Perimeter        → CIP-006-6
  System Security Management         → CIP-007-6
  Recovery Plans                     → CIP-009-6 R1
  Configuration Management           → CIP-010-4
  Interactive Remote Access          → CIP-005-7
  Supply Chain Risk Management       → CIP-013-2

The module may reference all of these topics — but must cite each
under its own correct standard, not under CIP-003-8.
```

**Breaks existing structure?** No.

---

### FIX L-8 | CRITICAL | [ANY NERC]
**What:** Quiz question attributes CSIRP activation to "CIP-003-8 R2" — wrong standard, wrong requirement
**Where:** `_build_quiz_prompt` → standard attribution accuracy instruction
**Why:** CIP-003-8 R2 is the CIP Senior Manager designation requirement. CSIRP is mandated by CIP-008-6 R1. This wrong citation appears in a quiz question a learner sees at the end of the course. It is the last impression they take away. This applies to ANY NERC course that includes an incident response quiz question.

**Confirmed in course JSON:**
Quiz Q3: "What is the immediate next step based on CIP-003-8 R2?" — cited for CSIRP activation. Incorrect.

**Add to the quiz prompt:**
```
STANDARD ATTRIBUTION — NEVER GET THESE WRONG IN QUIZ QUESTIONS:

  CSIRP activation                   → CIP-008-6 R1
  (NEVER cite CIP-003-8 R2 for this — R2 is CIP Senior Manager designation)

  CIP Senior Manager designation     → CIP-003-8 R2
  Cybersecurity policy framework     → CIP-003-8 R1
  Low Impact security plan           → CIP-003-8 R3

  Personnel training requirements    → CIP-004-7
  Electronic Security Perimeter      → CIP-005-7
  Interactive Remote Access controls → CIP-005-7
  Physical Security Perimeter        → CIP-006-6
  System security / patch management → CIP-007-6
  Incident response and reporting    → CIP-008-6
  Recovery plans                     → CIP-009-6
  Configuration management           → CIP-010-4
  BES Cyber System Information       → CIP-011-3
  Supply chain risk management       → CIP-013-2
  Physical security of TX stations   → CIP-014-3
  Internal network security mon.     → CIP-015-1

Before finalizing any quiz question that cites a standard by number,
verify the standard name matches the topic in the question.
A citation mismatch is a critical law error in a compliance course.
```

**Breaks existing structure?** No.

---

### FIX L-9 | MEDIUM | [ANY NERC]
**What:** Module 1 states "13 currently enforceable standards" but there are 14
**Where:** `_build_module_content_prompt` → Module 1 standard count
**Why:** The course correctly lists all 14 standards but then says 13. CIP-015-1 (Internal Network Security Monitoring) became enforceable January 1, 2025. A learner who counts the list reads "13" and finds 14 — the contradiction destroys trust in the course's accuracy on the very first substantive page.

**Confirmed in course JSON:**
Course text: "13 currently enforceable standards"
Course list: CIP-002 through CIP-015 = 14 standards

**Change in Module 1 prompt:**
```
WRONG:
"The NERC CIP framework includes 13 currently enforceable standards"

CORRECT:
"The NERC CIP framework includes 14 currently enforceable standards.
CIP-015-1 (Internal Network Security Monitoring) became enforceable
January 1, 2025, bringing the total to 14. Any reference to
'13 CIP standards' reflects pre-2025 information and is now outdated."
```

**Breaks existing structure?** No.

---

### FIX L-10 | CRITICAL | [ANY NERC]
**What:** Course states "perimeter integrity must be inspected monthly" as a CIP-006-6 requirement — this is not in the standard
**Where:** `_build_module_content_prompt` → module covering CIP-006-6 Physical Security
**Why:** CIP-006-6 does not mandate monthly PSP inspections. The enforceable testing requirement under CIP-006-6 R3 is that Physical Access Control Systems must be tested at least once every 24 calendar months. Monthly walkthroughs are a common organizational best practice but are not a NERC requirement. Citing this as CIP-006-6 creates a false compliance obligation. This fix also supersedes the N-6 fix line that introduced this error.

**Confirmed in course JSON:**
Module 6 text: "perimeter integrity must be inspected monthly"
CIP-006-6 R3 actual requirement: PACS testing every 24 calendar months

**In the Module 6 content prompt, replace the N-6 fix line that reads:**
```
- Perimeter integrity must be inspected monthly
```

**With:**
```
- Physical Access Control Systems must be tested and inspected
  at least once every 24 calendar months (CIP-006-6 R3).
  Note: many organizations conduct voluntary monthly walkthroughs
  as internal best practice — but the enforceable CIP-006-6
  requirement is 24-month PACS testing, not monthly inspection.
  Never present best practice as a regulatory mandate.
```

**Breaks existing structure?** No — replaces one line inside the existing N-6 fix block only.

---

## PART 2 — CONTENT AND ASSESSMENT FIXES (C-4 to C-8)

---

### FIX C-4 | CRITICAL | [ANY NERC]
**What:** Course overview learning objectives use retired CIP Version 3 terminology "Critical Cyber Assets (CCAs)"
**Where:** `_build_outline_prompt` → course-level learning objectives
**Why:** Course overview objectives are generated by the outline prompt, not the module content prompt. Fix L-3 (Round 2) corrected CCA in module body content, but the outline prompt was not updated — so the objectives page still uses the retired term. This is the first thing any learner, client, or approver reads. CCA was retired in 2016 when CIP Version 5 took effect. This applies to ANY NERC CIP course for any role.

**Confirmed in course JSON:**
Learning Objective 2: "correctly identify and categorize Critical Cyber Assets (CCAs)"

**Add to the outline prompt objectives instruction:**
```
TERMINOLOGY RULE FOR ALL COURSE-LEVEL LEARNING OBJECTIVES:

Never use "Critical Cyber Assets (CCAs)" or "CCAs" in any learning
objective. This is CIP Version 3 terminology retired in 2016.

Always use:
  "BES Cyber Systems (BCS)" for logical groupings
  "BES Cyber Assets (BCA)" for individual programmable devices

WRONG objective:
"Analyze CIP-002-5.1a requirements to identify and categorize
Critical Cyber Assets (CCAs)."

CORRECT objective:
"Analyze CIP-002-5.1a requirements to correctly identify and
categorize BES Cyber Systems (BCS) and BES Cyber Assets (BCA)."

This rule applies to all objectives, module summaries, and any
other text generated during the outline phase.
```

**Breaks existing structure?** No.

---

### FIX C-5 | CRITICAL | [ANY NERC]
**What:** Module 6 Knowledge Check uses "Implicit Routable Access" — a term that does not exist in any NERC CIP standard. The error appears in both the question text and the feedback text.
**Where:** `_build_knowledge_check_prompt` → module covering CIP-005-7 and IRA
**Why:** The correct NERC CIP defined term is "Interactive Remote Access (IRA)" as defined in CIP-005-7. "Implicit Routable Access" does not appear in any NERC standard, glossary, or regulatory document. A learner who uses this phrase in an audit, on an exam, or in a job interview will be immediately corrected. The error must be fixed in both the KC question and the KC feedback, as both contain the wrong term.

**Confirmed in course JSON:**
M6 KC question: "...mandate for Implicit Routable Access (IRA)?"
M6 KC feedback: "...specifically mandates an intermediate system...for Implicit Routable Access (IRA)."

**Add to the KC prompt for the module covering CIP-005-7:**
```
TERMINOLOGY ENFORCEMENT — CIP-005-7 MODULE KC:

The correct NERC CIP defined term is exactly:
  "Interactive Remote Access (IRA)"

This term must appear correctly in BOTH:
  1. The knowledge check question text
  2. All feedback text for correct and incorrect answers

NEVER use:
  "Implicit Routable Access"
  "Indirect Remote Access"
  "Inbound Remote Access"
  Any variation other than "Interactive Remote Access (IRA)"

Definition for reference: Interactive Remote Access is user-initiated
access by a person employing a routable protocol from outside the
Electronic Security Perimeter to a BES Cyber System.
The three mandatory controls under CIP-005-7 are:
  1. Intermediate system (jump host)
  2. Multi-factor authentication (MFA)
  3. Real-time monitoring and logging of all sessions
```

**Breaks existing structure?** No.

---

### FIX C-6 | MEDIUM | [TOP ONLY]
**What:** Quiz Question 5 tests Criterion 2.5 Medium Impact categorization but does not state the connection count — making the correct answer technically unverifiable
**Where:** `_build_quiz_prompt` → Criterion 2.5 scenario questions
**Why:** The course teaches that Criterion 2.5 requires BOTH: (1) aggregate weight ≥ 3,000 points AND (2) connected to 3 or more other transmission stations at 200 kV+. A quiz question that gives only the aggregate weight and omits the connection count cannot be answered correctly using what the learner was taught. It trains learners to ignore the second condition — the exact opposite of the course's teaching.

**Confirmed in course JSON:**
Q5: "A BES Cyber System controls 4 transmission lines at 300 kV...How should it be categorized?"
No connection count stated. Correct answer marked as Medium Impact — unverifiable.

**Add to the quiz prompt:**
```
CRITERION 2.5 QUESTION RULE:
Any quiz question involving Medium Impact categorization under
Criterion 2.5 MUST provide BOTH conditions in the question stem:

  1. The aggregate weighted value or enough data to calculate it
     (e.g., "four 300 kV lines = 5,200 aggregate points")
  2. The connection count to other transmission stations at 200 kV+
     (e.g., "connected to 5 other transmission stations at 230 kV")

A question that gives only the point total is technically unanswerable
using Criterion 2.5 as taught. It will make a learner who studied
correctly doubt their knowledge.

WRONG question stem (missing connection count):
"A BES Cyber System controls 4 transmission lines at 300 kV and
serves a critical industrial load. How should it be categorized?"

CORRECT question stem (both conditions present):
"A substation has 4 transmission lines at 300 kV (aggregate weight:
5,200 points) and is connected to 5 other transmission stations at
200 kV or higher. How should it be categorized?"
```

**Breaks existing structure?** No.

---

### FIX C-7 | MEDIUM | [TOP ONLY]
**What:** Module 4 Knowledge Check correct feedback does not name Criterion 2.5 or its two conditions — G-12 was not fully applied here
**Where:** `_build_knowledge_check_prompt` → Module 4 feedback instructions
**Why:** Fix G-12 (Round 1) requires feedback to name the specific principle. Module 4 tests the most technically important concept in the course — Criterion 2.5's two-condition rule. A learner who answers incorrectly reads "This choice correctly applies the detailed criteria" and learns nothing. They do not know which condition they missed.

**Confirmed in course JSON:**
M4 KC correct feedback: "This choice correctly applies the detailed criteria for asset impact rating, ensuring proper security measures."
This is vague — names no principle, teaches nothing.

**Add to Module 4 KC prompt:**
```
MODULE 4 KC FEEDBACK — MANDATORY CONTENT:

The correct answer feedback MUST name Criterion 2.5 and both conditions:

CORRECT ANSWER FEEDBACK TEMPLATE:
"Correct. Under Criterion 2.5, BOTH conditions must be satisfied for
Medium Impact classification: (1) aggregate weighted value must reach
3,000 points or more, AND (2) the facility must connect to 3 or more
other Transmission stations at 200 kV or higher.
In this scenario, condition 2 is not met — only [N] connections exist,
not 3 or more. Therefore the correct classification is Low Impact
regardless of the point total."

WRONG ANSWER FEEDBACK TEMPLATE:
"Incorrect. Criterion 2.5 requires BOTH conditions — not just the
aggregate weight. With only [N] connections to other transmission
stations at 200 kV+, the second condition fails. Both must be
satisfied before Medium Impact classification applies."

Do not write: "This choice correctly applies the detailed criteria."
That sentence teaches nothing and fails the G-12 requirement.
```

**Breaks existing structure?** No.

---

### FIX C-8 | MEDIUM | [ANY NERC]
**What:** Module 3 is titled "Identify Critical Cyber Assets" but its actual content covers CIP-003-8 Security Management Controls
**Where:** `_build_outline_prompt` → Module 3 title instruction
**Why:** "Identify Critical Cyber Assets" is CIP-002 content — already covered in Module 2. Module 3 covers CIP-003-8: policy framework, CIP Senior Manager designation, and references to supporting standards. The mismatch means a learner searching for incident response content cannot find it by title, and a client reviewing the outline will question what the module actually teaches.

**Confirmed in course JSON:**
Module 3 title: "Identify Critical Cyber Assets"
Module 3 content: CIP-003-8 R1 policy framework, CSIRP, information protection, personnel training, physical security

**Add to the outline prompt module structure section:**
```
MODULE 3 TITLE RULE:
Module 3 must be titled: "CIP-003-8: Cyber Security Management Controls"

This title accurately reflects the module's content:
- CIP-003-8 policy framework overview
- CIP Senior Manager (CIPSM) designation and role (R2)
- How CIP-003-8 R1 policies reference the supporting standards
  (CIP-004, CIP-005, CIP-006, CIP-007, CIP-008, CIP-009, CIP-011)

Do NOT title this module:
  "Identify Critical Cyber Assets" — that is Module 2 content
  "Cybersecurity Fundamentals" — too generic
  "Security Management Overview" — acceptable if CIP-003-8 is in subtitle

The title must make it clear to a learner which standard this module covers.
```

**Breaks existing structure?** No.

---

## PART 3 — NEW NERC CONTENT FIXES (N-8, N-9)

These address gaps found during law review that were not covered in previous rounds.

---

### FIX N-8 | CRITICAL | [TOP ONLY]
**What:** Criterion 2.4 (500 kV bright-line rule) is completely absent from the entire course
**Where:** `_build_module_content_prompt` → Module 4 (asset categorization/impact rating)
**Why:** Criterion 2.4 is the simplest and most commonly triggered Medium Impact rule for Transmission Operators — any substation at 500 kV or higher is automatically Medium Impact with no calculation required. The course teaches Criterion 2.5 (the calculation-based rule) thoroughly but never mentions Criterion 2.4. A TOP with a 500 kV substation would apply Criterion 2.4, not 2.5 — yet this course leaves them with no knowledge of it. Zero mentions of "500 kV" in the entire course.

**Confirmed in course JSON:**
Criterion 2.4 mentions: 0
500 kV mentions: 0
Criterion 2.5 mentions: 3

**Add to Module 4 content prompt:**
```
This module must cover ALL THREE impact criteria for Transmission Operators
in the following order:

CRITERION 1.1 — HIGH IMPACT:
  Primary and backup Control Centers of Transmission Operators that
  perform the functional obligations of a TOP.
  No calculation required — if you are a TOP Control Center, you are High Impact.

CRITERION 2.4 — MEDIUM IMPACT (BRIGHT LINE):
  Any BES Cyber System at a substation that is operated at 500 kV or higher.
  No calculation required — 500 kV or higher is automatically Medium Impact.
  This is called the "bright-line" rule because there is no judgment involved.
  Example: A 500 kV switching station = Medium Impact under Criterion 2.4.

CRITERION 2.5 — MEDIUM IMPACT (CALCULATED):
  Substations at 200 kV to 499 kV where BOTH conditions are met:
  1. Aggregate weighted value ≥ 3,000 points (using Attachment 1 table)
  2. Connected to 3 or more other Transmission stations/substations at 200 kV+
  Voltage weight table (must be shown as a labeled table, not inline text):
    200 kV to 299 kV = 700 points per line
    300 kV to 499 kV = 1,300 points per line
    500 kV and above = NOT counted here (Criterion 2.4 applies instead)

SECTION 3 — LOW IMPACT:
  All remaining BES Cyber Systems not meeting Criterion 1.1, 2.4, or 2.5.

Include a worked example for EACH criterion so learners can apply all three.
Criterion 2.4 worked example: "A protection relay at a 765 kV substation
— automatically Medium Impact under Criterion 2.4. No calculation needed."
Criterion 2.5 worked example: "A substation with 3 lines at 345 kV:
3 × 1,300 = 3,900 pts > 3,000 threshold, connected to 4 stations at 230 kV
— Medium Impact under Criterion 2.5."
```

**Breaks existing structure?** No — adds two missing criteria to an existing module.

---

### FIX N-9 | MEDIUM | [ANY NERC]
**What:** Course does not identify which Responsible Entity type is being trained or which CIP-002 criteria apply to that role — causing the course to be unusable for non-TOP roles without modification
**Where:** `_build_outline_prompt` → course scope section
**Why:** NERC CIP standards apply to multiple Responsible Entity types — Transmission Operators (TOP), Generator Operators (GOP), Balancing Authorities (BA), Reliability Coordinators (RC), Transmission Owners (TO), and others. Each entity type has different CIP-002 Attachment 1 criteria that determine what is High, Medium, or Low Impact for them. A course that only teaches TOP criteria (Criterion 1.1, 2.4, 2.5) will teach incorrect classification to a GOP learner. Any NERC CIP course must open by defining which Responsible Entity type is in scope and which criteria apply to that type.

**Add to the outline prompt scope section:**
```
RESPONSIBLE ENTITY SCOPE — REQUIRED IN EVERY NERC CIP COURSE:

The course introduction must identify which Responsible Entity type(s)
are the target audience for this course. Different entity types use
different CIP-002 Attachment 1 criteria.

Common entity types and their primary impact criteria:

  Transmission Operator (TOP):
    High Impact  → Criterion 1.1 (TOP Control Centers)
    Medium Impact→ Criterion 2.4 (500 kV+ bright line)
                   Criterion 2.5 (200-499 kV, calculated)
    Low Impact   → Section 3 (all remaining BES)

  Generator Operator (GOP):
    High Impact  → Criterion 1.3 (generating plants ≥1,500 MW aggregate)
    Medium Impact→ Criterion 2.6 (generating plants 300-1,499 MW aggregate
                   OR individual unit ≥300 MW)
    Low Impact   → Section 3

  Balancing Authority (BA) / Reliability Coordinator (RC):
    High Impact  → Criterion 1.2 (BA/RC Control Centers)
    Medium Impact→ Criteria applying to associated transmission assets

  Transmission Owner (TO) / Distribution Provider (DP):
    Typically Low Impact only unless owning High/Medium substations

The course must state at the beginning which entity type is in scope.
All scenarios, examples, and knowledge checks must use situations
relevant to that entity type's actual daily operations.
Do NOT mix criteria from different entity types in the same module.
```

**Breaks existing structure?** No — adds a scope declaration to the outline, not to any module content.

---

## PART 4 — QUALITY FIXES (Q-1 to Q-3)
### These close the gap vs top USA NERC CIP courses from learner, approval, and comparison POV

---

### FIX Q-1 | MEDIUM | [TOP ONLY]
**What:** CIP-004, CIP-007, CIP-008, CIP-009, CIP-011, CIP-013, CIP-014, CIP-015 are each mentioned only 1–3 times — not meaningfully taught
**Where:** `_build_module_content_prompt` → all modules + `_build_outline_prompt`
**Why:** Every top USA NERC CIP course (Infosec, EUCI, SANS) covers all 14 standards with meaningful depth. The current course treats 8 of 14 standards as list items. A learner who takes this course and then faces a CIP-008 audit finding will have no knowledge to draw on. From an approval POV, a course that lists standards but does not teach them will fail expert review.

**The standards that are currently only mentioned and need dedicated coverage:**

| Standard | Currently | Minimum Required |
|----------|-----------|-----------------|
| CIP-004-7 | 1 mention | At least one section: 4-part training program, background check, access revocation within 24 hours |
| CIP-007-6 | 1 mention | At least one section: ports/services, patch management 35-day window, malicious code controls |
| CIP-008-6 | 2 mentions | At least one section: reportable incident definition, 1-hour reporting clock to RE, annual testing |
| CIP-009-6 | 2 mentions | At least one section: recovery plan contents, annual test/drill requirement |
| CIP-011-3 | 1 mention | At least one section: BCSI definition, handling, storage, and disposal requirements |
| CIP-013-2 | 1 mention | At least one section: vendor risk assessment, software/patch source verification |
| CIP-014-3 | 1 mention | Dedicated module recommended (see S-1) |
| CIP-015-1 | 1 mention | At least one section: INSM defined, what must be monitored, log retention |

**Add to the outline prompt:**
```
CIP STANDARDS DEPTH REQUIREMENT FOR NERC COURSES:

Every currently enforceable CIP standard must be taught with enough
depth that a learner could identify a violation when they encounter one.
Listing standards is not teaching them.

The following standards require at least one dedicated concept block
each with: what it requires, why it was created, what a violation
looks like, and how to recover from a finding:

  CIP-004-7: Personnel training (4-part program), background checks,
             access authorization, and 24-hour access revocation rule.

  CIP-007-6: Ports and services management, security patch application
             within 35 days of vendor availability, malicious code
             prevention, security event monitoring.

  CIP-008-6: Reportable incident definition, 1-hour reporting clock
             to the Regional Entity after incident confirmation,
             annual testing of the incident response plan.

  CIP-009-6: Recovery plan required elements, annual test or drill
             requirement, backup and restore procedures.

  CIP-011-3: BES Cyber System Information (BCSI) definition,
             handling controls, storage requirements, disposal
             procedures for media containing BCSI.

  CIP-013-2: Vendor risk management plan, supply chain controls,
             software and patch source verification before deployment.

  CIP-015-1: Internal Network Security Monitoring (INSM) defined,
             what must be monitored inside the ESP, log retention
             requirements.

These do not each need a full module — one substantial concept block
per standard is the minimum. Treat these as the depth floor, not ceiling.
```

**Breaks existing structure?** No — adds depth requirements to existing module prompts.

---

### FIX Q-2 | MEDIUM | [ANY NERC]
**What:** The course has no scenario that puts a learner in an audit situation — the single highest-stakes moment in real NERC CIP compliance
**Where:** `_build_module_content_prompt` → audit/compliance module
**Why:** Every top USA competitor course (Infosec Boot Camp, EUCI) includes audit simulation or at minimum a realistic audit interaction scenario. From a learner POV: audit readiness is the primary reason operators take NERC CIP compliance training. From an approval POV: a compliance course that never puts the learner in a compliance scenario is weaker than one that does. The current M9 covers audit documentation but not what it actually feels like to respond to a Regional Entity request.

**Add to the audit module content prompt:**
```
AUDIT SCENARIO REQUIREMENT:

This module must include at least one scenario where a learner must
respond to an actual Regional Entity audit situation. The scenario
must include:

1. The specific request: a Regional Entity auditor sends a Request
   for Information (RFI) citing a specific Requirement by number
   (e.g., "CIP-002-5.1a Requirement R1, Part 1.2").

2. The operator's challenge: the required evidence is incomplete,
   missing a date stamp, or stored in the wrong location.

3. What the operator should do: locate the correct evidence, verify
   it meets the requirement, and respond within the timeframe.

4. What happens if they fail: a Notice of Alleged Violation (NAVS)
   is issued, leading to a Mitigation Plan requirement.

5. The consequence with a real number: NERC CIP violations carry
   penalties of up to $1,000,000 per violation per day.

This scenario turns compliance knowledge into a skill a learner can
actually use when an auditor arrives. It is the single most valued
content in any compliance training — include it every time.
```

**Breaks existing structure?** No.

---

### FIX Q-3 | MEDIUM | [ANY NERC]
**What:** The course does not define "Responsible Entity" — the legal term that determines who these standards actually apply to
**Where:** `_build_module_content_prompt` → Module 1 (fundamentals)
**Why:** Every NERC CIP standard begins with applicability — it applies to "Responsible Entities." If a learner does not understand what a Responsible Entity is and how NERC determines applicability, they cannot understand why their organization is required to comply. From a learner POV: "why does this apply to me?" is the first question in any compliance training. From an approval POV: any compliance course that does not explain applicability is incomplete.

**Add to Module 1 content prompt:**
```
Module 1 must define who NERC CIP applies to:

RESPONSIBLE ENTITY DEFINITION:
A Responsible Entity is an organization registered with NERC that
performs one or more reliability functions for the Bulk Electric System.
Registration is required by FERC Order 672. Once registered, the entity
is legally obligated to comply with all applicable NERC Reliability
Standards including CIP standards.

Registration is based on the functions an organization performs:
  - Operating transmission at 100 kV or higher → register as TOP or TO
  - Operating generating facilities → register as GOP or GO
  - Balancing load and generation → register as BA
  - Coordinating reliability across a region → register as RC

The CIP standards are enforceable ONLY against Responsible Entities.
An organization that operates BES assets but is not registered is
itself a compliance violation waiting for enforcement action.

FERC and NERC can impose penalties of up to $1,000,000 per violation
per day on Responsible Entities that fail to comply.
This is the legal basis for why this course exists.
```

**Breaks existing structure?** No.

---

## PART 5 — STRUCTURAL FIX (S-1)

---

### FIX S-1 | CRITICAL | [SETTINGS — NOT A PROMPT FIX]
**What:** Course was generated with numModules = 9 instead of 10
**Where:** Generation settings input — `numModules` parameter
**Why:** The previous version of this NERC course had 10 modules. The regeneration input was set to 9, dropping one module. This is a settings input error, not a prompt bug. Documented here so it is not missed again.

**Before regenerating any NERC CIP course:**
```
SET: numModules = 10 (minimum for a complete NERC CIP course)

The 10th module MUST cover one of the three currently absent topics.
In priority order:

  1st choice — CIP-014-3 (Physical Security of Transmission Stations):
     Largest content gap vs Infosec, EUCI, SANS, and NERC free materials.
     CIP-014-3 is heavily audited because physical attacks on substations
     are the fastest path to grid disruption.
     Must include: risk assessment, unaffiliated third-party review,
     corrective action plan, and coordination with law enforcement.

  2nd choice — Supply Chain Risk Management (CIP-013-2):
     All competitor courses cover this. Absent here.
     Must include: vendor risk assessment, software integrity checks,
     notification requirements when a vendor has a breach.

  3rd choice — Transient Cyber Asset (TCA) Controls (CIP-010-4 deep dive):
     TCA is one of the most common audit findings because it is new
     and organizations frequently mismanage contractor laptops and
     USB drives connecting to BCS.

Recommendation: CIP-014-3 as the 10th module for TOP courses.
```

**Breaks existing structure?** No — settings change only.

---

## PART 6 — URGENT CARRY-FORWARD (Round 2 — not yet applied)

These are from `nerc-law-regulation-fixes.xlsx` and have not been applied yet.
They must go in BEFORE the next regeneration.

### L-6 — URGENT — APRIL 1, 2026 (13 DAYS)
CIP-003-9 replaces CIP-003-8 effective April 1, 2026.
Any course generated on or after April 1 must reference CIP-003-9.
Add this note to Module 1 or the CIP-003-8 module:
```
CIP-003-9 TRANSITION:
CIP-003-9 replaces CIP-003-8 effective April 1, 2026.
Key addition in CIP-003-9: expanded supply chain risk management
requirements for vendors supplying products and services related
to industrial control system security.
Until April 1, 2026: cite CIP-003-8.
From April 1, 2026 onward: cite CIP-003-9.
```

### C-2 — CRITICAL — Weight table missing 1,300 pts row
Add an explicit labeled table to Module 4:
```
Voltage Range       | Points Per Line
--------------------|------------------
200 kV to 299 kV    | 700 per line
300 kV to 499 kV    | 1,300 per line
500 kV and above    | Not counted —
                    | Criterion 2.4 applies
```

### C-3 — MEDIUM — Distinct human factor per module
Apply one unique human factor per module using this mapping:
```
M1 — Overconfidence (assuming past categorization practices are still current)
M2 — Confirmation bias (assuming inventory is complete without checking)
M3 — Complacency (skipping policy review because nothing changed)
M4 — Time pressure (rushing categorization to meet a filing deadline)
M5 — Normalcy bias (assuming a new device matches old categories)
M6 — Familiarity bias (trusting a known vendor without verifying IRA controls)
M7 — Fatigue (missing reclassification trigger after long shift)
M8 — Overconfidence (assuming compliance posture has not changed)
M9 — Confirmation bias (assuming untested recovery plans still work)
M10 — Optimism bias (assuming physical security gaps are unlikely to be exploited)
```

---

## PART 7 — COMPLETE IMPLEMENTATION CHECKLIST

Your friend works through this list top to bottom before the next generation.

```
SETTINGS (do before opening gemini_service.py)
 [ ] S-1   Set numModules = 10 in generation UI             ← CRITICAL

URGENT — APPLY BEFORE APRIL 1, 2026
 [ ] L-6   Add CIP-003-9 transition note                   ← URGENT

LAW AND REGULATION FIXES (Round 3 — new)
 [ ] L-7   Module 3 prompt: fix CIP-003-8 R1/R2/R3 only    ← CRITICAL
 [ ] L-8   Quiz prompt: correct standard attribution table  ← CRITICAL
 [ ] L-10  Module 6 prompt: replace monthly with 24-month  ← CRITICAL
 [ ] L-9   Module 1 prompt: 13 → 14 standards              ← MEDIUM

CONTENT AND ASSESSMENT FIXES (Round 3 — new)
 [ ] C-4   Outline prompt: ban CCA in objectives            ← CRITICAL
 [ ] C-5   Module 6 KC prompt: Interactive Remote Access    ← CRITICAL
 [ ] N-8   Module 4 prompt: add Criterion 2.4 + 1.1        ← CRITICAL
 [ ] C-2   Module 4 prompt: add 1,300 pts/line table row   ← CRITICAL (Round 2 carry)
 [ ] C-6   Quiz prompt: Criterion 2.5 both conditions      ← MEDIUM
 [ ] C-7   Module 4 KC prompt: name Criterion 2.5 in fb    ← MEDIUM
 [ ] C-8   Outline prompt: rename Module 3 title           ← MEDIUM
 [ ] N-9   Outline prompt: add RE scope declaration        ← MEDIUM
 [ ] C-3   Assign distinct human factor per module         ← MEDIUM (Round 2 carry)

QUALITY FIXES (Round 3 — competitor gap closers)
 [ ] Q-1   All module prompts: add depth floor for         ← MEDIUM
           CIP-004, 007, 008, 009, 011, 013, 015
 [ ] Q-2   Audit module prompt: add audit scenario         ← MEDIUM
 [ ] Q-3   Module 1 prompt: add Responsible Entity def     ← MEDIUM
```

---

## PART 8 — QUICK REFERENCE: ALL FIXES THIS ROUND

| Fix | Type | Scope | Priority | What It Fixes |
|-----|------|-------|----------|---------------|
| L-7 | Law | Any NERC | CRITICAL | CIP-003-8 has only R1/R2/R3 — R4–R7 invented |
| L-8 | Law | Any NERC | CRITICAL | CSIRP attributed to CIP-003-8 R2 — wrong standard |
| L-9 | Law | Any NERC | MEDIUM | 13 standards stated, correct count is 14 |
| L-10 | Law | Any NERC | CRITICAL | Monthly PSP inspection not a CIP-006-6 requirement |
| C-4 | Content | Any NERC | CRITICAL | CCA in course overview objectives — retired term |
| C-5 | Content | Any NERC | CRITICAL | Wrong term "Implicit Routable Access" in KC + feedback |
| C-6 | Assessment | TOP only | MEDIUM | Q5 Criterion 2.5 missing connection count |
| C-7 | Assessment | TOP only | MEDIUM | M4 KC feedback vague — does not name Criterion 2.5 |
| C-8 | Content | Any NERC | MEDIUM | Module 3 title misleads — does not match CIP-003-8 content |
| N-8 | Content | TOP only | CRITICAL | Criterion 2.4 (500kV bright line) completely absent |
| N-9 | Content | Any NERC | MEDIUM | No Responsible Entity scope declaration at course start |
| Q-1 | Quality | TOP only | MEDIUM | 8 of 14 standards only mentioned — need depth floor |
| Q-2 | Quality | Any NERC | MEDIUM | No audit simulation scenario — highest-stakes content missing |
| Q-3 | Quality | Any NERC | MEDIUM | "Responsible Entity" never defined — who does this apply to? |
| S-1 | Settings | This course | CRITICAL | numModules must be 10, not 9 |

**Total new fixes this round: 15**
**Break existing architecture: 0**
**Apply to any NERC course (any role): 10 fixes**
**TOP-course specific: 4 fixes**
**Settings only: 1 fix**

---

## PROJECTED SCORE AFTER ALL FIXES APPLIED

| Stage | Score | What changes |
|-------|-------|-------------|
| Current version | 6.4/10 | As reviewed |
| After CRITICAL fixes only (L-7, L-8, L-10, C-4, C-5, N-8, C-2, S-1) | 7.5/10 | Law errors fixed, 500kV added, 10 modules |
| After all Round 3 fixes + L-6 + C-3 | 8.5/10 | Distinct HF, audit scenario, RE definition, depth floor |
| After CIP-014-3 as dedicated 10th module | 9/10 | Closes largest competitor gap |

At 8.5/10 this course is:
- Better than every Udemy course on accuracy, depth, and assessment
- Competitive with EUCI ($1,695) at a fraction of the price
- Suitable for submission to a corporate L&D approval process
- Defensible against expert review by a NERC compliance professional
- Usable for any NERC Responsible Entity type in the USA with role selection
