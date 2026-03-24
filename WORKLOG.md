## Status (February 23, 2026)
- Frontend and backend running with FastAPI + Next.js.
- Background generation with job polling and progress.
- Auto-redirect to `/view` on completion.
- Stop Generation added (job cancel).
- Create New Course clears local state and reloads `/`.
- Exports (xAPI/JSON/PDF) shown after generation completes.
- TTS timeouts no longer fail generation; audio skips gracefully on timeout.

## UI Enhancements (February 23, 2026)
- Added top navigation bar with workspace context, status, and global actions.
- Global downloads dropdown (unlocked after generation completes).
- Global New Course action (clears state + redirects to `/`).
- Inline tooltips added to major form fields.
- Estimated generation time indicator added to the wizard.
- Refined input and button styling for smoother, more polished UI.
