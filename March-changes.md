# Changelog: March Updates

## Task B-2: Number of Modules Validation (Min 1, Max 20)

**Why the change was made:**
The `Number of Modules` input on the frontend could be manipulated to send out-of-bounds numbers (such as 0 or 25), empty strings, or cause a frozen UI when a user attempts to backspace and enter a custom number. There was also a lack of server-side checks in the backend allowing malicious or malformed logic to bypass module generation limits. This could lead to infinite background tasks or API generation problems.

**Changes made:**

1. **Frontend Input Field Flexibility & Constraints:**
   - **File:** `frontend/app/components/wizard/StepCourseInfo.tsx`
   - **Lines:** ~142-160 (inside `StepCourseInfo` component)
   - **Change:**
     - Increased the HTML `max` attribute from `10` to `20`.
     - Modified the `onChange` handler to read `e.target.value` as text, rather than directly parsing to an integer. This avoids forcing the value to `NaN` (or instantly snapping to `1`) while the user presses "backspace" to delete the current number.
     - Added an `onBlur` event handler: when the user clicks away from the input (loses focus), the application evaluates the value. If it's empty or less than 1, it snaps to `1`. If it exceeds 20, it snaps back down to `20`.
     - Placed conditional UI feedback logic below the field to render a red warning (`<p>`) if the current text is temporarily out of range while they are interacting with it.

2. **Backend Server Verification - General Generation Loop:**
   - **File:** `services/course_generator.py`
   - **Lines:** ~252-258 (inside `_generate_full_course`)
   - **Change:** Updated the bounds for `requested_num_modules`. Before starting the loop to fetch Gemini modules, it validates the number passed in the `user_input` dictionary. If the value is `< 1`, it forces it to `1`, and if it's `> 20`, it forces it to `20`.

3. **Backend Server Verification - Regeneration Sequence Constraint:**
   - **File:** `services/course_generator.py`
   - **Lines:** ~167-171 (inside `_regenerate_from_existing`)
   - **Change:** Changed `user_input["numModules"] = detected_count` to use `user_input["numModules"] = max(1, min(20, detected_count))`. Originally, the regeneration mode mathematically bypassed all clamps by taking the literal `estimatedModuleCount` the AI discovered inside a document blueprint. Now, even if a document implies 50 modules, the system guarantees the ceiling remains 20.

4. **Prompt Instruction Bounds Control:**
   - **File:** `services/gemini_service.py`
   - **Lines:** ~741-747 (inside `_build_outline_prompt`)
   - **Change:** Hardcoded a min-max limiter `[1, 20]` for the explicit string injected into the Gemini prompt instructions. The AI relies heavily on this literal text prompt to establish its plan, and capping it strictly guarantees reliable structured AI response boundaries.

## Task B-3: Estimated Time Display (Dynamic Fallback)

**Why the change was made:**
The backend historically never generated an `estimatedTime` field directly onto module objects, meaning the UI defaulted to a static and unhelpful `"N/A"` display for every loaded module. To resolve this, a purely mathematical frontend-driven fallback was needed so users have immediate visibility into course duration expectations. When the backend later assumes responsibility for calculating this field, the UI naturally prefers the backend's explicit string.

**Changes made:**

1. **Dynamic Content Evaluator:**
   - **File:** `frontend/app/view/page.tsx`
   - **Lines:** ~241-269
   - **Change:** Injected an `estimateReadingTime(module)` function that gathers every sub-structure (HTML blocks, strings, concepts, scenario strings, summaries) directly off a module's content loop. It converts the text blocks into a single string to strip off explicit rich text HTML formatting tags via Regex, counts the pure length of words, divides this by a fast adult reading speed of ~200 WPM, and then formats it securely into an `X-Y min` duration string, acting as a fallback.

2. **Display Switchover:**
   - **File:** `frontend/app/view/page.tsx`
   - **Lines:** ~933
   - **Change:** Swapped the explicit `{module.estimatedTime || "N/A"}` line directly for a short-circuit switch that reads `{module.estimatedTime && module.estimatedTime !== "N/A" ? module.estimatedTime : estimateReadingTime(module)}`, bridging the frontend fallback directly over null fields or deprecated backend logic values.

## Task B-4: Course Outline Numbered Sections with Hierarchy and Jump Links

**Why the change was made:**
The `Course Overview` card previously contained no structured view of the actual course content (Modules > Sections > Concepts), displaying only the course title and a raw description. Users had no quick, deep, at-a-glance visualization of the structure without scrolling through the giant page manually.

**Changes made:**

1. **Deep Outline Tree Map:**
   - **File:** `frontend/app/view/page.tsx`
   - **Change:** Substituted the raw `Course Overview` card with a dynamic iterative mapping. For every Module, it loops exactly through its nested schema (`module -> module.content.sections -> section.concepts`).
   - Each level displays uniquely indented and explicitly numbered prefixes (`1`, `1.1`, `1.1.1` etc.) using custom flex gaps and accent theme variables correctly.

2. **Interactive DOM Links:**
   - **File:** `frontend/app/view/page.tsx`
   - **Change:** Added specific HTML `id={'module-' + mNum}` properties securely mapping to each generated module iteration further down the page. The newly constructed Course Outline elements function natively as smooth-scrolling `href` jump anchors directly binding to these module IDs, bypassing unnecessary user scrolling efforts.
   - It also integrates automatically with React Component state to instantly un-collapse target modules when clicked!

## Task B-6: Unified Expand/Collapse Behavior (Default to Collapsed)

**Why the change was made:**
Modules in the `page.tsx` course viewer natively started fully expanded. For a 20-module course, this rendered thousands of lines of text down the page, hurting performance and user experience. Meanwhile, a legacy component `ModuleCard.tsx` natively evaluated defaults to collapsed. To unify the design and drastically enhance UX, everything was converted to naturally default to collapsed and global controls were implemented.

**Changes made:**

1. **State Initialization Refactoring:**
   - **File:** `frontend/app/view/page.tsx`
   - **Change:** Substituted the strict default `{}` useState empty object with a `useEffect` initialization sweep hook running directly off the `modules` memo array. On the absolute first render cycle, it builds an index map toggling all valid initialized models to `true` (Collapsed = true). Further manual user clicks are perfectly preserved between backend `courseData` regeneration cycles due to checking if the map contains keys already.

2. **Global Expand/Collapse Toolkit:**
   - **File:** `frontend/app/view/page.tsx`
   - **Change:** Integrated a clean toolbar mapped above the rendered Module loop. Shows total modules count strings intelligently (`1 Module` vs `8 Modules`). Mapped dual "Expand All" and "Collapse All" button sets. Both buttons natively map `Object.fromEntries` overriding the entire `collapsedModules` dictionary recursively to `false` (expanded) or `true` (collapsed) in milliseconds with zero DOM thrashing.

3. **Legacy Component Standardization:**
   - **File:** `frontend/app/components/ModuleCard.tsx`
   - **Change:** Updated internal hooks (`useState(false)` -> `useState(true)`) so if this fallback component is strictly mounted elsewhere, it shares identical UX state values.

## Task B-5: xAPI Export Generator Flattening Bug Fix

**Why the change was made:**
When a user manually edited a module in the browser and clicked "Save Module", the `saveModule` loop blindly injected the raw nested ReactQuill HTML output into the `module.content.html` variable in the backend JSON database. Unfortunately, the Python backend xAPI PDF/ZIP exporter literally hard-halted its loop entirely if it ever encountered `.get("html")`, intentionally short-circuiting out of parsing structured concepts, nested audios, explicit jump locations, and interactive blocks, destroying the generated `.zip` file into a flat unstructured div loop.

This fix correctly forces the React save loop to evaluate if modern AI-generated structured `.sections` already exist. If they do, the manual "html" payload injection is strictly bypassed, protecting the xAPI exporter algorithm from short-circuiting down the line while successfully saving their interactive blocks!

**Changes made:**

1. **State Preservation Mapping:**
   - **File:** `frontend/app/view/page.tsx`
   - **Change:** Substituted the strict JSON schema spreading assignment `content: { ...module.content, html: cache.content }` completely for an Immediately Invoked Function Expression (IIFE) running `(() => { return object; })()`. It manually determines if `hasSections` evaluates to true via Array.isArray checks. If true, it returns the cloned object _without_ the `html: cache.content` variable injected, guaranteeing only the structured interactive block saves properly while ignoring the legacy raw HTML editor overwrite! Valid flat HTML saves are preserved perfectly for older pre-V3 generated courses.

2. **Inline Editor Warning Message:**
   - **File:** `frontend/app/view/page.tsx`
   - **Change:** Added a conditional rendering block within the `Module Content` editing area that checks if the active module contains structured `.sections`. If verified, it renders a bolded accent-colored disclaimer explicitly reminding the user: _"Note: This module has structured sections. Content body edits are for preview only — title, knowledge check, flashcards and interactive block changes will be saved."_ This directly mitigates any user confusion when flat DOM layout overrides are cleanly bypassed.

## Task B-5 Gap: Add New Interactive Block When None Exists

**Why the change was made:**
The Interactive Block editor (`{cache.interactiveBlock && (...)}`) only rendered when a block already existed on the module. If `cache.interactiveBlock` was `null`, there was zero UI to add one — users had no way to attach a new tabs, accordion, note, table, or flipcard block to a module that didn't already have one.

**Changes made:**

1. **State Variable for Type Selection:**
   - **File:** `frontend/app/view/page.tsx`
   - **Change:** Added `const [newIbType, setNewIbType] = useState<Record<number, string>>({})` — a map from `moduleNum` to the selected interactive block type. This follows the same pattern as `editModules` and `editCache` to avoid React hooks-in-loop violations.

2. **"Add Interactive Block" UI Panel:**
   - **File:** `frontend/app/view/page.tsx`
   - **Change:** Inserted a conditional `{!cache.interactiveBlock && (...)}` block directly after the existing IB editor's closing `)}` and before the Knowledge Check section. It renders a `<select>` dropdown with all 5 block types (tabs, accordion, note, table, flipcard), and an "Add Interactive Block" button. On click, it injects a pre-filled template object into `editCache` with valid default JSON structures matching the exact schemas already shown in the IB editor hint text. The existing IB editor then renders immediately for further customization.

## Task B-7: Drag-and-Drop Module Reorder (Native HTML5)

**Why the change was made:**
Modules were locked in their AI-generated order with no way to rearrange them. Users had to regenerate entire courses if they wanted to change the sequence. Installing `@dnd-kit` was deemed risky due to potential dependency conflicts with Next.js 16 / React 18.

**Changes made:**

1. **Drag State Variables:**
   - **File:** `frontend/app/view/page.tsx`
   - **Change:** Added `draggedModule` and `dragOverModule` state variables (`useState<number | null>(null)`) to track which module is being dragged and which is being hovered over.

2. **Reorder Function:**
   - **File:** `frontend/app/view/page.tsx`
   - **Change:** Added `reorderModules(fromNum, toNum)` function after `saveCourse`. It finds modules by `moduleNumber` (not array index), splices the array, and calls `saveCourse` with the new order. Safe because `collapsedModules`, `editCache`, and `editModules` are all keyed by `moduleNumber` (not index), and xAPI generator reads `module.moduleNumber` from the object itself.

3. **Module Card Drag Attributes:**
   - **File:** `frontend/app/view/page.tsx`
   - **Change:** Updated each module card `<div>` with `draggable`, `onDragStart`, `onDragOver` (with `e.preventDefault()`), `onDrop`, and `onDragEnd` handlers. Added a drag handle (`⠿`) icon to the left of the module number badge with `onClick={(e) => e.stopPropagation()}` so it doesn't accidentally toggle collapse. The card dynamically applies the `.drag-over` CSS class when it's a valid drop target.

4. **Visual Feedback CSS:**
   - **File:** `frontend/app/globals.css`
   - **Change:** Added `.module-card.drag-over` class with a dashed accent-colored outline and subtle background tint to clearly indicate the drop target during drag operations.
