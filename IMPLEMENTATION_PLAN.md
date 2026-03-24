# Kartavya 3.0 — Implementation Plan
## Team Division: 2-Person Git Collaboration Strategy

> **Goal:** Implement all required changes with zero merge conflicts by ensuring each team member works on completely separate files.
> **Branch Strategy:** `feature/member-A-changes` and `feature/member-B-changes` → merge to `main` sequentially (A first, then B rebases on A).

---

## Team Assignment Overview

| Member | Domain | Files Touched |
|--------|--------|--------------|
| **Member A** | xAPI / Completion Tracking / Backend Generator | `generators/xapi_generator.py`, `services/course_generator.py` |
| **Member B** | Frontend UI / Editor / Course Structure | `frontend/app/view/page.tsx`, `frontend/app/components/wizard/StepCourseInfo.tsx`, `frontend/app/components/QuizEditor.tsx` |

> **Zero overlap guaranteed** — Members A and B touch completely different files.

---

## MEMBER A TASKS (Backend / xAPI / Generator)

**Branch:** `feature/member-a-backend-xapi`
**Files:** `generators/xapi_generator.py`, `services/course_generator.py`

---

### A-1 · Knowledge Check: Remove Radio Buttons (Improve UI)

**File:** `generators/xapi_generator.py`
**Location:** `_build_knowledge_check_html()` method (around line 2025-2072)

**What to change:**
- Replace `<input type="radio">` elements with styled clickable **button cards** (one per option)
- Each option becomes a pill/card button: clicking it visually selects it (adds CSS class `selected`)
- Remove the separate "Submit" button — clicking an option triggers immediate evaluation
- Remove the lock/disabled logic tied to audio (or keep unlock logic but apply it to buttons)

**Before pattern (radio input rendering):**
```python
f'<input type="radio" name="kc-{module_num}" value="{key}" onchange="onKCOptionSelected({module_num})" {radio_disabled}>'
```

**After pattern (button card rendering):**
```python
f'<button class="kc-option-btn" id="kc-{module_num}-{key}" onclick="selectKCOption({module_num}, \'{key}\')" {btn_disabled}>'
f'  <span class="kc-option-label">{key}</span>'
f'  <span class="kc-option-text">{label_text}</span>'
f'</button>'
```

**JavaScript to update:**
- `onKCOptionSelected(moduleNum)` → replace with `selectKCOption(moduleNum, key)` that immediately calls `checkKnowledgeCheck`
- Remove separate `submitKnowledgeCheck()` function
- Add CSS for `.kc-option-btn`, `.kc-option-btn.selected`, `.kc-option-btn.correct`, `.kc-option-btn.incorrect`

---

### A-2 · Knowledge Check: Fix Correct Answer (Always A)

**File:** `generators/xapi_generator.py`
**Location:** `checkKnowledgeCheck()` JavaScript function (around line 6739-6755)

**What to change:**
- In the xAPI exported HTML, the `correctAnswer` field from the course JSON is used to check answers
- Bug: The check may be case-sensitive or comparing wrong values
- Fix: Normalize both sides — `selectedAnswer.toUpperCase() === knowledgeCheck.correctAnswer.toUpperCase()`
- Also verify in `_build_knowledge_check_html()` that `correctAnswer` is passed correctly into the JS data object

**Before:**
```javascript
if (selectedAnswer === knowledgeCheck.correctAnswer) {
```

**After:**
```javascript
if (selectedAnswer && selectedAnswer.toUpperCase() === (knowledgeCheck.correctAnswer || "").toUpperCase()) {
```

---

### A-3 · xAPI: Skip Quiz in Tracking When No Quiz Exists + Fix Completion %

**File:** `generators/xapi_generator.py`
**Location:** `generate_package()` method and completion calculation JavaScript

**Problem:** Without a quiz, course shows 65% even when all modules are complete. The 65% is because the completion formula counts quiz as a required component even when absent.

**What to change:**

**Part 1 — TinCan XML:** Do not include quiz activity in `tincan.xml` if `course.get('quiz')` is None or empty:
```python
# In _generate_tincan_xml()
if course_data.get('quiz') and course_data['quiz'].get('questions'):
    # Add quiz activity to manifest
    ...
```

**Part 2 — Completion JS:** The `checkCourseCompletion()` JavaScript function must calculate percentage dynamically based on what actually exists:
```javascript
function checkCourseCompletion() {
    const hasQuiz = {{ 'true' if has_quiz else 'false' }};
    const totalModules = {{ total_modules }};

    let completedComponents = 0;
    let totalComponents = totalModules;  // each module = 1 component
    if (hasQuiz) totalComponents += 1;   // quiz = 1 more component

    for (let m = 1; m <= totalModules; m++) {
        if (moduleCompleted[m]) completedComponents++;
    }
    if (hasQuiz && quizCompleted) completedComponents++;

    const pct = Math.round((completedComponents / totalComponents) * 100);
    updateCompletionBar(pct);
    if (pct >= 100) markCourseComplete();
}
```

**Part 3 — Backend generation:** In `generate_package()`, pass `has_quiz` flag into HTML template:
```python
has_quiz = bool(course_data.get('quiz') and course_data['quiz'].get('questions'))
```

---

### A-4 · Fix Course Completion Tracking (NavBar + Overall 100%)

**File:** `generators/xapi_generator.py`
**Location:** NavBar completion display + `markCourseComplete()` JS function

**Problem:** Even when all modules are done, NavBar doesn't show 100% completed.

**What to change:**
- Find the NavBar/progress bar HTML element rendering (search for `progress` or `navbar` in xapi_generator.py)
- Ensure `updateCompletionBar(pct)` updates the NavBar element's width and text
- Ensure `markCourseComplete()` sends the xAPI `completed` statement AND updates NavBar to 100%
- Fix the formula: completion = (modules done + quiz done if quiz exists) / (total modules + 1 if quiz exists)

**Key JS fix pattern:**
```javascript
function markCourseComplete() {
    document.getElementById('completion-pct').textContent = '100%';
    document.getElementById('completion-bar').style.width = '100%';
    // Send xAPI completed statement
    sendStatement('completed', courseId, courseTitle);
}
```

---

### A-5 · Fix Estimated Time: N/A → Proper Module-wise Time

**File:** `services/course_generator.py`
**Location:** `_generate_single_module()` method

**Problem:** `module.estimatedTime` is not being set during generation, so frontend shows "N/A".

**What to change:**
- After generating module content, calculate estimated reading time based on word count
- Formula: average reading speed = 200 words/min; narration = 130 words/min
- Set `estimatedTime` field on each module

```python
# After module content is generated
content_text = extract_plain_text(module_content)  # strip HTML
word_count = len(content_text.split())
reading_min = max(1, round(word_count / 200))
narration_min = max(1, round(word_count / 130)) if has_audio else 0
total_min = reading_min + narration_min
# Format: "X-Y minutes"
lo = max(1, total_min - 1)
hi = total_min + 2
module_data['estimatedTime'] = f"{lo}-{hi} minutes"
```

Also update the course-level `estimatedTime` to be sum of all modules:
```python
total_lo = sum(parse_time_lo(m['estimatedTime']) for m in modules)
total_hi = sum(parse_time_hi(m['estimatedTime']) for m in modules)
course_data['course']['estimatedTime'] = f"{total_lo}-{total_hi} minutes"
```

---

## MEMBER B TASKS (Frontend UI / Editor)

**Branch:** `feature/member-b-frontend-ui`
**Files:** `frontend/app/view/page.tsx`, `frontend/app/components/wizard/StepCourseInfo.tsx`

---

### B-1 · Remove Flashcards from Learning Aids (Keep Only Flipcards)

**File:** `frontend/app/components/wizard/StepCourseInfo.tsx`
**Location:** Learning Aids Section (around lines 183-300)

**Problem:** Flashcards (per-module auto-generated cards) and Flipcards (interactive block type) are the same concept shown twice.

**What to change:**
- Find the `generateFlashcards` / `includeFlashcards` checkbox/toggle in the Learning Aids section
- Remove it from the UI (comment it out or delete the JSX block)
- Keep the Flip Cards option in the Interactive Blocks multi-select (it stays)
- If there's a `formData.generateFlashcards` field, either keep it as a hidden default `false` or ensure backend handles its absence

**Specific change:**
```tsx
// REMOVE this block (or similar):
<div className="learning-aid-option">
  <input type="checkbox" name="generateFlashcards" ... />
  <label>Flashcards</label>
  <span className="hint">Key term flip cards per module</span>
</div>
```

---

### B-2 · Number of Modules: Validation (Min 1, Max 20)

**File:** `frontend/app/components/wizard/StepCourseInfo.tsx`
**Location:** Module count input (around lines 116-179, Tone & Structure section)

**What to change:**
- Find the `numModules` input field
- Add `min={1}` and `max={20}` HTML attributes
- Add validation: if user inputs 0 or negative → force to 1; if > 20 → force to 20
- Show inline error message: "Number of modules must be between 1 and 20"
- Change the `onChange` handler to clamp the value

```tsx
// Change input to:
<input
  type="number"
  name="numModules"
  min={1}
  max={20}
  value={formData.numModules}
  onChange={(e) => {
    const val = parseInt(e.target.value, 10);
    const clamped = isNaN(val) ? 1 : Math.min(20, Math.max(1, val));
    setFormData(prev => ({ ...prev, numModules: clamped }));
  }}
/>
{(formData.numModules < 1 || formData.numModules > 20) && (
  <p className="text-red-500 text-sm">Modules must be between 1 and 20</p>
)}
```

---

### B-3 · Estimated Time Display: Map Course-Level Total + Module-wise Times

**File:** `frontend/app/view/page.tsx`
**Location:** Line 933 — `<p><strong>Estimated Time:</strong> {module.estimatedTime || "N/A"}</p>`

**What to change:**
- Remove the `|| "N/A"` fallback — if estimatedTime is missing, calculate it inline from content length
- Add a course-level estimated time display in the Course Overview section (above modules)
- Show module-level estimated time under each module header (not "N/A")

**Module-level fix (inline fallback calculation):**
```tsx
// Helper function (add near top of component):
function estimateReadingTime(text: string): string {
  const words = text.replace(/<[^>]+>/g, '').split(/\s+/).filter(Boolean).length;
  const mins = Math.max(1, Math.round(words / 200));
  return `${mins}-${mins + 2} minutes`;
}

// In module render (replace line 933):
<p>
  <strong>Estimated Time:</strong>{' '}
  {module.estimatedTime && module.estimatedTime !== 'N/A'
    ? module.estimatedTime
    : estimateReadingTime(
        module.content?.sections?.map(s => s.content).join(' ') ||
        module.content?.html || ''
      )
  }
</p>
```

**Course-level total (add in Course Overview section around line 616-634):**
```tsx
{/* Course total estimated time */}
{modules && modules.length > 0 && (
  <p className="text-sm text-gray-500">
    <strong>Total Estimated Time:</strong>{' '}
    {courseData?.course?.estimatedTime || calculateTotalTime(modules)}
  </p>
)}
```

---

### B-4 · Course Outline: Format as 1.1, 1.2, 1.3 per Module

**File:** `frontend/app/view/page.tsx`
**Location:** Course Overview / Outline section (around lines 615-645)
Also: `frontend/app/components/OutlineEditor.tsx` if outline is displayed there

**What to change:**
- In the Course Overview section, when listing module sections, format them as `1.1 [Section Title]`, `1.2 [Section Title]` etc.
- Currently sections inside a module may not be numbered
- Add a nested list under each module header showing numbered sections

```tsx
{/* In Course Overview / module listing: */}
{modules.map((module, mIdx) => (
  <div key={mIdx} className="outline-module">
    <p className="font-semibold">
      Module {module.moduleNumber || mIdx + 1}: {module.moduleTitle}
    </p>
    {module.content?.sections && (
      <ul className="ml-4 text-sm text-gray-600">
        {module.content.sections.map((section, sIdx) => (
          <li key={sIdx}>
            {module.moduleNumber || mIdx + 1}.{sIdx + 1} {section.sectionTitle}
          </li>
        ))}
      </ul>
    )}
  </div>
))}
```

---

### B-5 · CRUD for Interactives: Full Inline Editing + Create New

**File:** `frontend/app/view/page.tsx`
**Location:** Interactive block section in module editor (around lines 730-769)

**What to change:**
Currently only raw JSON editing exists. Add proper CRUD UI:

**CREATE** — Add "Add Interactive Block" button when `interactiveBlock` is null:
```tsx
{!cache.interactiveBlock && (
  <div className="flex gap-2">
    <p className="text-sm text-gray-500">No interactive block</p>
    <select onChange={(e) => addInteractiveBlock(moduleNum, e.target.value)}>
      <option value="">+ Add Interactive Block</option>
      <option value="tabs">Tabs</option>
      <option value="accordion">Accordion</option>
      <option value="note">Callout Note</option>
      <option value="table">Table</option>
      <option value="flipcard">Flip Cards</option>
    </select>
  </div>
)}
```

With `addInteractiveBlock()` creating a default skeleton:
```tsx
const defaultBlocks = {
  tabs: { type: "tabs", data: { tabs: [{ title: "Tab 1", content: "Content here" }] } },
  accordion: { type: "accordion", data: { items: [{ question: "Q?", answer: "A." }] } },
  note: { type: "note", data: { variant: "tip", text: "Your note here" } },
  table: { type: "table", data: { headers: ["Col 1", "Col 2"], rows: [["Cell 1", "Cell 2"]] } },
  flipcard: { type: "flipcard", data: { cards: [{ front: "Term", back: "Definition" }] } },
};
```

**READ** — Already works via `InteractiveBlockPreview` component

**UPDATE** — Replace raw JSON textarea with structured form editors per type:
- **Tabs editor:** List of `{ title, content }` pairs with add/remove buttons
- **Accordion editor:** List of `{ question, answer }` pairs with add/remove buttons
- **Note editor:** Variant dropdown + text input
- **Table editor:** Header row inputs + add/remove rows/columns
- **Flipcard editor:** List of `{ front, back }` pairs with add/remove buttons

Each field renders as an inline editable text input (no JSON textarea needed).

**DELETE** — Keep existing "Remove Block" button

---

### B-6 · Module Header: Expand All / Collapse All + Default Collapsed

**File:** `frontend/app/view/page.tsx`
**Location:** Module section header / toolbar area (around lines 260-264 and wherever modules are mapped)

**What to change:**

**Part 1 — Default collapsed:**
Change `useState<Record<number, boolean>>({})` initial state so all modules start collapsed:
```tsx
// After modules are loaded, initialize all as collapsed:
const [collapsedModules, setCollapsedModules] = useState<Record<number, boolean>>(() => {
  const initial: Record<number, boolean> = {};
  // Will be populated via useEffect when modules load
  return initial;
});

useEffect(() => {
  if (modules && modules.length > 0) {
    const initial: Record<number, boolean> = {};
    modules.forEach(m => {
      const num = m.moduleNumber || 1;
      initial[num] = true; // true = collapsed
    });
    setCollapsedModules(initial);
  }
}, [modules?.length]); // Only on initial load
```

**Part 2 — Expand All / Collapse All buttons:**
Add these buttons above the module list (in the toolbar/header area):
```tsx
<div className="flex gap-2 mb-4">
  <button
    onClick={() => {
      const all: Record<number, boolean> = {};
      modules.forEach(m => { all[m.moduleNumber || 1] = false; }); // false = expanded
      setCollapsedModules(all);
    }}
    className="text-sm px-3 py-1 border rounded hover:bg-gray-50"
  >
    Expand All
  </button>
  <button
    onClick={() => {
      const all: Record<number, boolean> = {};
      modules.forEach(m => { all[m.moduleNumber || 1] = true; }); // true = collapsed
      setCollapsedModules(all);
    }}
    className="text-sm px-3 py-1 border rounded hover:bg-gray-50"
  >
    Collapse All
  </button>
</div>
```

---

### B-7 · Drag-and-Drop Reordering: Modules and Interactives

**File:** `frontend/app/view/page.tsx`
**Package to add:** `@dnd-kit/core` + `@dnd-kit/sortable` (lightweight, no jQuery dependency)

**Install:**
```bash
cd frontend && npm install @dnd-kit/core @dnd-kit/sortable @dnd-kit/utilities
```

**What to change:**

**Module reordering:**
1. Wrap module list in `<DndContext onDragEnd={handleModuleDragEnd}>`
2. Wrap each module card in `<SortableItem id={moduleNum}>`
3. Add drag handle icon (GripVertical from lucide-react) to module header
4. `handleModuleDragEnd` swaps module positions and reassigns `moduleNumber` values:

```tsx
function handleModuleDragEnd(event: DragEndEvent) {
  const { active, over } = event;
  if (!over || active.id === over.id) return;

  const oldIdx = modules.findIndex(m => m.moduleNumber === active.id);
  const newIdx = modules.findIndex(m => m.moduleNumber === over.id);

  // Reorder array
  const reordered = arrayMove(modules, oldIdx, newIdx);

  // Reassign moduleNumbers sequentially
  const renumbered = reordered.map((m, i) => ({ ...m, moduleNumber: i + 1 }));

  // Update context + auto-save
  setCourseData(prev => ({ ...prev, modules: renumbered }));
  saveModules(renumbered); // POST to /api/course/save
}
```

**Interactive block reordering within a module (tabs/accordion/flipcard items):**
- Each editable list (tabs, accordion items, flipcard cards) gets a drag handle
- Same DndContext pattern applied to the item list within the structured editor (from B-5)

---

## MERGE STRATEGY

```
main
├── feature/member-a-backend-xapi    (A's branch - pure backend/generator changes)
│   ├── A-1: KC radio → buttons (xapi_generator.py)
│   ├── A-2: KC correct answer fix (xapi_generator.py)
│   ├── A-3: Quiz-conditional xAPI tracking (xapi_generator.py)
│   ├── A-4: 100% completion tracking (xapi_generator.py)
│   └── A-5: Estimated time generation (course_generator.py)
│
└── feature/member-b-frontend-ui     (B's branch - pure frontend changes)
    ├── B-1: Remove flashcards from Learning Aids (StepCourseInfo.tsx)
    ├── B-2: Module count validation 1-20 (StepCourseInfo.tsx)
    ├── B-3: Estimated time display fix (view/page.tsx)
    ├── B-4: Outline 1.1, 1.2 section format (view/page.tsx)
    ├── B-5: CRUD for interactives (view/page.tsx)
    ├── B-6: Expand all / Collapse all + default collapsed (view/page.tsx)
    └── B-7: Drag-and-drop reordering (view/page.tsx)
```

**Merge order:**
1. Member A opens PR → reviewed → merged to main
2. Member B rebases `feature/member-b-frontend-ui` on updated main → opens PR → merged

**Why zero conflicts:**
- Member A only touches: `generators/xapi_generator.py`, `services/course_generator.py`
- Member B only touches: `frontend/app/view/page.tsx`, `frontend/app/components/wizard/StepCourseInfo.tsx`
- These file sets have **zero overlap**

---

## DEPENDENCY NOTES

### Member B depends on Member A for:
- **B-3 (Estimated Time display):** Works independently with inline fallback calculation. Once A-5 is merged, the backend will populate `estimatedTime` correctly and B-3's fallback becomes the safety net — no code change needed between them.

### Shared Data Contract:
- `module.estimatedTime` → A-5 sets it, B-3 displays it — no conflict
- `course.quiz` → A-3 checks existence; B's QuizEditor already handles null quiz gracefully
- `module.interactiveBlock` → A doesn't touch the field structure; B-5 adds CRUD UI for it

---

## TASK PRIORITY ORDER

### Member A — Recommended Order:
1. **A-2** (KC correct answer) — smallest, safest, critical bug fix
2. **A-1** (KC UI redesign) — depends on A-2 being done first
3. **A-3** (Quiz-conditional xAPI) — independent
4. **A-4** (Completion 100%) — builds on A-3
5. **A-5** (Estimated time) — independent, backend only

### Member B — Recommended Order:
1. **B-1** (Remove flashcards) — smallest change
2. **B-2** (Module count validation) — small, isolated
3. **B-6** (Expand/Collapse all + default) — medium, isolated
4. **B-4** (Outline section format) — medium
5. **B-3** (Estimated time display) — medium, needs B-4 context
6. **B-5** (CRUD for interactives) — largest, most complex
7. **B-7** (Drag-and-drop) — most complex, needs npm install

---

## FILE CHANGE SUMMARY

| Task | Member | Primary File | Lines Affected (approx) |
|------|--------|-------------|------------------------|
| A-1 KC UI | A | `generators/xapi_generator.py` | ~2025-2100, ~6714-6841 |
| A-2 KC Answer | A | `generators/xapi_generator.py` | ~6739-6755 |
| A-3 Quiz xAPI | A | `generators/xapi_generator.py` | generate_package(), tincan XML |
| A-4 Completion | A | `generators/xapi_generator.py` | checkCourseCompletion() JS |
| A-5 Est. Time | A | `services/course_generator.py` | _generate_single_module() |
| B-1 Flashcards | B | `frontend/app/components/wizard/StepCourseInfo.tsx` | ~183-220 |
| B-2 Validation | B | `frontend/app/components/wizard/StepCourseInfo.tsx` | ~140-175 |
| B-3 Time display | B | `frontend/app/view/page.tsx` | ~615-640, ~933 |
| B-4 Outline fmt | B | `frontend/app/view/page.tsx` | ~615-645 |
| B-5 CRUD | B | `frontend/app/view/page.tsx` | ~730-769 + new sections |
| B-6 Collapse all | B | `frontend/app/view/page.tsx` | ~260-264 + toolbar area |
| B-7 DnD | B | `frontend/app/view/page.tsx` | module map + package.json |
