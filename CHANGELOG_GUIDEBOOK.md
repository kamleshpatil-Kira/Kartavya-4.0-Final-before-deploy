# Project Changelog & Architecture Guidebook

This document tracks significant changes made to the "Kartavya-3.0 / Bhishma 2.0" application. It serves as a guide for developers to understand _what_ was changed in specific files and _why_ those design decisions were made.

---

## 1. Document Auto-fill Feature

**Date:** 2026-02-26
**Feature Goal:** Automatically extract key course metadata (Course Title, Target Audience, Institute, Relevant Laws) from uploaded documents to pre-fill the Course Generation form, saving user effort and ensuring context-accurate generation.

### Files Modified & Logic:

#### 1. `backend/services/gemini_service.py`

- **What changed:** Added a new method `analyze_document_metadata(self, text: str) -> Dict[str, str]`.
- **Logic / Why:**
  - We needed a dedicated prompts to instruct the Gemini AI to analyze raw document text and return highly structured JSON.
  - The prompt is strictly engineered to verify US federal and state laws, preventing the AI from hallucinating or referencing international laws.
  - We use a specific `generation_config` with a low `temperature` (0.2) and `response_mime_type: "application/json"` to ensure the AI behaves deterministically and always returns a parseable JSON object.

#### 2. `backend/main.py`

- **What changed:** Updated the `@app.post("/api/documents/process")` endpoint.
- **Logic / Why:**
  - Previously, this endpoint only read the raw text from the uploaded files using `DocumentProcessor`.
  - We injected the `GeminiService` here to take that raw text and pass it to our new `analyze_document_metadata` function.
  - Because `generate_content` is synchronous and can block the server, we wrapped the call in `await asyncio.to_thread(...)`. The AI-extracted metadata is then appended to the API response payload alongside the `processedDocuments` string.

#### 3. `frontend/app/page.tsx`

- **What changed:** Updated the `handleDocumentsUpload` function.
- **Logic / Why:**
  - The frontend needed to listen for the newly added `metadata` object in the API response.
  - Upon receiving the metadata, we use React's `setForm` state updater to overwrite the `courseTitle`, `targetAudience`, `institute`, and `relevantLaws` fields automatically.
  - We added fallback logic (`|| prev.courseTitle`) so that if the AI fails to extract a specific field, it preserves whatever the user might have already typed. A UI toast notification was also added to inform the user that their form was auto-filled.

---

## 2. Gemini Robustness & JSON Parsing Fixes

**Date:** 2026-02-27
**Feature Goal:** Fix `JSONDecodeError`s triggered when parsing non-English documents (like Marathi PDFs) that cause Gemini to hit token limits or return malformed JSON outputs.

### Files Modified & Logic:

#### 1. `backend/services/gemini_service.py`

- **What changed:** Updated the prompt inside `analyze_document_metadata` and increased `max_output_tokens` from `1024` to `8192`.
- **Logic / Why:**
  - Non-English documents consume significantly more tokens (sometimes up to 5x higher per character). This caused Gemini to silently truncate its output midway through, resulting in an "unterminated string" error during `json.loads`.
  - The model was also found to sometimes return `null` values or leave keys out entirely when data wasn't found in the text. We hardened the prompt to explicitly forbid `null` and enforce the return of empty strings `""` for any missing metadata. We also explicitly forbade the translation of JSON keys themselves into the target language.

#### 2. `test_gemini.py`

- **What changed:** Added an isolated debugging script.
- **Logic / Why:** To provide an offline, fast way to dump exactly what Gemini returned (including finish reasons like `MAX_TOKENS` and safety blocks) before it reached the backend parsing layers.

---

## 3. "Outline Only" UI/UX Distinction

**Date:** 2026-02-27
**Feature Goal:** When a user checks "Generate Outline Only," the Course Viewer should adapt its terminology and layout to reflect that an outline—not a fully narrated course—was generated.

### Files Modified & Logic:

#### 1. `frontend/app/view/page.tsx`

- **What changed:** Conditionally rendered texts based on an `isOutlineOnly` boolean flag logic.
- **Logic / Why:**
  - Previous behavior attempted to map over `courseData.course` and `courseData.modules`. Because "Outline Only" generation bypasses those keys and strictly returns `courseData.outline`, the View Course page appeared blank or showed "0 Modules".
  - We implemented fallback variables (`courseTitle = courseData?.course?.title || courseData?.outline?.courseTitle`) so the layout populates correctly from the outline object.
  - Dynamically altered component headings (e.g., "Course Viewer" -> "Outline Viewer", "Course Outline" -> "Generated Outline").
  - Dynamically hid the "Audio Settings" and "Downloads" components when `isOutlineOnly` is true, since these actions are unavailable until actual course generation takes place.
  - Reformatted the fallback "Course Outline" string format from a raw `JSON.stringify` codeblock into a clean, hierarchical mapped list of `Module X.Y` sections.

---

## 4. Antigravity Generation Loading Visuals

**Date:** 2026-02-27
**Feature Goal:** Enhance the user experience during long course generation waiting periods by displaying an interactive, high-fidelity 3D particle graphic in the background of the Status card.

### Files Modified & Logic:

#### 1. `frontend/components/Antigravity.tsx` [NEW]

- **What changed:** Created a self-contained 3D animation loop using `three` and `@react-three/fiber`.
- **Logic / Why:** Generates floating capsules that respond to mouse cursors. Uses internal `<instancedMesh>` techniques for performance over 300+ nodes.

#### 2. `frontend/app/page.tsx`

- **What changed:** Dynamically imported the `Antigravity` module (with `{ ssr: false }` to avoid SSR window errors). Added HTML/CSS absolute positioning wrappers within the `Generation Status` card.
- **Logic / Why:** Rendered fully invisibly unless the `isGenerating` state resolves to true.
