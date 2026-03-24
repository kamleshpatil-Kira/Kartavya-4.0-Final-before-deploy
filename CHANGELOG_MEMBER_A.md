# Changelog: Member A - Backend, xAPI & Generator Updates

## Task A-1: Knowledge Check - Remove Radio Buttons (Improve UI)

**Why the change was made:**
The legacy radio-button interface for knowledge checks was clunky and required multiple clicks to select and submit. The goal was to modernize the UI by using styled button cards that provide immediate feedback upon selection, creating a more interactive and premium feel.

**Changes made:**

1. **New Button-Based UI Structure:**
   - **File:** `generators/xapi_generator.py`
   - **Change:** Modified `_build_knowledge_check_html` to remove `<input type="radio">` and replace them with `<button class="kc-option-btn">` components.
   - **Logic:** Integrated `onclick="selectKCOption(...)"` directly onto the buttons for instant evaluation.

2. **Interactive Selection Logic (JS):**
   - **File:** `generators/xapi_generator.py`
   - **Change:** Updated `selectKCOption` to handle the new button-based selection. It now toggles CSS classes for "selected", "correct", and "incorrect" states immediately upon click.

3. **Styling and Feedback:**
   - **File:** `generators/xapi_generator.py`
   - **Change:** Added a comprehensive CSS block for `.kc-option-btn`. It includes hover effects, active states, and specific colors for correct/incorrect feedback, ensuring a modern look and feel.

---

## Task A-2: Knowledge Check - Fix Correct Answer & Randomization

**Why the change was made:**
There were two main issues:
1. Correct answer comparison was case-sensitive, leading to "Incorrect" results if the user input or backend data didn't match perfectly in casing.
2. The generator defaulted to "Option A" as the correct answer for almost all AI-generated questions, making the checks predictable and boring.

**Changes made:**

1. **Case-Insensitive Comparison (JS):**
   - **File:** `generators/xapi_generator.py`
   - **Line:** ~6830
   - **Change:** Updated `checkKnowledgeCheck` to use `.toUpperCase()` on both the selected answer and the correct answer key before comparing them.

2. **Backend Option Randomization (Python):**
   - **File:** `backend/main.py`
   - **Change:** Implemented a `_randomize_kc_options` helper function. This function shuffles the values of the knowledge check options dictionary and remaps the `correctAnswer` key to the new randomized letter (A, B, C, etc.).
   - **Trigger:** This logic is called automatically in `save_course_json` and `load_course_json`, ensuring randomization is fresh for every export and view.

---

## Task A-3: xAPI - Skip Quiz in Tracking & Fix Completion %

**Why the change was made:**
Courses without quizzes were still trying to track a "final quiz" activity in the xAPI (TinCan) manifest, causing failures or 404s in some LMSs. Additionally, the completion percentage was hardcoded to assume a quiz always existed, making it impossible to reach 100% in no-quiz courses.

**Changes made:**

1. **Conditional TinCan Manifest:**
   - **File:** `generators/xapi_generator.py`
   - **Change:** Modified `_generate_tincan_xml` to wrap the `assessment` activity in an `if add_quizzes:` check. If no quiz is opted-in, the manifest correctly excludes the quiz activity.

2. **Dynamic Progress Calculation (JS):**
   - **File:** `generators/xapi_generator.py`
   - **Change:** Refactored `updateProgress` to dynamically calculate the total number of trackable components (`totalComponents = numModules + (hasQuiz ? 1 : 0)`). 
   - Graduation is now calculated as `(completedComponents / totalComponents) * 100`, accurately reflecting 100% completion for any course structure.

---

## Task A-4: Fix Course Completion Tracking (NavBar + Overall 100%)

**Why the change was made:**
Even after finishing a course, the Navbar or Progress bar would occasionally hang at 98% or fail to show "Completed". This prevented the xAPI `completed` statement from being sent reliably.

**Changes made:**

1. **Force Final Completion State:**
   - **File:** `generators/xapi_generator.py`
   - **Change:** Updated `trackCourseCompletion` to explicitly set the progress bar width to `100%` and update the status text to `window.uiLabels.completed`.
   - **Logic:** Added a `courseCompletionTracked` flag to prevent redundant xAPI statements and ensure the "Completed" message is only sent once per session.

---

## Task A-5: Fix Estimated Time: Proper Module-wise Time

**Why the change was made:**
Modules previously displayed "N/A" for estimated time because the backend wasn't calculating it. Users had no way to gauge how long a course or specific module would take.

**Changes made:**

1. **Plain Text Extraction Helper:**
   - **File:** `services/course_generator.py`
   - **Change:** Added `_extract_plain_text` to recursively strip HTML tags and gather all text content from a module.

2. **Mathematical Time Estimation:**
   - **File:** `services/course_generator.py`
   - **Change:** Implemented duration logic based on word count:
     - Reading Speed: ~200 WPM
     - Narration Speed: ~130 WPM (if audio is enabled)
   - **Output:** The system now generates a formatted string like `5-8 minutes` for each module.

3. **Global Course Total:**
   - **File:** `services/course_generator.py`
   - **Change:** Updated `_generate_full_course` and `_edit_course` to sum up all module estimates and set a total `estimatedTime` on the main course object.

---

## Hotfixes & UI Polish

1. **SVG Icon Upgrade (No Emojis):**
   - **File:** `generators/xapi_generator.py`
   - **Change:** Replaced the `✅` and `❌` emojis in the knowledge check feedback with custom SVG icons (Check-circle for success, X-circle for error) and used a flex-gap layout for a cleaner, professional UI.

2. **Course Deletion Prevention:**
   - **File:** `backend/main.py`
   - **Change:** Removed a `shutil.rmtree` call in the xAPI download route that was accidentally deleting the entire course directory upon export.
