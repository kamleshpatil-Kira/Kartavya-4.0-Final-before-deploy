# 🛠️ Developer CHANGELOG — Kartavya 3.0

> **What is this file?**
> This is the *developer-facing* changelog. Every time you make a change to this project — whether it's a UI tweak, a bug fix, a new feature, or a refactor — **write it here**. Include:
> - **What** changed (which file, which component, which line roughly)
> - **Why** you changed it (the reason / problem it solves)
> - **Who** changed it (your name / GitHub handle)
> - **When** (date)
>
> This helps future developers (including yourself!) understand the history and intent of every change without having to dig through Git commits.

---

## Template (copy-paste this for every change)

```
### [YYYY-MM-DD] — [Your Name / GitHub Handle]
**Type:** Bug Fix | Feature | UI Change | Refactor | Config | Docs
**Files Changed:** path/to/file.tsx, path/to/other.py
**What:** One line summary of the change.
**Why:** Why was this change necessary? What problem did it solve?
**Notes:** Any extra context, caveats, or things to be aware of.
```

---

## Change History

---

### [2026-03-02] — AI / Kamlesh Patil
**Type:** UI Change | Refactor
**Files Changed:** `frontend/app/globals.css`, `frontend/app/page.tsx`, `frontend/app/...` (Multiple)
**What:** Comprehensive Visual UI/UX Cleanup & Refactoring
**Why:** To significantly improve the visual polish, consistency, and premium feel of the platform interface.
**Notes:** 
- **Sidebar:** Added `lucide-react` icons and active state border indicators to sidebar navigation.
- **Generation UX:** Restructured the generation status card into a logical top-to-bottom hierarchy. Converted the vertical phase list to a horizontal, animated timeline symmetrically aligned with the progress bar. Upgraded the progress track to an animated striped gradient and added a dynamic "sonar ping" ripple/glow effect to the active timeline node. Grouped metadata badges (Progress, Status, ETA) cleanly below. Removed redundant nested banners and spinners.
- **Module Cards:** Abstracted into `<ModuleCard />`. Added "01, 02" numbering badges, left-edge visual accent strips, and collapsible expand/collapse toggles for cleaner reading.
- **Hero & Empty States:** Standardized the Hero (pill + H1 + description) across all 5 pages. Added friendly icons to History, Settings, and View Course empty states.
- **History Page:** Added inline delete buttons per course, added description snippets under titles, and aded a sort label.
- **Components:** Abstracted `<OutlineEditor />`, `<ModuleCard />`, and `<QuizEditor />` into their own clean components from the view page. Fixed visibility of `.notice.info` over the Aurora background.
- **Animations:** Added a subtle confetti celebration effect on successful full course generation.

### [2026-03-01] — Kamlesh Patil / kamleshpatil-Kira
**Type:** UI Fix
**Files Changed:** `frontend/app/globals.css` (`.card` class)
**What:** Changed `.card` background from `var(--bg-alt)` to `rgba(255,255,255,0.95)` with `backdrop-filter: blur(8px)`.
**Why:** Cards were semi-transparent against the Aurora WebGL canvas background, making text hard to read during generation and on Step 1. Now all cards have a near-opaque frosted glass look that's always readable.
**Notes:** `.card.surface` already had correct background — only `.card` needed the fix.

### [2026-03-01] — Kamlesh Patil / kamleshpatil-Kira
**Type:** Bug Fix
**Files Changed:** `backend/main.py` (`save_course_to_history()`)
**What:** Added fallback to `outline.courseTitle` when resolving the course title for history entries.
**Why:** Outline-only courses store their title in `courseData.outline.courseTitle`, not in `courseData.course.title` (which doesn't exist). This caused all outline-only courses to show as "Unknown" in Course History.
**Notes:** The fix checks `outline.courseTitle` only when the existing checks return "Unknown" or empty.

### [2026-03-01] — Kamlesh Patil / kamleshpatil-Kira
**Type:** UX Improvement
**Files Changed:** `frontend/app/page.tsx`
**What:** Replaced the raw JSON dump after outline-only generation with a clean success card including "View Outline" and "Start New Course" buttons. Added `useRouter` import and `startNewCourse` from context.
**Why:** The JSON output was overwhelming and unhelpful. Users just need confirmation it worked and a clear next step.
**Notes:** The raw JSON is still fully accessible via the View Course → Course Outline section.

### [2026-03-01] — Kamlesh Patil / kamleshpatil-Kira
**Type:** Feature
**Files Changed:** `frontend/app/view/page.tsx`
**What:** Added full inline editing for outline-only courses on the View Course page. Users can now click "Edit" on the Course Outline section to edit Course Title, Course Description, and all Module Titles and Learning Objectives. Supports adding/removing objectives per module.
**Why:** Previously there was no way to edit an outline after generation — users were stuck with what the AI produced.
**Notes:** Uses the existing `/api/course/save` endpoint. Edits are written to `courseData.outline` and saved.

### [2026-03-01] — Kamlesh Patil / kamleshpatil-Kira
**Type:** UX Improvement
**Files Changed:** `frontend/app/view/page.tsx`
**What:** Added Enter-to-save on all single-line edit inputs (Outline title, outline module titles, learning objectives, module title in module editor). Added "💡 Press Enter to save" hint next to the Edit button when in editing mode.
**Why:** Requiring a click on a Save button for every small change is inefficient. Enter-to-save is a standard power-user UX pattern. The hint makes it discoverable.
**Notes:** Not applied to `<textarea>` elements (module content) where Enter inserts a newline.

### [2026-03-01] — Kamlesh Patil / kamleshpatil-Kira
**Type:** UI Improvement
**Files Changed:** `frontend/app/history/page.tsx`
**What:** Added "Outline Only" badge on History cards for courses with 0 modules. Changed fallback title from "Untitled Course" to "Untitled".
**Why:** Users couldn't distinguish outline-only entries from failed / incomplete full course generations in the history list.
**Notes:** Badge uses the existing `.badge` CSS class at 0.7rem for a subtle indicator.

---

### [2026-03-01] — Kamlesh Patil / kamleshpatil-Kira
**Type:** UI Change
**Files Changed:** `frontend/app/globals.css` (`.main` class)
**What:** Centered the main content area vertically and horizontally, removed `max-width` constraint.
**Why:** The form cards were too narrow and pushed to the top with excessive empty space below. Added `flex: 1`, `justify-content: center`, and removed `max-width` so the wizard fills the viewport properly on desktop.
**Notes:** Side padding kept at 56px for comfortable breathing room.

### [2026-03-01] — Kamlesh Patil / kamleshpatil-Kira
**Type:** UI Change
**Files Changed:** `frontend/app/globals.css` (`.step` class)
**What:** Made stepper items stretch equally across the full width using `flex: 1`.
**Why:** After step 05 there was excessive empty whitespace on the right. Now all steps take equal horizontal space and are centered within their pill.
**Notes:** Also added `justify-content: center` to `.step` for text alignment.

### [2026-03-01] — Kamlesh Patil / kamleshpatil-Kira
**Type:** UI Change
**Files Changed:** `frontend/app/globals.css` (`.choice-card`, `.choice-grid`, `.choice-title`)
**What:** Increased size and visual appeal of the three mode selection cards (Start from Scratch, Regenerate, Edit).
**Why:** Cards were too small and tight for a desktop experience. Increased padding to `24px 22px`, added `min-height: 120px`, bumped font size, increased gap to `20px`, and deepened hover/active shadows for a premium feel.
**Notes:** None.

### [2026-03-01] — Kamlesh Patil / kamleshpatil-Kira
**Type:** Feature / UI Change
**Files Changed:** `frontend/app/page.tsx` (step array, JSX, validation, navigation)
**What:** Merged Step 3 (Content Options) into Step 2 (Course Information). Wizard now has **4 steps** instead of 5.
**Why:** Content Options (Learning Aids + Generation Scope) logically belongs with Course Information — it was splitting a closely related form into unnecessary extra steps. Combining them reduces clicks and simplifies the flow.
**Notes:** Steps array reduced from 5 to 4. All step conditions renumbered: old Step 4 (Audio) → Step 3, old Step 5 (Review) → Step 4. Navigation limits updated from 5 to 4. Validation logic updated accordingly.

### [2026-03-01] — Kamlesh Patil / kamleshpatil-Kira
**Type:** Feature / UX Improvement
**Files Changed:** `frontend/app/page.tsx` (Learning Aids section)
**What:** Flashcards and Final Quiz toggles are grayed out and disabled when "Generate Outline Only" is set to Yes.
**Why:** Outline-only generation doesn't produce modules, so flashcards and quizzes are not applicable. Disabling them prevents user confusion and invalid configurations.
**Notes:** Uses `opacity: 0.45` and `pointerEvents: 'none'` with an italic notice: "Not applicable for outline-only generation."

### [2026-03-01] — Kamlesh Patil / kamleshpatil-Kira
**Type:** Bug Fix / UX Improvement
**Files Changed:** `frontend/app/view/page.tsx` (Course Overview section, Outline display)
**What:** Fixed missing title and description on the View Course page when displaying outline-only results. Changed heading to "Outline Overview" for outline-only courses. Replaced raw JSON outline display with human-readable structured text.
**Why:** When outline-only generation completes, `courseData.course.title` was empty — the title and description were only inside `courseData.outline`. The JSON dump was also hard to read. Now the view page falls back to `outline.courseTitle` / `outline.courseDescription`, shows module names with learning objectives as bulleted lists, and changes the heading dynamically.
**Notes:** Falls back to formatted JSON `<pre>` only if the outline structure is unexpected (no `modules` array).

---

### [2026-02-27] — Kamlesh Patil / kamleshpatil-Kira
**Type:** UI Change / Feature
**Files Changed:** `frontend/app/globals.css` (lines ~37-44 modified, Aurora CSS removed), `frontend/app/layout.tsx` (lines ~16-20), `frontend/app/components/Aurora.tsx` (created), `frontend/package.json` (added `ogl`)
**What:** Centered the main application layout and implemented the official React Bits WebGL Aurora background.
**Why:** The `.main` container previously had a max width of 1200px which caused excessive whitespace on the right side on larger monitors. By reducing it to `860px`, the form cards now sit perfectly in the center of the viewport, creating a much more focused tool aesthetic. For the background, we initially tried a pure CSS approach, but per the user's request, we swapped it out for the stunning WebGL `<Aurora />` component from React Bits. This utilizes the `ogl` rendering engine to paint a dynamic, fluid mesh of our Kartavya brand colors (Deep Blue, Light Blue, Warm Orange) directly onto a background `<canvas>`, giving a completely premium, next-generation feel.
**Notes:** Added `"use client";` to `Aurora.tsx` as it utilizes `useEffect` hooks for the WebGL loop.

### [2026-02-27] — Kamlesh Patil / kamleshpatil-Kira
**Type:** UI Change / Feature
**Files Changed:** `frontend/app/page.tsx` (lines ~90, ~460)
**What:** Made the "Institute / Organization" input field in Step 2 entirely optional.
**Why:** Users don't always have a strict branding or client name they need to inject into the course. Forcing this text field prevented users from proceeding. It is now optional, meaning the "Next" button activates without it, and the UI label specifically says `(Optional)` instead of requiring an asterisk.
**Notes:** The backend `course_generator.py` handles the `institute` field dynamically; if left blank, it simply doesn't heavily brand the generated text.

### [2026-02-27] — Kamlesh Patil / kamleshpatil-Kira
**Type:** Refactor / Feature Archival
**Files Changed:** `frontend/app/page.tsx` (lines ~47, 114-146, 460-489 deleted), `DEV_SPEED_PRESETS_ARCHIVE.md` (created)
**What:** Completely removed the "Generation Speed" presets section (Fast/Balanced/Full) and extracted its logic into an archive markdown file.
**Why:** The UI element was commented out, leaving dead code in `page.tsx` (`preset` state, `applyPreset` logic, and the JSX block). To keep the component clean while preserving the logic for potential future use, we moved the feature code into `DEV_SPEED_PRESETS_ARCHIVE.md`.
**Notes:** 

### [2026-02-27] — Kamlesh Patil / kamleshpatil-Kira
**Type:** UI Change
**Files Changed:** `frontend/app/globals.css` (lines ~660-672)
**What:** Updated the `.step` and `.step.active` CSS classes in the stepper menu to visually dim inactive steps and add attractive hover physics.
**Why:** Previously, all steps in the top navigation stepper had high contrast and no interactive feel, making it harder to distinguish the current step at a glance. We added `opacity: 0.5` to dull inactive steps. We also added sleek `:hover` states with `transform: translateY` and elevated `box-shadow` to make the steps feel tactile and premium when moused over. This improves user focus and introduces satisfying micro-interactions during the multi-step form process.
**Notes:** 


### [2026-02-27] — Kamlesh Patil / kamleshpatil-Kira
**Type:** UI Change
**Files Changed:** `frontend/app/page.tsx` (lines ~341–356 deleted)
**What:** Removed the entire `<div className="card hero">` block from the main Course Generation page — the full hero card including the KARTAVYA pill, "AI Course Generation" heading, description text, and the "Current step" panel.
**Why:** The hero card took up significant vertical space at the top of the page without adding functional value. Removing it means users land directly on the step navigation and form — a cleaner, more focused UX.
**Notes:** First, only the badge spans (`Wizard` and `Client-ready exports`) were removed from inside the panel — the hero card itself was still rendering. The user identified that the card itself was the issue. The full card was then commented out by the user and the comment block was deleted to leave clean code. The `.hero` CSS class and `.hero-pill` class still exist in `globals.css` — they are safe to delete from CSS too if desired.


---

### [2026-02-26] — Kamlesh Patil / kamleshpatil-Kira
**Type:** Bug Fix
**Files Changed:** `frontend/app/context/CourseContext.tsx`
**What:** Fixed an infinite polling loop that was sending excessive GET requests to the backend jobs endpoint.
**Why:** The polling interval was not being cleared properly when the job completed or the component unmounted. This caused the browser to keep sending requests even after generation finished, flooding the server with unnecessary traffic.
**Notes:** After the fix, polling stops as soon as the job reaches `completed`, `failed`, or `cancelled` state. The fix uses a `useRef` to store the interval ID and clears it with `clearInterval` inside the effect cleanup and state-change handlers.

---

### [2026-02-25] — Kamlesh Patil / kamleshpatil-Kira
**Type:** Config / Bug Fix
**Files Changed:** `.env`, `/etc/environment`
**What:** Fixed the GEMINI_API_KEY not being picked up by the application.
**Why:** The key in `/etc/environment` was misspelled as `GEMiNI_API_KEY` (lowercase `i`). Created a `.env` file in the project root with the correctly spelled `GEMINI_API_KEY` as a local fallback.
**Notes:** For Docker deployments, the `docker-compose.prod.yml` reads this key from the host environment. Make sure `/etc/environment` is correctly set before deploying with Docker. Run `set -a; source /etc/environment; set +a` after editing `/etc/environment` to export the variable into the current shell.

---

### [2026-02-25] — Kamlesh Patil / kamleshpatil-Kira
**Type:** Bug Fix
**Files Changed:** `generators/xapi_generator.py` (the generated `script.js` output)
**What:** Fixed `sendXAPIStatement()` — the ADL wrapper `.sendStatement()` call was commented out, meaning all xAPI statements were built but never actually sent to the LRS.
**Why:** Without this fix, all course interactions (quiz results, module views, certificate completions) were invisible in the emPower LMS xAPI Report. The statements were constructed correctly but never transmitted.
**Notes:** Both `sendStatement()` (used for module/audio/image events) and `sendXAPIStatement()` (used for quiz and course completion events) are now active. Wrapped the call in a try/catch for resilience. Re-generate any courses that were created before this fix — old ZIPs contain the broken `script.js`.

---

### [2026-02-25] — Kamlesh Patil / kamleshpatil-Kira
**Type:** Feature
**Files Changed:** `frontend/app/page.tsx`, `frontend/app/globals.css`
**What:** Added per-step progress indicator (stepper) and generation phase tracker to the main course wizard UI.
**Why:** Users had no visibility into which AI processing stage was running during course generation. The phase tracker (Queued → Outline → Modules → Quiz & Packaging → Finalizing) gives live feedback, reducing perceived wait time.
**Notes:** The phase index is derived from the `jobState.message` string using keyword matching (`outline`, `module`, `quiz`, `xapi`, `final`). If the backend message wording changes in `course_generator.py`, update the phase matching logic in `page.tsx` accordingly.

---

### [2026-02-23] — Kamlesh Patil / kamleshpatil-Kira
**Type:** Bug Fix
**Files Changed:** `frontend/app/lib/api.ts`, `frontend/app/api/[...path]/route.ts`
**What:** Fixed "Failed to save quiz" error caused by CORS preflight failures on cross-origin API calls.
**Why:** The frontend (port 3000) was making direct fetch calls to the backend (port 8000), which browsers block unless CORS headers are correct. The fix routes all API calls through the Next.js proxy (`/api/[...path]`) instead of directly hitting the backend.
**Notes:** All frontend API calls must use the `apiFetch` / `apiFetchBlob` utility from `lib/api.ts`, which automatically routes through the Next.js proxy. Do not use raw `fetch('http://localhost:8000/...')` directly in components.

---

### [2026-02-20] — Kamlesh Patil / kamleshpatil-Kira
**Type:** Feature / UI Change
**Files Changed:** `frontend/app/globals.css`
**What:** Migrated the frontend UI to a Claymorphism design language.
**Why:** The previous flat UI design looked generic and didn't reflect the premium quality of the AI output. Claymorphism adds soft shadows, rounded edges, and a tactile feel without reducing usability.
**Notes:** All layout and component logic was preserved — this was a CSS-only change. The key new classes are `card`, `card.hero`, `card.surface`, `badge`, `pill`, `chip`, `chip.active`, `toggle-button`, `toggle-group`, `choice-card`, `section-card`. Avoid ad-hoc inline styles; use these classes instead.

---

## How to Contribute Changes

1. Make your code change.
2. Open this file (`DEVCHANGELOG.md`).
3. Copy the template at the top and fill it in **honestly and completely**.
4. Commit both your code change and the DEVCHANGELOG update together.

> **Tip for future developers:** If you're cloning this repo and want to understand what was changed from the original Kartavya 2.x (Streamlit) version, read this file top-to-bottom and also check `CHANGELOG.md` for the product-level release notes.
### [2026-03-02] — Kamlesh Patil / kamleshpatil-Kira
**Type:** Refactor
**Files Changed:** `frontend/app/view/page.tsx`, `frontend/app/components/*`
**What:** Extracted view page sub-components (OutlineEditor, ModuleCard, QuizEditor).
**Why:** `frontend/app/view/page.tsx` was overly complex. By extracting these, we greatly reduced line count and encapsulated their specific logic.
**Notes:** Existing logic preserved.

### [2026-03-03] — Kamlesh Patil / kamleshpatil-Kira
**Type:** Refactor
**Files Changed:** `frontend/app/page.tsx`, `frontend/app/components/wizard/*`
**What:** Split monolithic generation wizard into dedicated step components.
**Why:** `page.tsx` had grown to 1330 lines and was getting unmaintainable. Extracted into 4 components (`StepGenerationMode`, `StepCourseInfo`, `StepAudioMedia`, `StepConfirm`), turning `page.tsx` into a lean ~310-line view orchestrator.
**Notes:** Passed comprehensive TypeScript zero-error checks.

### [2026-03-03] — Kamlesh Patil / kamleshpatil-Kira
**Type:** Refactor
**Files Changed:** `backend/main.py`, `backend/routes/history.py`, `backend/routes/state.py`
**What:** Extracted history API routes from `main.py` into a modular router.
**Why:** To begin reducing `main.py` bloat safely. Kept volatile shared globals in `state.py` to prevent cyclic import loops while extracting the clean `GET / DELETE` history endpoints.
**Notes:** Backend functionality remains exactly the same, zero breaking changes.

### [2026-03-03] — Kamlesh Patil / kamleshpatil-Kira
**Type:** UI Polish
**Files Changed:** `frontend/app/globals.css`, `frontend/app/history/page.tsx`
**What:** Added spring-bounce UI animations to setting chips and improved History empty state.
**Why:** Enhances the premium, tactile feel of the wizard form interactions using `cubic-bezier` scaling. Added a "Create First Course" CTA button strictly for empty history flows.
**Notes:** None.

