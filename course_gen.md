## System Improvement Plan

### 1. Anti-Verbosity & Content Quality

**In `_build_module_content_prompt()`**, replace/add these instructions:

```
VERBOSITY RULES (STRICT):
- Every sentence must deliver NEW information. No filler phrases like "In this section, we will explore...", "As mentioned earlier...", "It is important to note that..."
- No circular definitions. No padding. No restating the module title as a sentence.
- Target information density: each paragraph must contain at least 2 actionable or factual claims.
- Word count ceiling per topic: 250 words. If you exceed it, cut the weakest sentences first.
- Prefer active voice. Passive voice only when the actor is unknown or irrelevant.
```

---

### 2. Fact-Checking Before Generation

Add a **pre-generation verification step** in `gemini_service.py` — a new method `verify_facts_and_fetch_guidelines()`:

**Prompt for this step:**
```
You are a research validator and domain expert.

Task: Before generating any course content on the topic "{courseTitle}", do the following:

1. DOMAIN AUDIT: List the 5-7 authoritative bodies, standards organizations, or regulatory agencies that govern this field (e.g., ISO, OSHA, RBI, GDPR authority, etc.)

2. CURRENT GUIDELINES CHECK: State the most recently updated guidelines, laws, or frameworks relevant to this topic as of {current_date}. Include version numbers or effective dates where applicable.

3. FACT BASELINE: List 8-10 core facts about this domain that are universally accepted and verifiable. Flag any that are contested or jurisdiction-dependent.

4. OUTDATED CONTENT WARNINGS: List 3-5 concepts that were once standard but are now outdated, deprecated, or superseded. These must NEVER appear in the course as current practice.

5. JURISDICTION NOTES: If this topic has region-specific rules (e.g., EU vs US vs IN), flag them so they can be parameterized.

Return as JSON:
{
  "authoritative_sources": [],
  "current_guidelines": [{"name": "", "version": "", "effective_date": "", "summary": ""}],
  "verified_facts": [],
  "deprecated_concepts": [],
  "jurisdiction_flags": []
}

Only include information you can state with high confidence. Mark uncertain items with "confidence": "low".
```

**Wire this into `CourseGenerator.generate_course()`** — run this BEFORE outline generation, then inject the output into all subsequent prompts as `verified_context`.

---

### 3. No Real Names / No Company Names

Add to **every prompt** in `gemini_service.py`:

```
COPYRIGHT & ANONYMITY RULES (NON-NEGOTIABLE):
- NEVER use real person names in examples, scenarios, case studies, or dialogue. Use role-based placeholders only: "a project manager", "the compliance officer", "a new employee", "Team Lead A".
- NEVER use real company names, brand names, product names, or trademarked terms in examples. Use generic descriptors: "a mid-sized retail company", "a multinational bank", "a logistics firm", "a government agency".
- NEVER reference real events tied to specific organizations (e.g., "like what happened at Enron"). Use abstract analogies: "In a documented corporate fraud case..." or "A financial institution once faced...".
- Fictional names for personas are also BANNED. No "John", no "Acme Corp". Roles only.
- If a real law or regulation must be cited (e.g., GDPR, SOX), cite the LAW ITSELF, not the cases or companies involved.
```

---

### 4. Course Hook & Engagement Opening

Add a **new generation step** in `CourseGenerator` after outline generation — `generate_course_hook()`:

**Prompt:**
```
You are a master instructional designer and behavioral psychologist specializing in adult learning engagement.

Topic: {courseTitle}
Audience: {targetAudience}
Verified Domain Facts: {verified_facts_summary}

Your task: Write a course OPENING HOOK (300-400 words) that does ALL of the following:

1. PAIN-POINT MIRROR: Open with a specific, relatable professional problem or frustration this audience faces daily — without solving it yet. Make them feel "this course sees me."

2. STAKES STATEMENT: In 2-3 sentences, explain what is at risk if this knowledge gap continues — professionally, financially, or operationally.

3. TRANSFORMATION PROMISE: State concretely what the learner will be able to DO differently after completing this course. Use outcome verbs: "You will be able to...", "By the end, you can...". Minimum 3 concrete outcomes.

4. CREDIBILITY SIGNAL: Reference that the course is built on [list authoritative sources from verified_context] without sounding academic. e.g., "This course reflects guidelines updated as of {current_date}..."

5. CURIOSITY GAP: End with one provocative question or counterintuitive fact from the domain that makes them want to continue. It must be verifiably true.

Tone: {tone}. No fluff. No generic motivational language. This must feel written by a practitioner, not a marketer.

Return plain text only. No JSON. No headers.
```

---

### 5. Course Orientation Section (Section 1 Mandate)

Add a **mandatory first module override** in `_build_outline_prompt()`:

```
MANDATORY STRUCTURE RULE:
The FIRST module of every course must always be titled:
"Course Orientation & Certification Path"

This module must contain exactly these four sub-sections:
  1.1 - What This Course Covers & What It Does Not
  1.2 - Course Objectives (minimum 4, written as measurable outcomes using Bloom's Taxonomy action verbs)
  1.3 - How to Navigate & Use This Training (module flow, knowledge checks, quiz, estimated time)
  1.4 - Your Certification Path (what certification/recognition is earned, criteria to pass, how it applies to their role)

Do NOT count this as one of the 4-5 content modules. The content modules come AFTER this orientation module.
Total modules = 1 orientation module + 4-5 content modules.
```

And add a dedicated prompt for generating this module's content:

```
Generate the "Course Orientation & Certification Path" module for a course on "{courseTitle}" targeting "{targetAudience}".

Strictly follow this structure:

Section 1.1 - Scope Definition:
- 3-4 bullet points on what the learner WILL gain (specific, outcome-based)
- 2-3 bullet points on what is explicitly OUT OF SCOPE (sets correct expectations)

Section 1.2 - Course Objectives:
- Minimum 4 objectives written using Bloom's Taxonomy verbs (Analyze, Apply, Evaluate, Design, Demonstrate)
- Each objective: one sentence, starts with "By the end of this course, you will be able to [verb]..."

Section 1.3 - How to Use This Training:
- Explain the module structure, estimated time per module
- Explain knowledge checks (what they are, they don't affect final score)
- Explain the final quiz (passing threshold, retake policy if applicable)
- Advise optimal learning approach (take notes, complete in order, etc.)

Section 1.4 - Certification Path:
- What is awarded upon completion
- Criteria: minimum quiz score, all modules completed
- How this certification is relevant to their role/industry

Write in {tone} tone. Plain text only inside JSON values. No markdown. No real names. No company names.
```

---

### 6. "Master of the Field" Voice + Current Date Awareness

Add to **all content prompts**:

```
EXPERT VOICE MANDATE:
- Write as if you are a 20-year practitioner in {courseTitle} who also teaches at a graduate level.
- Practitioner voice means: you cite patterns you've "seen across many implementations", you warn about common mistakes, you give the reasoning BEHIND rules not just the rules.
- Do NOT write like a textbook. Write like an expert colleague explaining to a smart peer.
- Flag any principle that has changed in the last 2 years with: "[Updated {current_year}]" inline.

CURRENCY MANDATE:
- All guidelines, statistics, and regulatory references must reflect the state of the field as of {current_date}.
- If a guideline or law has a version or amendment date, state it explicitly.
- If you cannot confirm whether something is current, do NOT include it.
- Inject the pre-verified guidelines from: {verified_guidelines} as the authoritative source for all regulatory content.
```

---

### 7. Implementation Checklist

Here's the order to implement these changes:

```
[ ] 1. Add verify_facts_and_fetch_guidelines() to gemini_service.py
        - Call Gemini with web search enabled (or Gemini 1.5 with grounding)
        - Store result as verified_context dict

[ ] 2. Modify CourseGenerator.generate_course()
        - Step 0: Call fact verification, store verified_context
        - Step 1: Generate hook text via generate_course_hook()
        - Step 2: Generate orientation module via dedicated prompt
        - Step 3: Generate content modules (existing flow)
        - Inject verified_context into ALL prompt builders

[ ] 3. Update _build_outline_prompt()
        - Add mandatory orientation module rule
        - Inject current_date = datetime.now().strftime("%B %Y")

[ ] 4. Update _build_module_content_prompt()
        - Add anti-verbosity rules
        - Add copyright/anonymity rules  
        - Add expert voice mandate
        - Add currency mandate

[ ] 5. Update _build_knowledge_check_prompt() and _build_quiz_prompt()
        - Add anonymity rules
        - Ensure questions test application not just recall

[ ] 6. Update API response schema in main.py
        - Add hook field to course JSON
        - Add orientation_module as index 0
        - Add verified_sources field for transparency

[ ] 7. Update document_processor.py
        - When source material is provided, cross-validate it
          against verified_context and flag contradictions
```

---

### 8. Optional: Gemini Grounding for Live Fact Fetching

If you're using **Gemini 1.5 Pro or Gemini 2.0**, enable Google Search grounding on the fact-verification call specifically:

```python
# In gemini_service.py - for verify_facts_and_fetch_guidelines() only
generation_config = {
    "tools": [{"google_search_retrieval": {}}],  # Enable grounding
    "temperature": 0.1  # Low temp for factual accuracy
}
# Use higher temperature (0.7-0.8) for content generation prompts
# Use temperature 0.1-0.2 for fact verification only
```

This ensures the fact-check step actually retrieves current information rather than relying on training data, while creative/explanatory content still flows naturally.