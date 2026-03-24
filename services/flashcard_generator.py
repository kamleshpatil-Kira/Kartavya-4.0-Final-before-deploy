import google.generativeai as genai
import json
import re
from typing import Dict, Any, List
from config import GEMINI_API_KEY, GEMINI_MODEL
from utils.logger import logger, log_api_call
import time

class FlashcardGenerator:
    """Generate interactive flashcards for course modules"""
    
    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("AI provider API key is not configured")
        
        genai.configure(api_key=GEMINI_API_KEY)
        # Use configured model (consistent with GeminiService)
        model_name = GEMINI_MODEL or 'gemini-3-flash-preview'
        self.model = genai.GenerativeModel(model_name)
    
    def generate_flashcards(self, module_content: Dict, module_title: str, num_flashcards: int = 5) -> List[Dict[str, Any]]:
        """Generate flashcards for a module"""
        start_time = time.time()
        log_api_call("AI", "generate_flashcards", 0, False)
        
        try:
            prompt = self._build_flashcard_prompt(module_content, module_title, num_flashcards)
            response = self.model.generate_content(prompt)
            
            duration = time.time() - start_time
            log_api_call("AI", "generate_flashcards", duration, True)
            
            return self._parse_flashcard_response(response.text)
        except Exception as error:
            duration = time.time() - start_time
            log_api_call("AI", "generate_flashcards", duration, False, error)
            logger.error(f"Failed to generate flashcards: {error}", exc_info=True)
            return []  # Return empty list on error
    
    def _build_flashcard_prompt(self, section_content: Dict, section_title: str, num_flashcards: int) -> str:
        """Build prompt for flashcard generation - now accepts section content instead of module content"""
        # Handle both section dict and module dict for backward compatibility
        if isinstance(section_content, dict) and 'sectionTitle' in section_content:
            # It's a section
            content_to_use = section_content
            title_to_use = section_title or section_content.get('sectionTitle', 'Section')
        else:
            # It's a module (backward compatibility)
            content_to_use = section_content
            title_to_use = section_title
        
        return f"""Generate interactive flashcards for this content. Create EXACTLY {num_flashcards} flashcards that help learners memorize and understand key concepts from the content provided.

Section Title: {title_to_use}
Section Content: {json.dumps(content_to_use, indent=2)}

CRITICAL REQUIREMENTS:
1. Create EXACTLY {num_flashcards} flashcards covering the most important concepts
2. Each flashcard should have:
   - Front: A ONE-LINER concept, question, or key term (MAXIMUM 4 words - MUST fit in one line)
   - Back: A clear, concise explanation or answer (MAXIMUM 8 words - MUST be ONE COMPLETE LINE)
3. Content MUST fit inside a flashcard box without ANY truncation or overflow
4. NEVER use ellipsis (...) - if content is too long, make it shorter
5. Front side: Can be EITHER:
   - A ONE-LINER QUESTION format (e.g., "What is Machine Learning?" or "Why is data important?")
   - OR a ONE-LINER CONCEPT/KEY TERM (e.g., "Machine Learning" or "Strategic Alignment" or "Data Quality")
   - Keep it SHORT and COMPLETE - must fit in one line
   - Use whichever format best represents the concept
6. Back side: Use EXTREMELY short, punchy explanations that are COMPLETE SENTENCES (e.g., "AI learns from data" not "AI that learns from data to make predictions")
7. CRITICAL: Back side answers MUST be complete thoughts - never start mid-sentence or end mid-sentence
8. Each answer must be a standalone, complete statement that makes sense on its own
9. Make flashcards engaging and educational
10. Focus on key concepts, definitions, and important facts
11. Keep ALL text EXTREMELY SHORT - prioritize fitting in box over detail
12. Each word counts - be ruthless about brevity but ensure completeness
13. Front side can be a question OR a concept/term - choose the format that best fits the content
14. No plagiarism

Format your response as JSON:
{{
  "flashcards": [
    {{
      "id": 1,
      "front": "Question or key term",
      "back": "Explanation or answer"
    }},
    {{
      "id": 2,
      "front": "Question or key term",
      "back": "Explanation or answer"
    }}
  ]
}}"""
    
    def _truncate_flashcard_text(self, text: str, max_words: int, is_back: bool = False) -> str:
        """Truncate flashcard text to max_words without using ellipsis
        
        Args:
            text: Text to truncate
            max_words: Maximum number of words
            is_back: If True, ensures the answer is a complete sentence
        """
        if not text:
            return ""
        
        words = text.split()
        if len(words) <= max_words:
            # Ensure it's a complete sentence if it's the back side
            if is_back and text and not text.rstrip().endswith(('.', '!', '?')):
                # Add period if missing
                return text.rstrip() + '.'
            return text
        
        # Take first max_words
        truncated = " ".join(words[:max_words])
        
        # For back side, ensure it's a complete sentence
        if is_back:
            # Remove trailing punctuation that might look odd
            truncated = truncated.rstrip('.,;:')
            # Ensure it ends with proper punctuation
            if not truncated.rstrip().endswith(('.', '!', '?')):
                truncated += '.'
            # Try to end at a natural break point (before conjunctions, prepositions)
            # If we cut off mid-sentence, try to find a better break point
            if len(words) > max_words:
                # Look for natural break points in the last few words
                break_words = ['and', 'or', 'but', 'the', 'a', 'an', 'to', 'for', 'of', 'in', 'on', 'at']
                for i in range(max_words - 1, max(0, max_words - 3), -1):
                    if words[i].lower() in break_words:
                        truncated = " ".join(words[:i])
                        truncated = truncated.rstrip('.,;:')
                        if not truncated.rstrip().endswith(('.', '!', '?')):
                            truncated += '.'
                        break
        
        return truncated
    
    def _clean_json_text(self, json_text: str) -> str:
        """Clean JSON text to handle trailing commas"""
        # Remove trailing commas before closing braces/brackets
        json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
        # Remove trailing commas at end of lines
        json_text = re.sub(r',\s*\n\s*([}\]])', r'\n\1', json_text)
        return json_text.strip()
    
    def _parse_flashcard_response(self, text: str) -> List[Dict[str, Any]]:
        """Parse flashcard response and ensure content is short and crisp"""
        try:
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', text) or re.search(r'```\s*([\s\S]*?)\s*```', text)
            json_text = json_match.group(1) if json_match else text
            json_text = json_text.strip()
            
            # Clean trailing commas and other common JSON issues
            json_text = self._clean_json_text(json_text)
            
            data = json.loads(json_text)
            flashcards = data.get('flashcards', [])
            
            # Post-process to ensure content is short and crisp
            for card in flashcards:
                # Front: max 4 words (further reduced for better fit)
                if 'front' in card:
                    card['front'] = self._truncate_flashcard_text(card['front'], 4, is_back=False)
                # Back: max 8 words (further reduced for better fit) - ensure complete sentence
                if 'back' in card:
                    card['back'] = self._truncate_flashcard_text(card['back'], 8, is_back=True)
            
            return flashcards
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse flashcard response: {e}")
            return []

