import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path
import time
from services.gemini_service import GeminiService
from services.google_tts_service import GoogleTTSService
from services.flashcard_generator import FlashcardGenerator
from services.image_generator import ImageGeneratorService
from utils.logger import logger, log_generation_start, log_generation_progress, log_generation_complete
from utils.qa_validator import qa_validator
from config import OUTPUT_DIR, GEMINI_API_KEY

class CourseGenerator:
    """Orchestrates the entire course generation process"""
    
    def __init__(self):
        self.gemini = GeminiService()
        self.google_tts = GoogleTTSService()
        self.flashcard_gen = FlashcardGenerator()
        self.image_gen = ImageGeneratorService(api_key=GEMINI_API_KEY)
        
    def _extract_abbreviations(self, modules: List[Dict]) -> Dict[str, str]:
        """
        Scans all module content and returns a dict: { "SIP": "Systematic Investment Plan", ... }
        Only the first occurrence is captured. Pattern matches formats like 'Full Form (ABB)'.
        """
        import re
        # Match 'Words (ABB)' where ABB is 2-8 uppercase letters
        pattern = re.compile(r'\b([A-Za-z][^\(]{2,50}?)\s*\(([A-Z]{2,8})\)')
        seen = {}
        
        def _extract_all_text(obj):
            """Recursive helper to extract all string values from the content dictionary"""
            if isinstance(obj, str):
                yield obj
            elif isinstance(obj, dict):
                for v in obj.values():
                    yield from _extract_all_text(v)
            elif isinstance(obj, list):
                for item in obj:
                    yield from _extract_all_text(item)

        for module in modules:
            for text in _extract_all_text(module):
                for match in pattern.finditer(text):
                    full_form = match.group(1).strip()
                    abbr = match.group(2)
                    if abbr not in seen:
                        seen[abbr] = full_form
        return seen

    async def generate_course(self, user_input: Dict[str, Any], 
                            progress_callback=None,
                            is_regen: bool = False,
                            stats_uploads_dir: Path = None) -> Dict[str, Any]:
        """
        Generate complete course with the requested number of modules (1–N).
        
        user_input should contain:
        - courseTitle
        - targetAudience
        - institute
        - relevantLaws
        - tone
        - audioOptions: {accent, gender, speed}
        - generationType: "scratch", "regenerate", "edit"
        - existingCourseData: existing course data (for edit/regenerate)
        - editOptions: list of options to regenerate (for edit mode)
        - generateOutlineOnly: bool
        - generateQuizOnly: bool
        """
        start_time = time.time()
        user_id = user_input.get("userId", "anonymous")
        generation_type = user_input.get("generationType", "scratch")
        existing_course = user_input.get("existingCourseData")
        edit_options = user_input.get("editOptions", [])
        generate_outline_only = user_input.get("generateOutlineOnly", False)
        generate_quiz_only = user_input.get("generateQuizOnly", False)
        
        log_generation_start(user_id, generation_type)
        
        try:
            # Handle outline only
            if generate_outline_only:
                await self._update_progress(progress_callback, 50, "Generating course outline...")
                outline = await asyncio.to_thread(
                    self.gemini.generate_course_outline, user_input
                )
                await self._update_progress(progress_callback, 100, "Outline generated!")
                return {
                    "outline": outline,
                    "metadata": {
                        "generation_time": time.time(),
                        "generation_duration": time.time() - start_time
                    }
                }
            
            # Handle quiz only
            if generate_quiz_only:
                await self._update_progress(progress_callback, 50, "Generating quiz...")
                if existing_course and existing_course.get("modules"):
                    module_contents = [m.get("content", {}) for m in existing_course["modules"]]
                    course_title = existing_course.get("course", {}).get("title", user_input.get("courseTitle", "Course"))
                else:
                    # Need to generate modules first for quiz
                    await self._update_progress(progress_callback, 10, "Generating modules for quiz...")
                    temp_course = await self._generate_full_course(user_input, progress_callback)
                    module_contents = [m.get("content", {}) for m in temp_course["modules"]]
                    course_title = temp_course["course"]["title"]
                
                quiz = await asyncio.to_thread(
                    self.gemini.generate_quiz,
                    module_contents,
                    course_title,
                    user_input.get('courseLanguage', 'English')
                )
                await self._update_progress(progress_callback, 100, "Quiz generated!")
                return {
                    "quiz": quiz,
                    "metadata": {
                        "generation_time": time.time(),
                        "generation_duration": time.time() - start_time
                    }
                }
            
            # Handle edit mode
            if generation_type == "edit_generated_course" and existing_course:
                return await self._edit_course(existing_course, user_input, edit_options, progress_callback)
            
            # Handle regenerate mode — full deep analysis + seeded regeneration
            if generation_type == "regenerate_from_existing_course" and existing_course:
                return await self._regenerate_from_existing(existing_course, user_input, progress_callback)
            
            # Default: generate from scratch
            return await self._generate_full_course(user_input, progress_callback, is_regen=is_regen, stats_uploads_dir=stats_uploads_dir)
            
        except Exception as error:
            duration = time.time() - start_time
            log_generation_complete(user_id, duration, False)
            logger.error(f"Course generation failed: {error}", exc_info=True)
            raise
    
    async def _regenerate_from_existing(self, existing_course: Dict[str, Any],
                                        user_input: Dict[str, Any],
                                        progress_callback=None,
                                        stats_uploads_dir: Path = None) -> Dict[str, Any]:
        """
        Deep analysis of uploaded course + seeded full regeneration.
        
        Pipeline:
          1. Extract full text from existing_course (JSON, raw content, etc.)
          2. Call gemini.analyze_existing_course() → produces rich blueprint
          3. Merge blueprint into user_input (pre-populate title, audience, etc.)
          4. Call _generate_full_course() with blueprint-enriched user_input
        """
        await self._update_progress(progress_callback, 5, "Analysing your existing course content...")

        # Extract raw text for Gemini analysis
        extracted_content = ""
        file_type = existing_course.get("file_type", "unknown")

        if existing_course.get("extracted_content"):
            # Came from CourseLoader (document/ZIP upload)
            extracted_content = existing_course["extracted_content"]
        elif existing_course.get("raw_course_data"):
            import json as _json
            extracted_content = _json.dumps(existing_course["raw_course_data"], indent=2)[:30000]
            file_type = "json"
        else:
            # It's a plain course JSON structure — serialize it
            import json as _json
            extracted_content = _json.dumps(existing_course, indent=2)[:30000]
            file_type = "json"

        await self._update_progress(progress_callback, 10, "Running Gemini course intelligence analysis...")

        # Deep Gemini analysis
        blueprint = await asyncio.to_thread(
            self.gemini.analyze_existing_course,
            extracted_content,
            file_type
        )

        await self._update_progress(progress_callback, 15, f"Blueprint ready — regenerating improved course...")

        # Pre-populate user_input from blueprint (only if user hasn't overridden)
        if blueprint:
            if blueprint.get("courseTitle") and not user_input.get("courseTitle"):
                user_input["courseTitle"] = blueprint["courseTitle"]
            if blueprint.get("detectedAudience") and not user_input.get("targetAudience"):
                user_input["targetAudience"] = blueprint["detectedAudience"]
            if blueprint.get("complianceRefs") and not user_input.get("relevantLaws"):
                user_input["relevantLaws"] = ", ".join(blueprint["complianceRefs"])
            if blueprint.get("detectedTone") and not user_input.get("tone"):
                user_input["tone"] = blueprint["detectedTone"]

            # Inject blueprint as seeding context for Gemini outline prompt
            user_input["existingCourseBlueprint"] = blueprint

            # Use detected module count — honour exact count from blueprint, no clamping
            detected_count = blueprint.get("estimatedModuleCount", 0)
            # Fallback: count detectedModules if estimatedModuleCount wasn't set correctly
            if not detected_count:
                detected_count = len(blueprint.get("detectedModules", []))
            if detected_count > 0 and not user_input.get("numModules"):
                user_input["numModules"] = max(1, min(20, detected_count))  # Clamp to 1-20

        logger.info(f"Regenerating course from blueprint: '{blueprint.get('courseTitle')}' → improved version")

        return await self._generate_full_course(user_input, progress_callback, is_regen=True, stats_uploads_dir=stats_uploads_dir)

    def _assign_interactive_types(self, modules: list, selected_types: list) -> dict:
        """
        Assigns one interactive type per module.
        - Shuffles selected_types
        - Cycles through types to cover all modules
        - Ensures no two consecutive modules have the same type
        Returns: { module_number: type_string }
        """
        if not selected_types:
            return {}
        
        import random
        assignment = {}
        shuffled = selected_types.copy()
        random.shuffle(shuffled)
        
        for i, module in enumerate(modules):
            module_num = module.get('moduleNumber', i + 1)
            # Pick type, ensuring no consecutive repeat
            for attempt in range(len(shuffled) * 2):
                candidate = shuffled[i % len(shuffled)]
                if i == 0 or assignment.get(modules[i-1].get('moduleNumber', i)) != candidate:
                    assignment[module_num] = candidate
                    break
                # rotate to try next
                shuffled = shuffled[1:] + [shuffled[0]]
            else:
                # fallback: just pick something different from previous
                prev = assignment.get(modules[i-1].get('moduleNumber', i))
                candidates = [t for t in shuffled if t != prev]
                if not candidates:  # only 1 type selected — must reuse it
                    candidates = shuffled
                assignment[module_num] = candidates[0]
        
        return assignment

    async def _generate_full_course(self, user_input: Dict[str, Any], 
                                   progress_callback=None,
                                   is_regen: bool = False,
                                   stats_uploads_dir: Path = None) -> Dict[str, Any]:
        """Generate complete course from scratch"""

        start_time = time.time()
        user_id = user_input.get("userId", "anonymous")
        
        course_data = {
            "course": {},
            "modules": [],
            "quiz": {},
            "metadata": {
                "generation_time": time.time(),
                "user_input": user_input
            }
        }

        # Whether to include audio in this course (allows no-audio courses)
        include_audio = user_input.get("includeAudio", True)
        
        # Step 1: Generate course outline
        await self._update_progress(progress_callback, 5, "Generating course outline...")
        outline = await asyncio.to_thread(
            self.gemini.generate_course_outline, user_input
        )
        
        course_data["course"] = {
            "title": outline.get("courseTitle", user_input.get("courseTitle", "Course")),
            "description": outline.get("courseDescription", ""),
            "overview": outline.get("courseOverview", ""),  # Course overview section
            "learningObjectives": outline.get("courseLearningObjectives", []),  # Course-level learning objectives
            "standardName": outline.get("standardName", "None"),
            "jurisdiction": outline.get("jurisdiction", "Global"),
            "requiredTopics": outline.get("requiredTopics", []),
            "roleConstraints": outline.get("roleConstraints", {}),
            "id": f"course-{int(time.time())}",
            "courseLanguage": user_input.get("courseLanguage", "English"),
            "showAiFooter": user_input.get("showAiFooter", True)
        }
        
        # Use all modules from outline
        modules_outline = outline.get("modules", [])
        
        # Get requested number of modules from user input
        requested_num_modules = user_input.get("numModules", 4)
        if not isinstance(requested_num_modules, int) or requested_num_modules < 1:
            requested_num_modules = 1
        elif requested_num_modules > 20:
            requested_num_modules = 20
        
        # Validate we have at least some modules
        if not modules_outline or len(modules_outline) == 0:
            raise ValueError("Course outline generation failed - no modules were generated. Please try again.")
        
        # Validate module count matches requested (allow some flexibility - within 1 module)
        actual_num_modules = len(modules_outline)
        if abs(actual_num_modules - requested_num_modules) > 1:
            logger.warning(f"Generated {actual_num_modules} modules but requested {requested_num_modules}. Using generated modules.")
        elif actual_num_modules != requested_num_modules:
            logger.info(f"Generated {actual_num_modules} modules (requested {requested_num_modules}). Using generated modules.")
        
        # Log module count
        logger.info(f"Course outline generated with {actual_num_modules} modules (requested: {requested_num_modules})")
        
        # Step 2: Generate each module sequentially to prevent thread exhaustion/rate limits
        all_module_content = []
        total_modules = len(modules_outline)
        
        progress_per_module = 75.0 / total_modules if total_modules > 0 else 75.0
        module_base_progress = 5  # Start after outline
        
        interactive_assignments = self._assign_interactive_types(
            modules_outline, user_input.get("interactiveBlocks", [])
        )

        law_ownership_map = outline.get("regulatoryOwnershipMap", {})
        scenario_type_plan = outline.get("scenarioTypePlan", {})
        modules_covered_so_far = []
        
        for idx, module_outline in enumerate(modules_outline):
            try:
                interactive_type = interactive_assignments.get(module_outline.get('moduleNumber', idx + 1))
                module_num_str = str(module_outline.get('moduleNumber', idx + 1))
                scenario_type = scenario_type_plan.get(module_num_str, "BAD_DECISION")
                
                module_data = await self._generate_single_module(
                    idx, module_outline, total_modules, course_data, user_input,
                    module_base_progress, progress_per_module, progress_callback,
                    interactive_type=interactive_type,
                    modules_covered_so_far=modules_covered_so_far,
                    law_ownership_map=law_ownership_map,
                    scenario_type=scenario_type
                )
                
                covered_summary = f"Module {module_data.get('moduleNumber', idx+1)}: {module_data.get('moduleTitle', '')}"
                modules_covered_so_far.append(covered_summary)
                
                course_data["modules"].append(module_data)
                all_module_content.append(module_data["content"])
            except Exception as e:
                logger.error(f"Module {idx+1} generation failed: {e}", exc_info=True)
                raise e
        
        # Step 2.5: Generate Course Instructions audio (78% - after all modules are done)
        instructions_progress = 78
        await self._update_progress(
            progress_callback,
            instructions_progress,
            "Generating course instructions audio..."
        )
        
        # Generate instructions text (same as what's shown in the UI)
        total_modules = len(modules_outline)
        estimated_minutes = total_modules * 6
        course_title = course_data["course"]["title"]
        
        instructions_text = f"""Welcome to your {course_title}.

This course will take approximately {estimated_minutes} minutes to complete. You can pause at any time and return later - your progress will be saved.

At the end of each module, you'll see short knowledge checks. These are practice questions that you can retry as many times as needed. They do not count towards your final score.

At the end of the course, there is a final quiz. You have a maximum of 3 quiz attempts to pass with a score of 80% or higher. Your best score will be recorded. You won't need to retake the course until all three quiz attempts are consumed.

An auto-audio player is built into this course. Narration will begin automatically when each slide loads, guiding you through the content. If you need, you can pause, replay, or adjust the volume at any time.

If you experience technical issues, or if something doesn't work as expected, please reach out to your administrator or support team.

The goal of this training is to provide you with the knowledge and skills needed to succeed. Let's begin."""
        
        # Generate audio for instructions using the same audio options as modules
        audio_options = user_input.get("audioOptions", {})

        if include_audio:
            try:
                instructions_audio_result = await asyncio.to_thread(
                    self.google_tts.generate_audio,
                    instructions_text,
                    audio_options
                )

                # Save instructions audio file
                temp_dir = Path(OUTPUT_DIR) / "temp"
                temp_dir.mkdir(exist_ok=True)

                instructions_audio_filename = "instructions-audio.mp3"
                instructions_audio_path = temp_dir / instructions_audio_filename

                # Handle both single and chunked audio
                if instructions_audio_result.get("is_chunked") and instructions_audio_result.get("audio_chunks"):
                    # Concatenate all chunks so the full narration is preserved (Bug #6 fix)
                    audio_data = b"".join(
                        chunk["audio_data"]
                        for chunk in instructions_audio_result["audio_chunks"]
                        if chunk.get("audio_data")
                    )
                    with open(instructions_audio_path, "wb") as f:
                        f.write(audio_data)
                else:
                    # Single audio file
                    audio_data = instructions_audio_result.get("audio_data")
                    if audio_data:
                        with open(instructions_audio_path, "wb") as f:
                            f.write(audio_data)

                # Store instructions audio path in course data
                course_data["instructions"] = {
                    "audioPath": str(instructions_audio_path),
                    "text": instructions_text
                }

                logger.info(f"Generated instructions audio: {instructions_audio_path}")

            except Exception as e:
                logger.warning(f"Failed to generate instructions audio: {e}. Course will continue without instructions audio.")
                # Don't fail the entire course generation if instructions audio fails
                course_data["instructions"] = {
                    "audioPath": None,
                    "text": instructions_text
                }
        else:
            # Audio excluded - do not generate instructions audio
            instructions_audio_path = None
            course_data["instructions"] = {
                "audioPath": None,
                "text": instructions_text
            }
            logger.info("Audio generation disabled for this course; skipped instructions audio.")
        
        # Step 2.6: Generate course images (if user opted in)
        include_images = user_input.get("includeImages", False)
        if include_images:
            try:
                await self._update_progress(progress_callback, 76, "Generating course images...")
                course_id = course_data["course"].get("id", "")
                image_paths = await self.image_gen.generate_images_for_course(
                    course_title=course_data["course"]["title"],
                    modules=course_data["modules"],
                    output_dir=OUTPUT_DIR / "assets",
                    course_id=course_id,
                    progress_callback=progress_callback,
                    user_input=user_input,
                    is_regen=is_regen,
                    stats_uploads_dir=stats_uploads_dir,
                )
                for module_idx, image_path in image_paths.items():
                    if module_idx < len(course_data["modules"]):
                        course_data["modules"][module_idx]["imagePath"] = str(image_path)
                logger.info(f"Image generation complete: {len(image_paths)} images generated")
            except Exception as e:
                logger.warning(f"Image generation failed, continuing without images: {e}")
        
        # Step 3: Generate final quiz (80% - only if user opted in)
        quiz_progress = 80
        add_quizzes = user_input.get("addQuizzes", False)
        num_quiz_questions = user_input.get("numQuizQuestions", 10)
        quiz = {}

        if add_quizzes:
            existing_course = user_input.get("existingCourseData")
            existing_quiz = None

            # Check if existing course has a quiz to scramble
            if existing_course and isinstance(existing_course, dict):
                existing_quiz = existing_course.get("quiz")
                if existing_quiz and isinstance(existing_quiz, dict):
                    questions = existing_quiz.get("questions", [])
                    if questions and len(questions) > 0:
                        await self._update_progress(progress_callback, quiz_progress, "Scrambling quiz with new questions...")
                        quiz = await asyncio.to_thread(
                            self.gemini.scramble_quiz,
                            existing_quiz,
                            all_module_content,
                            course_data["course"]["title"],
                            user_input.get('courseLanguage', 'English')
                        )
                    else:
                        await self._update_progress(progress_callback, quiz_progress, f"Generating {num_quiz_questions}-question final quiz...")
                        quiz = await asyncio.to_thread(
                            self.gemini.generate_quiz,
                            all_module_content,
                            course_data["course"]["title"],
                            user_input.get('courseLanguage', 'English'),
                            num_quiz_questions
                        )
                else:
                    await self._update_progress(progress_callback, quiz_progress, f"Generating {num_quiz_questions}-question final quiz...")
                    quiz = await asyncio.to_thread(
                        self.gemini.generate_quiz,
                        all_module_content,
                        course_data["course"]["title"],
                        user_input.get('courseLanguage', 'English'),
                        num_quiz_questions
                    )
            else:
                await self._update_progress(progress_callback, quiz_progress, f"Generating {num_quiz_questions}-question final quiz...")
                quiz = await asyncio.to_thread(
                    self.gemini.generate_quiz,
                    all_module_content,
                    course_data["course"]["title"],
                    user_input.get('courseLanguage', 'English'),
                    num_quiz_questions
                )
        else:
            logger.info("Quiz generation skipped — user did not opt in (addQuizzes=False)")
            await self._update_progress(progress_callback, quiz_progress, "Skipping quiz (not enabled)...")

        course_data["quiz"] = quiz
        
        # QA Validation (85%)
        await self._update_progress(progress_callback, 85, "Validating course content...")
        is_valid, issues = await asyncio.to_thread(
            qa_validator.validate_course_content,
            course_data
        )
        
        if not is_valid:
            logger.warning(f"QA validation found issues: {issues}")
            course_data["metadata"]["qa_issues"] = issues
            course_data["metadata"]["qa_validated"] = False
        else:
            course_data["metadata"]["qa_validated"] = True
            course_data["metadata"]["qa_issues"] = []
        
        # Calculate course level estimated time
        def parse_time(time_str: str, index: int) -> int:
            try:
                val = time_str.split(" ")[0].split("-")[index]
                return int(val)
            except:
                return 1

        total_lo = sum(parse_time(m.get('estimatedTime', '1-3 minutes'), 0) for m in course_data["modules"])
        total_hi = sum(parse_time(m.get('estimatedTime', '1-3 minutes'), 1) for m in course_data["modules"])
        course_data["course"]["estimatedTime"] = f"{total_lo}-{total_hi} minutes"

        # Extract abbreviations / acronyms from all generated module content
        course_data["abbreviations"] = self._extract_abbreviations(course_data["modules"])

        # Complete
        duration = time.time() - start_time
        log_generation_complete(user_id, duration, True)
        
        await self._update_progress(progress_callback, 100, "Course generation complete!")
        
        course_data["metadata"]["generation_duration"] = duration
        
        return course_data
    
    async def _edit_course(self, existing_course: Dict[str, Any], 
                          user_input: Dict[str, Any], 
                          edit_options: List[str],
                          progress_callback=None) -> Dict[str, Any]:
        """Edit specific parts of an existing course"""
        start_time = time.time()
        user_id = user_input.get("userId", "anonymous")
        edit_details = user_input.get("editDetails", {})
        
        # Start with existing course data
        course_data = existing_course.copy()
        course_data["metadata"] = course_data.get("metadata", {})
        course_data["metadata"]["edit_time"] = time.time()
        course_data["metadata"]["edit_options"] = edit_options
        course_data["metadata"]["edit_details"] = edit_details
        
        # If no options selected, regenerate everything
        if not edit_options:
            edit_options = [
                "Course Outline", "Module Content", "Module Images", 
                "Module Audio", "Knowledge Checks", "Flashcards", "Final Quiz"
            ]
        
        logger.info(f"Editing course with options: {edit_options}")
        
        # Regenerate course outline if requested
        if "Course Outline" in edit_options:
            await self._update_progress(progress_callback, 5, "Regenerating course outline...")
            outline = await asyncio.to_thread(
                self.gemini.generate_course_outline, user_input
            )
            course_data["course"] = {
                "title": outline.get("courseTitle", course_data["course"].get("title", "")),
                "description": outline.get("courseDescription", course_data["course"].get("description", "")),
                "id": course_data["course"].get("id", f"course-{int(time.time())}")
            }
        
        # Regenerate modules
        modules_to_regenerate = []
        if "Module Content" in edit_options or "Module Images" in edit_options or \
           "Module Audio" in edit_options or "Knowledge Checks" in edit_options or \
           "Flashcards" in edit_options:
            modules_to_regenerate = list(range(len(course_data.get("modules", []))))
        
        all_module_content = []
        for idx, module in enumerate(course_data.get("modules", [])):
            module_num = idx + 1
            progress = 10 + (idx * 40)
            
            # Regenerate module content if requested
            if "Module Content" in edit_options:
                await self._update_progress(
                    progress_callback, 
                    progress, 
                    f"Regenerating Module {module_num} content..."
                )
                module_content = await asyncio.to_thread(
                    self.gemini.generate_module_content,
                    module_num,
                    module.get("moduleTitle", f"Module {module_num}"),
                    course_data["course"],
                    user_input
                )
                module["content"] = module_content
                all_module_content.append(module_content)
            else:
                all_module_content.append(module.get("content", {}))
            
            # Regenerate knowledge check if requested
            if "Knowledge Checks" in edit_options:
                await self._update_progress(
                    progress_callback,
                    progress + 10,
                    f"Regenerating knowledge check for Module {module_num}..."
                )
                knowledge_check = await asyncio.to_thread(
                    self.gemini.generate_knowledge_check,
                    module.get("content", {}),
                    module.get("moduleTitle", f"Module {module_num}"),
                    user_input.get('courseLanguage', 'English'),
                    user_input.get('courseTitle', '')
                )
                module["knowledgeCheck"] = knowledge_check
            
            
            # Module Images editing has been removed
            
            # Regenerate audio if requested
            if "Module Audio" in edit_options:
                await self._update_progress(
                    progress_callback,
                    progress + 25,
                    f"Regenerating audio for Module {module_num}..."
                )
                audio_options = user_input.get("audioOptions", {})
                audio_result = await asyncio.to_thread(
                    self.google_tts.generate_module_audio,
                    module.get("content", {}),
                    audio_options
                )
                
                # Save audio
                audio_filename = f"module_{module_num}_audio.mp3"
                audio_path = OUTPUT_DIR / "assets" / audio_filename
                audio_path.parent.mkdir(parents=True, exist_ok=True)
                saved_audio_path = await asyncio.to_thread(
                    self.google_tts.save_audio,
                    audio_result["audio_data"],
                    audio_path
                )
                
                if saved_audio_path:
                    module["audioPath"] = str(saved_audio_path)
                    module["transcript"] = audio_result.get("text", "")
        
        # Regenerate quiz if requested
        if "Final Quiz" in edit_options:
            await self._update_progress(progress_callback, 90, "Regenerating final quiz...")
            quiz = await asyncio.to_thread(
                self.gemini.generate_quiz,
                all_module_content,
                course_data["course"]["title"],
                user_input.get('courseLanguage', 'English')
            )
            course_data["quiz"] = quiz
        
        # QA Validation
        await self._update_progress(progress_callback, 95, "Validating course content...")
        is_valid, issues = await asyncio.to_thread(
            qa_validator.validate_course_content,
            course_data
        )
        
        if not is_valid:
            logger.warning(f"QA validation found issues: {issues}")
            course_data["metadata"]["qa_issues"] = issues
            course_data["metadata"]["qa_validated"] = False
        else:
            course_data["metadata"]["qa_validated"] = True
            course_data["metadata"]["qa_issues"] = []
        
        # Calculate course level estimated time
        def parse_time(time_str: str, index: int) -> int:
            try:
                val = time_str.split(" ")[0].split("-")[index]
                return int(val)
            except:
                return 1

        total_lo = sum(parse_time(m.get('estimatedTime', '1-3 minutes'), 0) for m in course_data.get("modules", []))
        total_hi = sum(parse_time(m.get('estimatedTime', '1-3 minutes'), 1) for m in course_data.get("modules", []))
        course_data["course"]["estimatedTime"] = f"{total_lo}-{total_hi} minutes"

        duration = time.time() - start_time
        log_generation_complete(user_id, duration, True)
        
        await self._update_progress(progress_callback, 100, "Course editing complete!")
        
        course_data["metadata"]["generation_duration"] = duration
        
        return course_data
    
    def _trim_verbose_content(self, content: Any) -> Any:
        """
        Post-process generated content to strip Gemini's habitual filler phrases.
        Works recursively on dicts, lists, and strings.
        Zero additional API calls — pure Python regex.
        """
        import re

        # Filler patterns to strip outright (sentence-level removals)
        # These are opening clauses that carry no information
        FILLER_PATTERNS = [
            r"It is (?:important|crucial|essential|critical|vital|worth noting|worth mentioning) (?:to note |to mention |to remember |to understand |to keep in mind )?that[,]?\s*",
            r"It goes without saying that[,]?\s*",
            r"Needless to say[,]?\s*",
            r"As (?:we can see|mentioned (?:above|earlier|previously)|noted above|discussed above)[,]?\s*",
            r"As you (?:may|might|will|can|should) (?:know|recall|remember|expect|see|notice)[,]?\s*",
            r"In today'?s (?:world|society|environment|workplace|fast-paced world)[,]?\s*",
            r"In (?:today's|the modern|the current|our) (?:world|era|times|age|landscape)[,]?\s*",
            r"In the realm of [^,\.]+[,]?\s*",
            r"When it comes to [^,\.]+[,]?\s*",
            r"Moving forward[,]?\s*",
            r"At the end of the day[,]?\s*",
            r"This is something (?:that )?everyone should know[\.!]?\s*",
            r"Remember that[,]?\s*",
            r"It'?s (?:important|crucial|essential|critical|vital) (?:to|that)[,]?\s*",
            r"One (?:important|key|crucial|critical|essential) (?:thing|point|aspect|consideration) to (?:note|remember|keep in mind) is that[,]?\s*",
            r"This (?:is a |represents a |serves as a )?crucial (?:aspect|element|component|part) of[^\.]+\.\s*",
            r"The (?:importance|significance|value|role) of this cannot be (?:overstated|understated)[\.!]?\s*",
        ]

        # Compile once
        compiled = [re.compile(p, re.IGNORECASE) for p in FILLER_PATTERNS]

        def clean_string(text: str) -> str:
            if not isinstance(text, str) or not text.strip():
                return text
            for pattern in compiled:
                text = pattern.sub("", text)
            # Clean up any double spaces left behind
            text = re.sub(r"  +", " ", text)
            # Clean up sentences that now start with a lowercase letter after stripping a prefix
            # (capitalise the first letter of each sentence start)
            text = re.sub(r"(?<=[.!?]\s)([a-z])", lambda m: m.group(1).upper(), text)
            # Capitalise very first character
            if text and text[0].islower():
                text = text[0].upper() + text[1:]
            # Replace non-breaking spaces with regular spaces
            text = text.replace('\xa0', ' ').replace('\u00A0', ' ')
            return text.strip()

        def walk(obj: Any) -> Any:
            if isinstance(obj, dict):
                return {k: walk(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [walk(item) for item in obj]
            elif isinstance(obj, str):
                return clean_string(obj)
            return obj

        result = walk(content)
        logger.debug("Verbosity trimmer applied to module content")
        return result

    def _extract_plain_text(self, content: Any) -> str:
        """Helper to extract text from generated module content for word count estimation."""
        import re
        texts = []
        
        def walk(obj: Any):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    # don't extract image urls or audio paths
                    if k not in ['imagePath', 'audioPath', 'audioPaths']:
                        walk(v)
            elif isinstance(obj, list):
                for item in obj:
                    walk(item)
            elif isinstance(obj, str):
                texts.append(re.sub(r'<[^>]+>', ' ', obj))
                
        walk(content)
        return " ".join(texts)

    def _extract_key_topics(self, module_content: Dict) -> List[str]:
        """Extract key topics and concepts from module content to preserve during regeneration"""
        topics = []

        
        if isinstance(module_content, dict):
            # Extract section titles
            if "sections" in module_content:
                for section in module_content.get("sections", []):
                    if "sectionTitle" in section:
                        topics.append(section["sectionTitle"])
                    
                    # Extract concept titles
                    if "concepts" in section:
                        for concept in section.get("concepts", []):
                            if "conceptTitle" in concept:
                                topics.append(concept["conceptTitle"])
            
            # Extract module title
            if "moduleTitle" in module_content:
                topics.insert(0, module_content["moduleTitle"])
        
        # Return unique topics, limit to most important ones
        unique_topics = list(dict.fromkeys(topics))[:10]  # Keep top 10 topics
        logger.info(f"Extracted {len(unique_topics)} key topics to preserve: {unique_topics[:5]}...")
        return unique_topics
    
    async def _update_progress(self, callback, progress: int, message: str):
        """Update progress if callback provided"""
        # Ensure progress is between 0 and 100
        clamped_progress = max(0, min(100, progress))
        
        if callback:
            try:
                await callback(clamped_progress, message)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")
        
        log_generation_progress("user", message, clamped_progress)
    

    async def _generate_single_module(self, idx, module_outline, total_modules, course_data, user_input,
                                     module_base_progress, progress_per_module, progress_callback,
                                     interactive_type: str = None,
                                     modules_covered_so_far: list = None,
                                     law_ownership_map: dict = None,
                                     scenario_type: str = "BAD_DECISION"):
        """Helper to generate a single module asynchronously to support concurrent generation"""
        from config import OUTPUT_DIR
        module_num = idx + 1
        module_start_progress = module_base_progress + (idx * progress_per_module)
        
        # If addFlashcards is on and this module has no interactive type yet, use flipcard
        if user_input.get("addFlashcards", False) and not interactive_type:
            interactive_type = "flipcard"

        # Module content generation (40% of module progress)
        await self._update_progress(
            progress_callback, 
            int(module_start_progress), 
            f"Generating Module {module_num} content (this may take a few minutes)..."
        )
        
        # Generate module content
        module_content = await asyncio.to_thread(
            self.gemini.generate_module_content,
            module_num,
            module_outline["moduleTitle"],
            course_data["course"],
            user_input,
            None, # previous_content
            interactive_type, # interactive_type
            False, # is_regeneration
            modules_covered_so_far,
            law_ownership_map,
            scenario_type
        )
        
        # Post-process: strip Gemini filler phrases without extra API calls
        module_content = self._trim_verbose_content(module_content)
        
        # Store total modules count for navigation
        module_content['totalModules'] = total_modules

        
        # Generate knowledge check (55% of module progress)
        knowledge_check_progress = module_start_progress + (progress_per_module * 0.15)
        await self._update_progress(
            progress_callback,
            int(knowledge_check_progress),
            f"Generating knowledge check for Module {module_num}..."
        )
        
        # Extract primary scenario for knowledge check coupling
        primary_scenario = None
        for section in module_content.get("sections", []):
            if primary_scenario:
                break
            for concept in section.get("concepts", []):
                if "scenario" in concept and isinstance(concept["scenario"], dict):
                    primary_scenario = concept["scenario"]
                    break
        
        knowledge_check = await asyncio.to_thread(
            self.gemini.generate_knowledge_check,
            module_content,
            module_outline["moduleTitle"],
            user_input.get('courseLanguage', 'English'),
            user_input.get('courseTitle', ''),
            primary_scenario
        )
        

        # Generate flashcards PER SECTION (65% of module progress)
        add_flashcards = user_input.get("addFlashcards", False)
        section_flashcards = {}
        sections = module_content.get("sections", [])
        
        if add_flashcards:
            for section_idx, section in enumerate(sections):
                section_title = section.get("sectionTitle", f"Section {section_idx + 1}")
                
                flashcards_progress = module_start_progress + (progress_per_module * 0.25) + ((progress_per_module * 0.05) * (section_idx / len(sections)) if len(sections) > 0 else 0)
                await self._update_progress(
                    progress_callback,
                    int(flashcards_progress),
                    f"Generating flashcards for Module {module_num}, Section {section_idx + 1}/{len(sections)}..."
                )
                
                section_flashcards_list = await asyncio.to_thread(
                    self.flashcard_gen.generate_flashcards,
                    section,
                    section_title
                )
                
                if section_flashcards_list:
                    section_flashcards[section_idx] = section_flashcards_list
                    section["flashcards"] = section_flashcards_list
        else:
            logger.info(f"Flashcard generation skipped for Module {module_num} (user opted out)")
        
        flashcards = section_flashcards.get(0, []) if section_flashcards else []

        # Generate audio for each section (70-90% of module progress)
        audio_options = user_input.get("audioOptions", {})
        include_audio = user_input.get("includeAudio", True)
        section_audio_data = []
        
        if include_audio:
            for section_idx, section in enumerate(sections):
                section_title = section.get("sectionTitle", f"Section {section_idx + 1}")
                
                section_audio_progress = module_start_progress + (progress_per_module * 0.70) + ((progress_per_module * 0.20) * (section_idx / len(sections)) if len(sections) > 0 else 0)
                await self._update_progress(
                    progress_callback,
                    int(section_audio_progress),
                    f"Generating audio for Module {module_num}, Section {section_idx + 1}/{len(sections)}..."
                )
                
                try:
                    section_audio_result = await asyncio.to_thread(
                        self.google_tts.generate_section_audio,
                        section,
                        section_title,
                        audio_options
                    )
                except Exception as error:
                    logger.warning(
                        f"Audio generation failed for Module {module_num}, Section {section_idx + 1}: {error}. "
                        "Continuing without audio for this section."
                    )
                    section_audio_result = {
                        "audio_data": None,
                        "audio_chunks": None,
                        "text": "",
                        "duration_seconds": 0,
                        "estimated_duration": 0,
                    }
                
                saved_section_audio_paths = []
                
                if section_audio_result.get("is_chunked") and section_audio_result.get("audio_chunks"):
                    for chunk_idx, chunk_data in enumerate(section_audio_result["audio_chunks"], 1):
                        chunk_filename = f"module_{module_num}_section_{section_idx + 1}_chunk_{chunk_idx}.mp3"
                        chunk_path = OUTPUT_DIR / "assets" / chunk_filename
                        chunk_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        saved_chunk_path = await asyncio.to_thread(
                            self.google_tts.save_audio,
                            chunk_data["audio_data"],
                            chunk_path
                        )
                        if saved_chunk_path:
                            saved_section_audio_paths.append(str(saved_chunk_path))
                elif section_audio_result.get("audio_data"):
                    section_filename = f"module_{module_num}_section_{section_idx + 1}.mp3"
                    section_audio_path = OUTPUT_DIR / "assets" / section_filename
                    section_audio_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    saved_section_path = await asyncio.to_thread(
                        self.google_tts.save_audio,
                        section_audio_result["audio_data"],
                        section_audio_path
                    )
                    if saved_section_path:
                        saved_section_audio_paths.append(str(saved_section_path))
                
                section_audio_data.append({
                    "sectionIndex": section_idx,
                    "sectionTitle": section_title,
                    "audioPath": saved_section_audio_paths[0] if saved_section_audio_paths else None,
                    "audioPaths": saved_section_audio_paths if len(saved_section_audio_paths) > 1 else None,
                    "transcript": section_audio_result.get("text", ""),
                    "duration_seconds": section_audio_result.get("duration_seconds", 0)
                })
                
                section["audioPath"] = saved_section_audio_paths[0] if saved_section_audio_paths else None
                section["audioPaths"] = saved_section_audio_paths if len(saved_section_audio_paths) > 1 else None
                section["transcript"] = section_audio_result.get("text", "")
        else:
            for section_idx, section in enumerate(sections):
                section_title = section.get("sectionTitle", f"Section {section_idx + 1}")
                section_audio_data.append({
                    "sectionIndex": section_idx,
                    "sectionTitle": section_title,
                    "audioPath": None,
                    "audioPaths": None,
                    "transcript": "",
                    "duration_seconds": 0
                })
                section["audioPath"] = None
                section["audioPaths"] = None
                section["transcript"] = ""
        
        main_audio_path = section_audio_data[0]["audioPath"] if section_audio_data else None
        saved_audio_paths = section_audio_data[0]["audioPaths"] if section_audio_data and section_audio_data[0].get("audioPaths") else ([main_audio_path] if main_audio_path else [])
        
        content_text = self._extract_plain_text(module_content)
        word_count = len(content_text.split())
        reading_min = max(1, round(word_count / 200))
        narration_min = max(1, round(word_count / 130)) if user_input.get("includeAudio", True) else 0
        total_min = reading_min + narration_min
        lo = max(1, total_min - 1)
        hi = total_min + 2
        estimated_time = f"{lo}-{hi} minutes"
        
        module_data = {
            "moduleNumber": module_num,
            "moduleTitle": module_outline["moduleTitle"],
            "learningObjectives": module_outline.get("learningObjectives", []),
            "content": module_content,
            "knowledgeCheck": knowledge_check,
            "flashcards": flashcards,
            "imagePath": None,
            "audioPath": main_audio_path,
            "audioPaths": saved_audio_paths,
            "sectionAudio": section_audio_data,
            "transcript": "\n\n".join([sa.get("transcript", "") for sa in section_audio_data if sa.get("transcript")]),
            "totalModules": total_modules,
            "estimatedTime": estimated_time
        }
        
        return module_data
    def generate_course_outline_only(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """Generate only the course outline"""
        return self.gemini.generate_course_outline(user_input)
    
    def generate_quiz_only(self, module_contents: List[Dict], course_title: str, language: str = "English") -> Dict[str, Any]:
        """Generate only the quiz"""
        return self.gemini.generate_quiz(module_contents, course_title, language)
