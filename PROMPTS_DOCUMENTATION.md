# Naksha AI Prompts Documentation

## Overview

This document contains all AI prompts and configurations used in the Naksha course outline generation system. The backend uses Google's Gemini AI to generate course outlines based on two different input types: **File Content** and **Course Title**.

---

## Model Configuration

### AI Model Settings
- **Model**: `gemini-2.5-flash`
- **Temperature**: `0.2` (Extremely low for deterministic, analytical output)
- **Top P**: `0.95` (Filters out bottom 5% of improbable token choices)

### Why These Settings Matter
- **Low Temperature (0.2)**: Forces the AI to be highly deterministic and strictly adhere to the document structure provided, leaving almost zero room for creative hallucinations
- **Top P (0.95)**: Further stabilizes output by filtering unlikely word choices
- **Single-Shot Prompting**: No system instructions, multi-turn chat histories, or hidden system messages—relies entirely on one comprehensive prompt

---

## Prompt Types

There are two distinct prompt templates based on the input type:

1. **File Prompt** (`type: 'file'`) - Extracts structure from document content
2. **Title Prompt** (`type: 'title'`) - Generates outline from course title

---

## 1. File Prompt (type: 'file')

### Purpose
Extracts hierarchical structure from provided document content and formats it as a course outline.

### Full Prompt Template

```
You are a highly accurate content structure analysis tool with expertise in US federal regulations. Your task is to extract the hierarchical structure from the provided document content and format it as a course outline.

RULES:
1.  **EXTRACT, DON'T CREATE:** Identify all main headings, titles, or chapters in the text and use their EXACT wording for the "Module" titles. Do not summarize, paraphrase, or invent new titles, unless needed to merge for the module count limit.
2.  **MAXIMUM 10 MODULES:** The outline must contain a maximum of 10 instructional modules. If the document structure exceeds this, merge related sections under broader headings to fit within 10 modules.
3.  **EXCLUDE FINAL ASSESSMENT:** Do NOT include the "Final Quiz", "Final Exam", or any comprehensive final course assessment in the generated outline.
4.  **RENAME INTERMEDIATE EXAMS:** If you encounter intermediate exams (e.g. "Mid-term Exam"), rename "Exam" to "Quiz".
5.  **IDENTIFY SUB-HEADINGS:** Identify the sub-headings under each main heading and use their EXACT wording for the sub-items.
6.  **TITLES ONLY:** Your output must consist ONLY of the extracted module and sub-item titles. Do NOT include any descriptive text, explanations, summaries, or examples.
7.  **SPECIAL SECTIONS:** If a main heading is clearly an intermediate assessment (e.g., "Quiz", "Test", "Case Study"), treat it as a standalone module. Do NOT extract or list any sub-items or questions from under it. Remember to exclude the Final Exam.
8.  **EXCLUDE KNOWLEDGE CHECKS:** Knowledge checks are considered part of the content but must NOT be listed in the outline. Do not extract headings like "Knowledge Check", "Check Your Understanding", or "Practice Questions".
9.  **FORMATTING:**
    - Use Markdown heading level 2 (##) for Module titles.
    - Use a numbered list for sub-items under each module.
    - **CRITICAL:** Format sub-items using the pattern "**X.Y:** Title" (e.g., **1.1:** Title). Do NOT use the word "Module" or "Lesson" in the sub-item lines. Only use the number sequence.[USER_CONFIGURATION_BLOCK]

EXAMPLE OUTPUT:
## Module 1: Extracted Main Heading
1.  **1.1:** Extracted Sub-heading
2.  **1.2:** Another Extracted Sub-heading

## Module 2: Another Main Heading from the Document
1.  **2.1:** Sub-topic from the document

## Module 3: Mid-term Quiz

Here is the document content to analyze:
---
[DOCUMENT_CONTENT]
```

### User Configuration Block (File Prompt)

When user provides compliance standard and/or additional information, the following block is injected as **Rule #9** continuation:

```
9.  **USER CONFIGURATION & CONTEXT:**
    The user has provided specific configuration settings. You must prioritize these instructions:
    - **SPECIFIC COMPLIANCE:** You MUST strictly adhere to and explicitly mention **[COMPLIANCE_STANDARD]** guidelines in the relevant modules.
    - **USER NOTES:** [ADDITIONAL_INFO]
```

**Note**: This block appears only when `complianceStandard` or `additionalInfo` options are provided. It elegantly continues the numbered list as part of Rule #9.

---

## 2. Title Prompt (type: 'title')

### Purpose
Generates a course outline from a given course title, with expertise in US federal compliance and regulatory training.

### Compliance Context
The prompt includes dynamic compliance context based on user configuration:
- **With Compliance Standard**: "adhering strictly to **[STANDARD]** and other relevant US federal regulations"
- **Without Compliance Standard**: "specializing in US federal compliance and regulatory training"

### Full Prompt Template

```
You are an expert instructional designer [COMPLIANCE_CONTEXT]. Your task is to generate a course outline for the given course title.

IMPORTANT:
- **COMPLIANCE:** Ensure the course content, structure, and terminology strictly adhere to relevant US federal guidelines and incorporate the latest regulatory updates.
- **MAXIMUM 10 MODULES:** Create a maximum of 10 instructional modules.
- **NO FINAL QUIZ:** Do NOT include a "Final Quiz", "Final Exam", or final assessment module.
- **RENAME INTERMEDIATE ASSESSMENTS:** Use the term "Quiz" instead of "Exam" for any intermediate assessments.
- **TERMINOLOGY:** The top-level sections are "Modules". The items under them are sub-sections.
- Do NOT include any descriptive text, explanations, key concepts, or examples. Only provide the titles.
- Knowledge checks are part of the learning content but must NOT be listed as separate items in this outline.
- For modules that are assessments (e.g., Quizzes, Case Studies), provide ONLY the module title. Do not create or list any sub-items for them.[TITLE_MODE_CONFIGURATION_BLOCK]

The output must be in Markdown format.
- Use heading level 2 (##) for Module titles.
- Use a numbered list for sub-items.
- **Format sub-items as "**X.Y:** Title". Do NOT use the word "Module" or "Lesson" in the sub-items.**

Example:

## Module 1: Introduction to HIPAA
1.  **1.1:** Core Principles of HIPAA
2.  **1.2:** Protected Health Information (PHI)

## Module 2: Privacy Rule Compliance
1.  **2.1:** Patient Rights
2.  **2.2:** Administrative Requirements

Create a course outline for the following course title: "[COURSE_TITLE]"
```

### User Configuration Block (Title Prompt)

When user provides compliance standard and/or additional information, the following block is appended as another bullet point in the IMPORTANT section:

```
- **USER CONFIGURATION:**
    - **SPECIFIC COMPLIANCE:** You MUST strictly adhere to and explicitly mention **[COMPLIANCE_STANDARD]** guidelines in the relevant modules.
    - **USER NOTES:** [ADDITIONAL_INFO]
```

**Note**: This block appears only when `complianceStandard` or `additionalInfo` options are provided. It appends as another bullet point in the IMPORTANT section.

---

## Dynamic Options

### Compliance Standard
When provided, this parameter:
1. Updates the compliance context in the Title prompt
2. Adds a **SPECIFIC COMPLIANCE** instruction to the user configuration block

**Code Implementation**:
```javascript
if (complianceStandard) {
  specificInstructions += `    - **SPECIFIC COMPLIANCE:** You MUST strictly adhere to and explicitly mention **${complianceStandard}** guidelines in the relevant modules.\n`;
}
```

### Additional Info
When provided, this parameter adds user notes to the configuration block.

**Code Implementation**:
```javascript
if (additionalInfo) {
  specificInstructions += `    - **USER NOTES:** ${additionalInfo}\n`;
}
```

---

## Prompt Construction Logic

### Code Location
Function: `createPrompt(input, type, options = {})`
File: `server/index.js`
Lines: 100-190

### Process Flow

1. **Extract Options**
   ```javascript
   const { additionalInfo, complianceStandard } = options;
   ```

2. **Build Specific Instructions**
   - Adds compliance standard instruction if provided
   - Adds additional info instruction if provided

3. **Create Configuration Blocks**
   - **File Mode**: Wraps as Rule #9 continuation
   - **Title Mode**: Wraps as bullet point in IMPORTANT section

4. **Generate Compliance Context**
   - With standard: "adhering strictly to **[STANDARD]** and other relevant US federal regulations"
   - Without: "specializing in US federal compliance and regulatory training"

5. **Return Complete Prompt**
   - File prompt: Includes extraction rules + document content
   - Title prompt: Includes generation guidelines + course title

---

## Output Format Requirements

### Module Structure
- **Heading Level**: Markdown `##` for all module titles
- **Module Naming**: "Module [Number]: [Title]"
- **Maximum Modules**: 10 instructional modules

### Sub-item Structure
- **Format**: Numbered list (1. 2. 3. etc.)
- **Pattern**: `**X.Y:** Title` where X is module number, Y is sub-item number
- **Prohibition**: NO use of "Module" or "Lesson" in sub-item lines
- **Example**: `1.  **1.1:** Core Principles of HIPAA`

### Special Rules
- **Assessments**: Quiz/Case Study modules have NO sub-items
- **Knowledge Checks**: Must NOT appear in outline
- **Final Assessment**: Must be excluded entirely
- **Intermediate Exams**: Rename "Exam" to "Quiz"

---

## Example Outputs

### File Prompt Example Output
```markdown
## Module 1: Extracted Main Heading
1.  **1.1:** Extracted Sub-heading
2.  **1.2:** Another Extracted Sub-heading

## Module 2: Another Main Heading from the Document
1.  **2.1:** Sub-topic from the document

## Module 3: Mid-term Quiz
```

### Title Prompt Example Output
```markdown
## Module 1: Introduction to HIPAA
1.  **1.1:** Core Principles of HIPAA
2.  **1.2:** Protected Health Information (PHI)

## Module 2: Privacy Rule Compliance
1.  **2.1:** Patient Rights
2.  **2.2:** Administrative Requirements
```

---

## Error Handling & Retry Logic

### Retry Mechanism
- **Maximum Attempts**: 5
- **Backoff Strategy**: Exponential with jitter
  - Wait time formula: `2^attempts * 1000 + random(0-500)ms`
- **Rate Limit Detection**: Checks for 429 status, quota messages, resource exhaustion

### Error Types
1. **API Key Invalid**: "The outline service is not configured correctly right now. Please try again later."
2. **Rate Limit Exceeded**: "The outline service is temporarily busy. Please try again in a moment."
3. **Generic Failure**: "Failed to generate the course outline right now."
4. **Empty Response**: "The service returned an empty response."

---

## API Integration

### Endpoint
`POST /api/generate-outline`

### Request Body
```json
{
  "input": "string (required)",
  "type": "title | file (required)",
  "options": {
    "complianceStandard": "string (optional)",
    "additionalInfo": "string (optional)"
  }
}
```

### Response
```json
{
  "outline": "string (Markdown formatted course outline)"
}
```

---

## Environment Configuration

### Required Environment Variable
```bash
NAKSHA_GEMINI_API_KEY=your_api_key_here
```

### Optional Environment Variables
```bash
PORT=8890                    # Server port (default: 8890)
HOST=0.0.0.0                 # Server host (default: 0.0.0.0)
MAX_BODY_SIZE_BYTES=20971520 # Max request body size (default: 20MB)
CORS_ORIGIN=*                # CORS origin (default: *)
```

---

## Key Insights

### Why This Approach Works

1. **Single-Shot Prompting**: No complex conversation history or system messages—just one comprehensive, well-structured prompt
2. **Low Temperature**: Ensures deterministic, rule-following behavior with minimal hallucination
3. **Explicit Rules**: Numbered rules with bold headers make instructions impossible to miss
4. **Format Enforcement**: Critical formatting requirements are repeated and emphasized
5. **Example-Driven**: Concrete examples demonstrate the exact expected output format
6. **Compliance Focus**: Built-in expertise in US federal regulations and compliance standards

### Structural Differences

| Aspect | File Prompt | Title Prompt |
|--------|-------------|--------------|
| **Role** | Content structure analysis tool | Expert instructional designer |
| **Task** | Extract existing structure | Generate new structure |
| **Input** | Document content | Course title |
| **Emphasis** | EXACT wording extraction | Compliance & terminology |
| **Rules Format** | Numbered list (1-9) | Bullet points in IMPORTANT |
| **Config Block** | Continues Rule #9 | Separate bullet in IMPORTANT |

---

## Version Information

- **Document Date**: 2026-03-24
- **Source File**: `server/index.js`
- **AI Model**: `gemini-2.5-flash`
- **API**: Google GenAI

---

*This documentation preserves the exact prompt content and structure from the Naksha backend implementation.*
