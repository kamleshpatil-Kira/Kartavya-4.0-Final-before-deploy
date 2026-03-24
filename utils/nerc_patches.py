"""
Dictionary of specific factual prompt injections for NERC CIP courses.
These apply strictly per-module to ensure technical accuracy and coverage.
"""

def get_nerc_patches(course_title: str, module_number: int) -> str:
    """Return specific NERC CIP prompt instructions based on the module number if this is a NERC course."""
    if not course_title:
        return ""
        
    title_upper = course_title.upper()
    is_nerc_course = "NERC" in title_upper or "CIP" in title_upper
    
    if not is_nerc_course:
        return ""

    HUMAN_FACTOR_MAP = {
        1: "Overconfidence — assuming existing compliance is already sufficient",
        2: "Confirmation bias — assuming asset inventory is complete without verification",
        3: "Complacency — routine access reviews skipped on familiar systems",
        4: "Time pressure — rushing classification to meet a filing deadline",
        5: "Alert fatigue — ESP monitoring alerts dismissed as false positives",
        6: "Complacency — failing to challenge an unescorted visitor inside the PSP",
        7: "Fatigue — missing threshold crossings during a long monitoring shift",
        8: "Overconfidence — assuming an incident is minor before formal assessment",
        9: "Confirmation bias — assuming backup recovery plans work without testing",
        10: "Complacency — trusting a known vendor's software without integrity verification"
    }

    patches = {
        1: """NERC-SPECIFIC INSTRUCTIONS:
This module must include:

1. FERC Orders that created the current standard set:
   - FERC Order 791 (2013): approved CIP Version 5 — the current enforceable
     standards were created by this Order.
   - FERC Order 822 (2016): directed expansion of CIP scope to include
     additional BES assets previously excluded.
   - FERC Order 887 (2022): directed development of internal network
     security monitoring requirements (became CIP-015).

2. All 14 currently enforceable CIP standards listed by number:
   When listing CIP standards, use ONLY these currently enforced version numbers:
     CIP-002-5.1a | CIP-003-8  | CIP-004-7  | CIP-005-7
     CIP-006-6    | CIP-007-6  | CIP-008-6  | CIP-009-6
     CIP-010-4    | CIP-011-3  | CIP-012-1  | CIP-013-2
     CIP-014-3    | CIP-015-1
   Do NOT cite any other version numbers. These are the only versions in force as of 2025.
   The count is 14 standards — not 13. CIP-015-1 (Internal Network Security Monitoring)
   became enforceable January 1, 2025, bringing the total to 14. Any reference to
   "13 CIP standards" reflects pre-2025 information and is now outdated.
   Note: CIP-003-9 becomes enforceable April 1, 2026 — do not reference it as current.

3. RESPONSIBLE ENTITY DEFINITION — must appear in Module 1:
   A Responsible Entity is an organization registered with NERC that performs one or
   more reliability functions for the Bulk Electric System. Registration is required
   by FERC Order 672. Once registered, the entity is legally obligated to comply with
   all applicable NERC Reliability Standards including all CIP standards.

   Registration is based on the functions an organization performs:
   - Operating transmission at 100 kV or higher → register as TOP or TO
   - Operating generating facilities → register as GOP or GO
   - Balancing load and generation → register as BA
   - Coordinating reliability across a region → register as RC

   The CIP standards are enforceable ONLY against Responsible Entities.
   FERC and NERC can impose penalties of up to $1,000,000 per violation per day.
   This is the legal basis for why this course exists — learners must understand
   that their organization is a Registered Entity with binding compliance obligations.

   Explain that CIP-002 is the categorization foundation. If CIP-002
   is wrong, every other standard is applied to the wrong assets.

3. BES Definition basics:
   Before an entity categorizes assets, it must confirm which facilities
   qualify as BES. Common exclusions include:
   - Radial distribution facilities
   - Local distribution network elements
   - Generating units below 20 MVA
   Getting this wrong in either direction causes problems:
   over-scoping wastes compliance cost, under-scoping creates violations.""",

        2: """NERC-SPECIFIC INSTRUCTIONS:
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
- The 15-minute impact threshold for BCA qualification""",

        3: """NERC-SPECIFIC INSTRUCTIONS:
BANNED TERMINOLOGY — Version 3 terms retired in 2016. DO NOT USE:
  - "Critical Cyber Asset (CCA)"
  - "Critical Cyber Assets (CCAs)"
  - "CCAs" (standalone)
These terms do not appear anywhere in CIP-002-5.1a or any currently
enforceable CIP standard. Using them is a factual error.

REQUIRED REPLACEMENTS:
  When referring to an individual device   → BES Cyber Asset (BCA)
  When referring to a grouped system       → BES Cyber System (BCS)
  When uncertain which applies             → use BCS (the broader term)

Cross-reference Module 2's definitions for BCA and BCS.
Do not redefine them — Module 3 builds on Module 2's foundation.

This module covers CIP-003-8 Security Management Controls.
The CIPSM role and the CIP-003 policy framework are the core content here.
Do NOT introduce BES asset classification content — that belongs in Module 2.

CRITICAL — CIP-003-8 REQUIREMENT NUMBERS (3 requirements only):
CIP-003-8 has exactly THREE requirements. Never invent R4, R5, R6, or R7.

  R1: Cybersecurity policies for High and Medium Impact BES Cyber Systems.
      The entity must have documented policies that ADDRESS (not contain) the
      following topics: personnel and training, electronic security perimeters,
      physical security, systems security management, incident reporting, recovery
      plans, and configuration management.
      CIP-003-8 R1 is the policy mandate. The detailed requirements for each topic
      live in their own dedicated standards — do NOT place them under CIP-003-8.

  R2: Designation of a CIP Senior Manager (CIPSM) responsible for leading and
      overseeing the entity's CIP compliance program.
      R2 is a LEADERSHIP requirement — NOT incident response, NOT CSIRP.

  R3: For entities with Low Impact BES Cyber Systems only — a documented security
      plan covering physical security, electronic access controls, and cyber security
      awareness training.

CIP-003-8 R4, R5, R6, and R7 DO NOT EXIST. Never use these labels.

CORRECT STANDARD FOR EACH TOPIC (cite these, not CIP-003-8):
  Incident Response / CSIRP     → CIP-008-6 R1
  BES Cyber System Information  → CIP-011-3 R1
  Personnel and Training        → CIP-004-7
  Physical Security Perimeter   → CIP-006-6
  System Security Management    → CIP-007-6
  Recovery Plans                → CIP-009-6 R1
  Configuration Management      → CIP-010-4
  Interactive Remote Access     → CIP-005-7
  Supply Chain Risk Management  → CIP-013-2

CIP-003-9 TRANSITION NOTE (include in this module):
CIP-003-9 replaces CIP-003-8 effective April 1, 2026.
Key addition in CIP-003-9: expanded supply chain risk management requirements
for vendors supplying products and services related to industrial control system
security. Until April 1, 2026: cite CIP-003-8. From April 1, 2026 onward: cite
CIP-003-9. Learners should be aware this transition is imminent.""",

        4: """NERC-SPECIFIC INSTRUCTIONS:
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

Include TWO worked examples — one per voltage tier:

Example 1 (200-299 kV tier):
  A substation has 5 lines at 230 kV:
  5 × 700 = 3,500 points → 3,500 > 3,000 + 3 or more connections → Medium Impact.

Example 2 (300-499 kV tier):
  A substation has 3 lines at 345 kV:
  3 × 1,300 = 3,900 points → 3,900 > 3,000 + 3 or more connections → Medium Impact.

The 700-point value (200-299 kV tier) must appear explicitly in the content —
not just in the table. Learners calculating aggregate weight for 230 kV substations
need this value.

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

KNOWLEDGE CHECK — MANDATORY REQUIREMENTS:
Criterion 2.5 has TWO conditions. BOTH must be satisfied for Medium Impact:
  Condition 1: Aggregate weighted value ≥ 3,000 points
  Condition 2: Station connects to 3 OR MORE other Transmission stations at 200 kV+

A station with 10,000 points but only 2 connections = Low Impact.
A station with 3,100 points and 4 connections = Medium Impact.
A scenario that satisfies only Condition 1 teaches the WRONG rule.

The KC question MUST use a scenario that satisfies BOTH conditions, like this:
  "A Transmission station has 200 kV lines, 3,500 aggregate points,
   and connects to 4 other Transmission stations at 200 kV or higher.
   How is it classified?"
  Correct answer: Medium Impact — both Criterion 2.5 conditions are met.

DO NOT write: "A Transmission station has 200 kV lines, 3,500 points, 2 connections."
That scenario teaches that points alone determine classification. That is wrong.""",

        6: """NERC-SPECIFIC INSTRUCTIONS:
This module must include:

1. Interactive Remote Access (IRA) — governed by CIP-005-7:
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
   - Physical Access Control Systems (PACS) must be tested and inspected
     at least once every 24 calendar months (CIP-006-6 R3).
     Note: many organizations conduct voluntary monthly walkthroughs as
     internal best practice — but the enforceable CIP-006-6 requirement
     is 24-month PACS testing, NOT monthly inspection.
     Never present organizational best practice as a regulatory mandate.""",

        7: """NERC-SPECIFIC INSTRUCTIONS:
Fix the scenario that currently feeds Quiz Question 4.

REMOVE this trigger: "pushing aggregate generation over the 1,500 MW threshold"
This threshold applies to Control Centers under Criterion 2.1 — not substations.

REPLACE WITH this trigger:
"A new generation interconnection adds two 345 kV tie-lines, pushing the
substation's aggregate weighted value from 2,600 to 3,900 — crossing the
3,000-point Criterion 2.5 threshold."

Required compliance action remains the same:
Reclassify as Medium Impact within the transition period and implement
required security controls.""",

        8: """NERC-SPECIFIC INSTRUCTIONS:
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
- Board resolution designating the CIPSM with their signature recorded""",

        9: """NERC-SPECIFIC INSTRUCTIONS:
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

3. Configuration Management — CIP-010-4:
   The currently enforced version is CIP-010-4 (not CIP-010-3, which is retired).
   CIP-010-4 introduced two specific new controls vs CIP-010-3:
   - Software and firmware integrity verification before deployment to BCS
   - Expanded transient cyber asset (TCA) and removable media controls
   Cite CIP-010-4 by name whenever referencing configuration change management
   or vulnerability assessments in this module.

4. AUDIT SIMULATION SCENARIO — MANDATORY in this module:
   This module must include at least one scenario where a learner must respond
   to a real Regional Entity audit situation. The scenario must include:

   a. The specific request: a Regional Entity auditor sends a Request for
      Information (RFI) citing a specific Requirement by number
      (e.g., "CIP-002-5.1a Requirement R1, Part 1.2").

   b. The operator's challenge: the required evidence is incomplete, missing
      a date stamp, or stored in the wrong location.

   c. What the operator should do: locate the correct evidence, verify it
      meets the requirement, and respond within the stated timeframe.

   d. What happens if they fail: a Notice of Alleged Violation (NAVS) is
      issued, leading to a Mitigation Plan requirement.

   e. The consequence with a real number: NERC CIP violations carry penalties
      of up to $1,000,000 per violation per day.

   This scenario turns compliance knowledge into a skill the learner can use
   when an auditor arrives. It is the single most valued scenario in any
   compliance training — include it every time."""
    }

    patch = patches.get(module_number, "")
    if patch:
        human_factor = HUMAN_FACTOR_MAP.get(module_number, "Complacency")
        patch += f"\n\nHUMAN FACTOR ASSIGNMENT:\nAssign the following human factor trait to the error scenario in this module:\n{human_factor}"
    return patch


def get_nerc_outline_patches(course_title: str) -> str:
    """Return NERC CIP instructions for the course outline/objectives prompt.
    Returns empty string for non-NERC courses."""
    if not course_title:
        return ""
    title_upper = course_title.upper()
    if "NERC" not in title_upper and "CIP" not in title_upper:
        return ""

    return """
NERC CIP — OUTLINE AND OBJECTIVES RULES:

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

TERMINOLOGY RULE — ALL COURSE-LEVEL LEARNING OBJECTIVES:
Never use "Critical Cyber Assets (CCAs)" or "CCAs" in any learning objective,
module summary, or course overview text. This is CIP Version 3 terminology
retired in 2016 when CIP Version 5 took effect.

Always use:
  "BES Cyber Systems (BCS)" for logical groupings of cyber assets
  "BES Cyber Assets (BCA)" for individual programmable devices

WRONG objective:
  "Analyze CIP-002-5.1a requirements to identify and categorize Critical Cyber Assets (CCAs)."
CORRECT objective:
  "Analyze CIP-002-5.1a requirements to correctly identify and categorize BES Cyber Systems (BCS) and BES Cyber Assets (BCA)."

This rule applies to all objectives, module summaries, and any other text generated during the outline phase.

RESPONSIBLE ENTITY SCOPE — REQUIRED IN EVERY NERC CIP COURSE:
The course introduction and learning objectives must identify which Responsible
Entity type(s) are the target audience. Different entity types use different
CIP-002 Attachment 1 criteria. State the entity type clearly so learners
understand why this course applies to their organization.

Common entity types and their primary impact criteria:
  Transmission Operator (TOP):
    High Impact   → Criterion 1.1 (TOP Control Centers)
    Medium Impact → Criterion 2.4 (500 kV+ bright line) / Criterion 2.5 (200–499 kV, calculated)
    Low Impact    → Section 3 (all remaining BES)

  Generator Operator (GOP):
    High Impact   → Criterion 1.3 (generating plants ≥1,500 MW aggregate)
    Medium Impact → Criterion 2.6 (generating plants 300–1,499 MW or individual unit ≥300 MW)
    Low Impact    → Section 3

  Balancing Authority (BA) / Reliability Coordinator (RC):
    High Impact   → Criterion 1.2 (BA/RC Control Centers)
    Medium Impact → Criteria applying to associated transmission assets

  Transmission Owner (TO) / Distribution Provider (DP):
    Typically Low Impact unless owning High/Medium substations

All scenarios, examples, and knowledge checks must reflect situations relevant
to the declared entity type's actual daily operations. Do NOT mix criteria from
different entity types in the same module."""


def get_nerc_quiz_patches(course_title: str) -> str:
    """Return NERC CIP instructions for the quiz prompt.
    Returns empty string for non-NERC courses."""
    if not course_title:
        return ""
    title_upper = course_title.upper()
    if "NERC" not in title_upper and "CIP" not in title_upper:
        return ""

    return """
NERC CIP — STANDARD ATTRIBUTION RULES FOR QUIZ QUESTIONS:

Never misattribute a topic to the wrong CIP standard. Before finalizing any
quiz question that cites a standard by number, verify the standard name matches
the topic in the question. A citation mismatch is a critical law error.

CORRECT STANDARD FOR EACH TOPIC — use exactly these, no others:
  CSIRP activation / incident response    → CIP-008-6 R1
    (NEVER cite CIP-003-8 R2 for this — R2 is CIP Senior Manager designation)
  CIP Senior Manager (CIPSM) designation  → CIP-003-8 R2
  Cybersecurity policy framework          → CIP-003-8 R1
  Low Impact security plan                → CIP-003-8 R3
  Personnel training requirements         → CIP-004-7
  Electronic Security Perimeter           → CIP-005-7
  Interactive Remote Access (IRA) controls→ CIP-005-7
  Physical Security Perimeter             → CIP-006-6
  System security / patch management      → CIP-007-6
  Incident response and reporting         → CIP-008-6
  Recovery plans                          → CIP-009-6
  Configuration management                → CIP-010-4
  BES Cyber System Information (BCSI)     → CIP-011-3
  Supply chain risk management            → CIP-013-2
  Physical security of TX stations        → CIP-014-3
  Internal network security monitoring    → CIP-015-1

CIP-003-8 has ONLY three requirements (R1, R2, R3).
CIP-003-8 R4, R5, R6, R7 DO NOT EXIST — never cite them.

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
200 kV or higher. How should it be categorized?"""


def get_nerc_kc_patches(course_title: str, module_number: int) -> str:
    """Return NERC CIP instructions for the knowledge check prompt.
    Returns empty string for non-NERC courses or modules without specific KC rules."""
    if not course_title:
        return ""
    title_upper = course_title.upper()
    if "NERC" not in title_upper and "CIP" not in title_upper:
        return ""

    kc_patches = {
        4: """
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
""",
        6: """
NERC CIP — MODULE 6 KC TERMINOLOGY ENFORCEMENT:

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

Definition for reference: Interactive Remote Access is user-initiated access
by a person employing a routable protocol from outside the Electronic Security
Perimeter to a BES Cyber System.

The three mandatory controls under CIP-005-7 are:
  1. Intermediate system (jump host) — no direct external-to-BCS connection
  2. Multi-factor authentication (MFA) for all IRA sessions
  3. Real-time monitoring and logging of all sessions"""
    }

    return kc_patches.get(module_number, "")
