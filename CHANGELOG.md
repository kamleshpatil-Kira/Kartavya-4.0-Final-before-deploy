# Changelog

## [2026-03-08] - Interactive Blocks Integration

### Added

- Multi-select interactive blocks UI to Step 2 of the course generation wizard (Tabs, Accordion, Note, Table, Flip Cards).
- Backend logic to assign and shuffle interactive block types cleanly across generated modules (1 per module initially).
- Gemini prompting logic to enforce strict JSON schemas for 5 unique interactive block types without breaking base content payload.
- Rich Interactive Blocks rendering directly into the xAPI/HTML outputs including custom CSS styles and layout.
- xAPI tracking events hooked securely to interactive blocks (`track_ib_module_x_type(id)`).
- Inline preview and raw JSON editing tools for Interactive Blocks within `frontend/app/view/page.tsx`, directly updating the editable module state.

### Fixed

- **Type Mismatch Resolution:** Intercepted strictly capitalized API outputs from Gemini via `type.toLowerCase()` resolving silent parsing fall-through bug rendering raw JSON.
- **Deep 3D Context Fixes (Flip Card):** Re-structured React keys, wrapper boundaries, CSS `backfaceVisibility: "hidden"`, `<motion.div>` inline `transformStyle: "preserve-3d"`, and `perspective: "1200px"` to allow rendering pipeline depth penetration resolving both flat rotation limits and front/back dual visibility mid-transition.
- **Data Destructive Overwrite:** Removed `sections: undefined` from module content `saveModule` fallback logic which irreversibly wiped out nested generation trees upon user text-edit completion.
- **Progress Bar Scaling Calculation:** Safely parsed percentage widths utilizing `Number(jobState.progress) || 0` ensuring zero-crash limits avoiding undefined CSS dimension injections.
- **Dead Component Clean-up:** Purged redundant 500-line `ModuleCard.tsx` architecture, centralizing `module.content.interactiveBlock` parsing, UX states, and deep clones securely inside the active Dashboard `page.tsx` UI payload.
- **QuizEditor SSR Runtime Crash:** Injected `"use client";` bounding execution safely to the App Router frontend mitigating Next.js evaluation hook errors.

### Changed (UX Enhancements)

- **Interactive Block JSON Schema Error Protection:** Active schema templates prepended to module editors indicating exact required boundaries with real-time `try / catch` UI border coloration preventing invalid state saves.
- **Note Icons Context Map:** Automatically renders `AlertTriangle`, `Lightbulb`, or generic `Info` bounding icons dynamically based on Note types (Important, Warning, Tip).
- **Interactive Block Scroll Overflow Support:** Activated webkit standards styling transparent `.custom-scrollbar` rules dynamically injected when Flipcard (back) payload data height exceeds constraints.
- **Ctrl+Enter / Cmd+Enter Hotkeys:** Configured core Module Content `textarea` DOM nodes to automatically intercept command execution triggering `saveModule()` functions instantly.
- **UI Element Rotational Mapping:** Reverted boolean tracking for `ChevronDown` module dropdowns pointing visually downward on collapse and up when fully expanded.
- **Flipcard Reverse Visuals:** Attached secondary text hint spans noting "Click to flip back" when the end-user achieves a 180° element limit natively matching internal user flows on `front` elements.

## [2026-03-01] - Wizard Streamline & Outline UX

### Changed

- Merged wizard Steps 2 (Course Information) and 3 (Content Options) — **wizard is now 4 steps** instead of 5.
- Stepper items now stretch equally across the full width.
- Enlarged mode selection cards for a premium desktop experience.
- Main content area expands to fill the viewport and centers vertically.

### Added

- Outline-only mode disables Flashcards and Quiz with a "Not applicable" notice.
- View page now reads title, description, and learning objectives from outline data.
- Outline displays as readable structured text (module titles + objectives) instead of raw JSON.
- Heading changes to "Outline Overview" for outline-only generated courses.

## [2026-02-23] - UI Enhancements

### Added

- Top navigation bar with workspace context, status, and global actions.
- Global downloads dropdown and New Course action.
- Tooltips for major input fields.
- Estimated generation time indicator.

### Updated

- Form input and button styling for smoother, more polished UI.

## [2026-02-09] - Fixes & Improvements

### Fixed

- **JSON Truncation Error:** Fixed "Unterminated string" error during quiz generation by increasing `max_output_tokens` to 8192 and enabling JSON mode in Gemini API calls.
- **Dependency Issues:** Removed incompatible `pyaudioop` package from `requirements.txt` to fix installation on Python 3.10.
- **Missing Module:** Restored missing `utils/` directory to fix `ModuleNotFoundError`.
- **Run Script:** Created `run.sh` for easy one-click startup on Linux.

### Added

- **MAINTENANCE.md:** added comprehensive guide for running and maintaining the project.
