from typing import Dict, Any, Optional, List
from pathlib import Path
import time
import io
import base64
import requests
import json
import os
from config import GOOGLE_TTS_API_KEY, AUDIO_WPM_DEFAULT
from utils.logger import logger, log_api_call

# Google Cloud Text-to-Speech API limit: 5,000 characters per request
GOOGLE_TTS_MAX_CHARS = 4000  # Reduced to 4000 chars to account for byte encoding (5000 byte limit)
GOOGLE_TTS_TIMEOUT = float(os.getenv("GOOGLE_TTS_TIMEOUT", "30"))
GOOGLE_TTS_RETRIES = int(os.getenv("GOOGLE_TTS_RETRIES", "1"))
GOOGLE_TTS_BACKOFF = float(os.getenv("GOOGLE_TTS_BACKOFF", "1.6"))

class GoogleTTSService:
    """
    Google Cloud Text-to-Speech API service for text-to-speech audio generation
    Uses Google Cloud Text-to-Speech API for distinct accents (American, British, Indian)
    """
    def __init__(self):
        if not GOOGLE_TTS_API_KEY:
            raise ValueError("API key for content generation service is not configured")

        self.api_key = GOOGLE_TTS_API_KEY
        
        # Google Cloud Text-to-Speech API endpoint
        self.api_url = "https://texttospeech.googleapis.com/v1/text:synthesize"

        self.timeout = GOOGLE_TTS_TIMEOUT
        self.max_retries = max(0, GOOGLE_TTS_RETRIES)
        self.retry_backoff = max(1.0, GOOGLE_TTS_BACKOFF)
        
        logger.info("Initialized Google Cloud Text-to-Speech service")
        
        # Voice mappings for different languages and genders
        # Priority: Journey (most human/character-rich) > Studio > Wavenet > Standard
        # Note: Journey voices are internally named Zephyr, Puck, Aoede, Charon, etc.
        self.voice_configs = {
            "english":    {"male": "en-US-Casual-K",    "female": "en-US-Studio-O"},     # Casual-K (Male), Studio-O (Female) -> Reddit's favorite natural voices
            "american":   {"male": "en-US-Casual-K",    "female": "en-US-Studio-O"},     # Casual-K (Male), Studio-O (Female)
            "british":    {"male": "en-GB-Journey-D",   "female": "en-GB-Journey-F"},    # Charon (Male), Aoede (Female)
            "indian":     {"male": "en-IN-Journey-D",   "female": "en-IN-Journey-F"},    # Fenrir (Male), Kore (Female)
            "spanish":    {"male": "es-ES-Journey-D",   "female": "es-ES-Journey-F"},    # Journey: natural Spanish voices
            "french":     {"male": "fr-FR-Journey-D",   "female": "fr-FR-Journey-F"},    # Journey: natural French voices
            "german":     {"male": "de-DE-Journey-D",   "female": "de-DE-Journey-F"},    # Journey: natural German voices
            "portuguese": {"male": "pt-BR-Wavenet-B",   "female": "pt-BR-Wavenet-C"},    # Wavenet: Studio/Journey unavailable for pt-BR
            "italian":    {"male": "it-IT-Journey-D",   "female": "it-IT-Journey-F"},    # Journey: natural Italian voices
            "dutch":      {"male": "nl-NL-Wavenet-B",   "female": "nl-NL-Wavenet-A"},    # Wavenet: Studio/Journey unavailable for nl-NL
            "russian":    {"male": "ru-RU-Wavenet-B",   "female": "ru-RU-Wavenet-A"},    # Wavenet: best available for Russian
            "chinese":    {"male": "cmn-CN-Wavenet-B",  "female": "cmn-CN-Wavenet-A"},   # Wavenet: best available for Mandarin
            "japanese":   {"male": "ja-JP-Wavenet-D",   "female": "ja-JP-Wavenet-B"},    # Wavenet: best available for Japanese
            "korean":     {"male": "ko-KR-Wavenet-C",   "female": "ko-KR-Wavenet-A"},    # Wavenet: best available for Korean
            "arabic":     {"male": "ar-XA-Wavenet-B",   "female": "ar-XA-Wavenet-A"},    # Wavenet: best available for Arabic
            "hindi":      {"male": "hi-IN-Wavenet-B",   "female": "hi-IN-Wavenet-A"},    # Wavenet: Journey unavailable for Hindi
            "turkish":    {"male": "tr-TR-Wavenet-B",   "female": "tr-TR-Wavenet-C"},    # Wavenet: Studio/Journey unavailable for Turkish
            "polish":     {"male": "pl-PL-Wavenet-B",   "female": "pl-PL-Wavenet-A"},    # Wavenet: best available for Polish
            "vietnamese": {"male": "vi-VN-Wavenet-B",   "female": "vi-VN-Wavenet-A"},    # Wavenet: best available for Vietnamese
            "thai":       {"male": "th-TH-Standard-A",  "female": "th-TH-Standard-A"},   # Standard: only option for Thai
            "indonesian": {"male": "id-ID-Wavenet-B",   "female": "id-ID-Wavenet-A"},    # Wavenet: best available for Indonesian
        }
        
        # Language codes for different languages (used for voice selection)
        self.language_codes = {
            "english": "en-US", "american": "en-US", "british": "en-GB", "indian": "en-IN",
            "spanish": "es-ES", "french": "fr-FR", "german": "de-DE", "portuguese": "pt-BR",
            "italian": "it-IT", "dutch": "nl-NL", "russian": "ru-RU", "chinese": "cmn-CN",
            "japanese": "ja-JP", "korean": "ko-KR", "arabic": "ar-XA", "hindi": "hi-IN",
            "turkish": "tr-TR", "polish": "pl-PL", "vietnamese": "vi-VN", "thai": "th-TH",
            "indonesian": "id-ID",
        }

        # Course language labels used in the frontend wizard (Step 2).
        self.course_language_to_accent = {
            "english": "english",
            "hindi": "hindi",
            "spanish": "spanish",
            "french": "french",
            "german": "german",
            "portuguese": "portuguese",
            "italian": "italian",
            "dutch": "dutch",
            "russian": "russian",
            "chinese (simplified)": "chinese",
            "chinese (traditional)": "chinese",
            "japanese": "japanese",
            "korean": "korean",
            "arabic": "arabic",
            "turkish": "turkish",
            "vietnamese": "vietnamese",
            "thai": "thai",
            "indonesian": "indonesian",
        }

        # Aliases to support language names, accents, and common language codes.
        self.language_aliases = {
            "en": "english",
            "en-us": "english",
            "en-gb": "british",
            "en-in": "indian",
            "es": "spanish",
            "es-es": "spanish",
            "fr": "french",
            "fr-fr": "french",
            "de": "german",
            "de-de": "german",
            "pt": "portuguese",
            "pt-br": "portuguese",
            "it": "italian",
            "it-it": "italian",
            "nl": "dutch",
            "nl-nl": "dutch",
            "ru": "russian",
            "ru-ru": "russian",
            "zh": "chinese",
            "zh-cn": "chinese",
            "zh-tw": "chinese",
            "ja": "japanese",
            "ja-jp": "japanese",
            "ko": "korean",
            "ko-kr": "korean",
            "ar": "arabic",
            "ar-xa": "arabic",
            "hi": "hindi",
            "hi-in": "hindi",
            "tr": "turkish",
            "tr-tr": "turkish",
            "pl": "polish",
            "pl-pl": "polish",
            "vi": "vietnamese",
            "vi-vn": "vietnamese",
            "th": "thai",
            "th-th": "thai",
            "id": "indonesian",
            "id-id": "indonesian",
        }
    
    def generate_audio(self, text: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate audio from text using Google Gemini TTS
        Automatically handles text chunking if text exceeds 5,000 character limit
        
        Options:
        - accent: "american" (default), "british", "indian"
        - gender: "male", "female"
        - speed: float (0.5-2.0, default 1.0) - Note: Gemini TTS may have limited speed control
        """
        start_time = time.time()
        log_api_call("Google TTS", "generate_audio", 0, False)
        
        try:
            options = options or {}
            accent = self.normalize_language_key(options.get("accent") or options.get("language") or "english")
            gender = options.get("gender", "male").lower()
            speed = options.get("speed", 1.0)
            
            # Get voice name and language code
            voice_name = self._get_voice_name(accent, gender)
            language_code = self.language_codes.get(accent, "en-US")
            
            # Check text length BEFORE processing - Google Cloud TTS limit is 5,000 BYTES
            # Always chunk on RAW text bytes so that SSML markup added during processing
            # never inflates an already-borderline chunk past the API limit.
            text_bytes = len(text.encode('utf-8'))
            # Use 3200 bytes as safe threshold: SSML markup (<break> tags etc.) can add
            # up to ~25% overhead, so 3200 raw bytes → ~4000 bytes after SSML processing,
            # well within the 5000-byte Google Cloud TTS limit.
            if text_bytes > 3200:
                logger.info(f"Text byte size ({text_bytes} bytes) exceeds safe threshold (3200 bytes). Will chunk before processing.")
                return self._generate_audio_chunked(text, voice_name, language_code, accent, gender, speed)

            # Process text for natural pauses (target 140-160 WPM)
            processed_text = self._process_text_for_audio(text, speed)

            # Sanity-check: if SSML expansion pushed us over the limit, fall back to chunking
            # on the original RAW text (not processed_text) to avoid double-SSML processing.
            processed_bytes = len(processed_text.encode('utf-8'))
            if processed_bytes > 4800:
                logger.info(f"Processed text byte size ({processed_bytes} bytes) exceeds safe limit. Will chunk from raw text.")
                return self._generate_audio_chunked(text, voice_name, language_code, accent, gender, speed)
            
            # Generate audio using Google Cloud TTS REST API
            # Pass speed and gender parameters
            audio_data = self._generate_audio_via_rest_api(
                processed_text,
                voice_name,
                language_code,
                speed,
                gender
            )
            
            duration = time.time() - start_time
            log_api_call("Google TTS", "generate_audio", duration, True)
            
            # Estimate audio duration
            estimated_duration = self._estimate_audio_duration(text, speed)
            
            return {
                "audio_data": audio_data,
                "mime_type": "audio/mpeg",  # Gemini TTS typically returns MP3
                "duration_seconds": estimated_duration,
                "voice_id": voice_name,  # Return voice name for compatibility
                "accent": accent,
                "gender": gender
            }
        except Exception as error:
            duration = time.time() - start_time
            log_api_call("Google TTS", "generate_audio", duration, False, error)
            
            text_len = len(text) if 'text' in locals() else (len(processed_text) if 'processed_text' in locals() else 0)
            error_str = str(error).lower()
            error_full = str(error)
            
            logger.error(f"Failed to generate audio (text length: {text_len} chars): {error}", exc_info=True)
            
            # Provide helpful error messages
            if 'authentication' in error_str or 'api key' in error_str or '401' in error_full or '403' in error_full:
                raise ValueError(
                    f"Google TTS API authentication error: {str(error)}\n\n"
                    f"Please check your API key in the environment variables."
                ) from error
            elif 'rate limit' in error_str or '429' in error_full:
                raise ValueError(
                    f"Google TTS API rate limit exceeded: {str(error)}\n\n"
                    f"Please wait a moment and try again."
                ) from error
            elif 'quota' in error_str:
                raise ValueError(
                    f"Google TTS API quota exceeded: {str(error)}\n\n"
                    f"Please check your Google Cloud billing and quota limits."
                ) from error
            elif '5000 bytes' in error_full or 'limit of 5000' in error_full or ('5000' in error_full and 'byte' in error_str):
                # Text exceeded 5000 byte limit - retry with chunking
                text_bytes = len(text.encode('utf-8')) if 'text' in locals() else len(processed_text.encode('utf-8')) if 'processed_text' in locals() else 0
                logger.warning(f"Text exceeded 5000 byte limit ({text_bytes} bytes). Retrying with chunking...")
                try:
                    return self._generate_audio_chunked(
                        processed_text if 'processed_text' in locals() else text,
                        voice_name,
                        language_code,
                        accent,
                        gender,
                        speed
                    )
                except Exception as chunk_error:
                    logger.error(f"Failed to generate chunked audio: {chunk_error}", exc_info=True)
                    raise ValueError(
                        f"Failed to generate audio from long text ({text_bytes} bytes). Error: {str(chunk_error)}\n\n"
                        f"Please check your Google Cloud billing and quota limits."
                    ) from chunk_error
            else:
                raise ValueError(
                    f"Failed to generate audio: {str(error)}\n\n"
                    f"Text length: {text_len} characters\n"
                    f"If this error persists, please check your API key and account status."
                ) from error
    
    def generate_module_audio(self, module_content: Dict, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate audio for entire module content
        Automatically handles long text by chunking
        No duration or word count restrictions - audio can be any length
        """
        try:
            # Extract ALL text from module (no truncation - content and audio are directly proportional)
            text = self._extract_text_from_module(module_content)
            
            word_count = len(text.split())
            estimated_duration = self._estimate_audio_duration(text, options.get("speed", 1.0) if options else 1.0)
            
            logger.info(f"Extracted text for audio: {len(text)} characters, {word_count} words")
            logger.info(f"Estimated audio duration: {estimated_duration}s (no restrictions - audio can be any length)")
            
            # Check text length and log warning if it's long
            if len(text) > GOOGLE_TTS_MAX_CHARS:
                logger.info(f"Text exceeds Google Cloud TTS limit ({len(text)} > {GOOGLE_TTS_MAX_CHARS} chars). Will automatically chunk.")
            
            # Generate audio (will auto-chunk if needed)
            audio_result = self.generate_audio(text, options)
            
            # Handle both single audio and chunked audio
            actual_duration = audio_result.get("duration_seconds", estimated_duration)
            
            # If chunked, calculate total duration from chunks
            if audio_result.get("is_chunked") and audio_result.get("audio_chunks"):
                logger.info(f"Audio generated as {len(audio_result['audio_chunks'])} separate chunks (no FFmpeg needed)")
                # Duration already estimated in chunked generation
                actual_duration = audio_result.get("duration_seconds", estimated_duration)
            
            # No restrictions - audio can be any length
            logger.info(f"✅ Generated audio duration: {actual_duration:.1f}s, word count: {word_count} words")
            
            return {
                **audio_result,
                "text": text,
                "word_count": word_count,
                "estimated_duration": estimated_duration,
                "within_duration_limit": True  # No restrictions
            }
        except Exception as error:
            logger.error(f"Failed to generate module audio: {error}", exc_info=True)
            raise
    
    def save_audio(self, audio_data: bytes, output_path: Path) -> Path:
        """Save audio data to file"""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(audio_data)
            logger.info(f"Audio saved to {output_path}")
            return output_path
        except Exception as error:
            logger.error(f"Failed to save audio: {error}", exc_info=True)
            raise

    def normalize_language_key(self, language_or_accent: Optional[str]) -> str:
        """
        Normalize user-selected course language/accent into an internal voice key.
        Falls back to English when the input is missing or unknown.
        """
        if not language_or_accent:
            return "english"

        raw = str(language_or_accent).strip().lower()
        if raw in self.voice_configs:
            return raw

        if raw in self.course_language_to_accent:
            return self.course_language_to_accent[raw]

        if raw in self.language_aliases:
            return self.language_aliases[raw]

        normalized = raw.replace("_", " ").strip()
        if normalized in self.course_language_to_accent:
            return self.course_language_to_accent[normalized]

        if normalized.startswith("chinese"):
            return "chinese"

        if normalized.startswith("portuguese"):
            return "portuguese"

        return "english"

    def get_supported_course_languages(self) -> List[str]:
        return [
            "English",
            "Hindi",
            "Spanish",
            "French",
            "German",
            "Portuguese",
            "Italian",
            "Dutch",
            "Russian",
            "Chinese (Simplified)",
            "Chinese (Traditional)",
            "Japanese",
            "Korean",
            "Arabic",
            "Turkish",
            "Vietnamese",
            "Thai",
            "Indonesian",
        ]
    
    def _get_voice_name(self, accent: str, gender: str) -> str:
        """Get voice name based on accent and gender"""
        accent_key = self.normalize_language_key(accent)
        gender_key = gender.lower().strip()
        
        logger.info(f"Selecting voice: accent='{accent_key}', gender='{gender_key}'")
        
        # Get accent config with fallback to American
        accent_config = self.voice_configs.get(accent_key, self.voice_configs["american"])
        
        # Get gender-specific voice (full voice name like "en-US-Wavenet-D")
        if gender_key not in accent_config:
            logger.warning(f"Gender '{gender_key}' not found in config for accent '{accent_key}', using 'male' as fallback")
            voice_name = accent_config.get("male", "en-US-Wavenet-D")
        else:
            voice_name = accent_config.get(gender_key)
        
        logger.info(f"Selected voice: '{voice_name}' for accent='{accent_key}', gender='{gender_key}'")
        
        return voice_name
    
    def _get_ssml_gender_from_voice_name(self, voice_name: str, gender: str) -> str:
        """
        Determine SSML gender from voice name and requested gender
        Google Cloud TTS voice naming: A/C/E = female, B/D/F = male
        """
        gender_lower = gender.lower().strip()
        
        # Use the requested gender directly (more reliable)
        if gender_lower == "male":
            return "MALE"
        elif gender_lower == "female":
            return "FEMALE"
        
        # Fallback: try to detect from voice name suffix
        # Voice names end with -A (female), -B (male), -C (female), -D (male), etc.
        if voice_name.endswith("-A") or voice_name.endswith("-C") or voice_name.endswith("-E"):
            return "FEMALE"
        elif voice_name.endswith("-B") or voice_name.endswith("-D") or voice_name.endswith("-F"):
            return "MALE"
        
        # Default fallback
        logger.warning(f"Could not determine gender from voice name '{voice_name}', defaulting to FEMALE")
        return "FEMALE"

    def _build_voice_candidates(self, voice_name: str, gender: str) -> List[str]:
        """
        Build fallback voice candidates for a requested gender.
        Keeps the original voice first, then tries same locale across common families/suffixes.
        """
        candidates: List[str] = [voice_name]
        parts = voice_name.split("-")
        if len(parts) < 4:
            return candidates

        locale = "-".join(parts[:-2])
        family = parts[-2]
        gender_key = gender.lower().strip()

        male_suffixes = ["B", "D", "F", "H", "J"]
        female_suffixes = ["A", "C", "E", "G", "I"]
        target_suffixes = male_suffixes if gender_key == "male" else female_suffixes

        families = [family] + [f for f in ("Wavenet", "Neural2", "Standard") if f != family]

        for fam in families:
            for suffix in target_suffixes:
                candidate = f"{locale}-{fam}-{suffix}"
                if candidate not in candidates:
                    candidates.append(candidate)

        return candidates
    
    # Common abbreviations/acronyms that must always be spelled out letter-by-letter.
    # Keys are uppercase; matching is case-insensitive in _normalize_text_for_tts.
    _SPELL_OUT_ABBREVS = {
        # Technology & IT
        "TCS", "IBM", "HP", "AI", "ML", "API", "UI", "UX", "URL", "HTTP", "HTTPS",
        "HTML", "CSS", "SQL", "NoSQL", "JSON", "XML", "CSV", "PDF", "IDE", "SDK",
        "OS", "PC", "VM", "VPN", "SaaS", "PaaS", "IaaS", "CI", "CD", "DevOps",
        "LMS", "CMS", "CRM", "ERP", "IoT", "AR", "VR", "GPU", "CPU", "RAM", "ROM",
        "SSD", "HDD", "USB", "LAN", "WAN", "DNS", "IP", "TCP", "SMTP", "FTP",
        "AWS", "GCP", "CLI", "GUI", "REST", "SOAP", "JWT", "OAuth", "SSO",
        # Business & Finance
        "CEO", "CFO", "CTO", "COO", "HR", "PR", "KPI", "OKR", "ROI",
        "B2B", "B2C", "SLA", "NDA", "IPO", "EMI", "GST", "VAT", "ATM", "PIN",
        "PAN", "TAN", "SEBI", "FEMA", "RBI", "NBFC", "MFI",
        # Education
        "MBA", "PhD", "BSc", "MSc", "BBA", "MCA", "BCA", "IIT", "IIM", "NIT",
        "CBSE", "ICSE", "UGC", "AICTE",
        # General / Government
        "USA", "UK", "EU", "UN", "WHO", "NASA", "FBI", "CIA", "NATO",
        "NGO", "CSR", "PPP", "GDP", "GNP", "FDI", "WTO", "IMF",
        # Medical
        "ICU", "OPD", "MRI", "CT", "ECG", "BP", "OTC", "FDA",
    }

    def _normalize_text_for_tts(self, text: str) -> str:
        """
        Convert plain text to SSML, wrapping abbreviations/acronyms so that
        Google Cloud TTS spells them out letter-by-letter instead of reading
        them as words.  Also handles other common pronunciation issues.

        Returns an SSML string (without the outer <speak> wrapper — that is
        added in _generate_audio_via_rest_api).
        """
        import re

        # Escape XML special characters FIRST (only in non-SSML regions).
        # We do a character-level pass later, so just note what needs escaping.
        def xml_escape(s: str) -> str:
            return (s
                    .replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;"))

        # Pattern: sequences of 2+ uppercase letters (and optional digits),
        # not already inside an SSML tag.  We also handle dot-separated
        # abbreviations like U.S.A. or e.g., i.e.
        abbrev_pattern = re.compile(
            r'\b'
            r'(?:'
            # dot-separated: U.S.A. or U.S.A (trailing dot optional)
            r'(?:[A-Z]\.){2,}[A-Z]?\.?'
            r'|'
            # solid caps: 2+ uppercase letters optionally followed by digits
            r'[A-Z]{2,}\d*'
            r')'
            r'\b'
        )

        def replace_match(m: re.Match) -> str:
            token = m.group(0)
            upper = token.replace(".", "").upper()
            # Spell out if it's in the known list OR it's 2-5 all-caps letters
            # (short enough that pronouncing as a word is almost always wrong)
            should_spell = (
                upper in self._SPELL_OUT_ABBREVS
                or (re.fullmatch(r'[A-Z]{2,5}', upper) is not None)
            )
            if should_spell:
                # Remove internal dots for the tag content (G.D.P. -> GDP)
                clean = upper
                return f'<say-as interpret-as="characters">{xml_escape(clean)}</say-as>'
            # Longer all-caps words (6+ letters, e.g. "INTRODUCTION") stay as-is
            return xml_escape(token)

        # Run the abbreviation replacement FIRST (before symbol substitution so
        # tokens like "P&L" can still be matched by the acronym pattern if needed)
        result = abbrev_pattern.sub(replace_match, text)

        # Now replace remaining plain symbols with spoken equivalents.
        # These substitutions happen AFTER SSML tag injection so they only affect
        # the plain-text regions between tags.
        symbol_map = [
            ("%", " percent "),
            ("@", " at "),
            ("+", " plus "),
            ("=", " equals "),
            ("#", " number "),
            ("&", " and "),   # must come last to avoid double-escaping &amp;
        ]
        # Only replace symbols that are outside SSML tags
        def replace_outside_tags(s: str, sym: str, replacement: str) -> str:
            parts = re.split(r'(<[^>]+>)', s)
            return "".join(
                p.replace(sym, replacement) if not p.startswith("<") else p
                for p in parts
            )
        for sym, replacement in symbol_map:
            result = replace_outside_tags(result, sym, replacement)

        return result

    def _strip_ssml_tags(self, ssml: str) -> str:
        """Strip all SSML/XML tags and decode entities, returning plain text."""
        import re
        plain = re.sub(r'<[^>]+>', '', ssml)
        plain = (plain
                 .replace("&amp;", "&")
                 .replace("&lt;", "<")
                 .replace("&gt;", ">")
                 .replace("&quot;", '"')
                 .replace("&#39;", "'"))
        return plain

    def _process_text_for_audio(self, text: str, speed: float) -> str:
        """
        Process text to add natural pauses for 140-160 WPM and normalize
        abbreviations/acronyms so they are spelled out correctly by the TTS engine.
        Returns SSML markup (without outer <speak> tags).
        """
        import re

        # Step 1: Normalize abbreviations → SSML say-as tags
        processed = self._normalize_text_for_tts(text)

        # Step 2: Add pause breaks after sentence terminators.
        # Use SSML <break> tags instead of "..." since we are now in SSML mode.
        processed = processed.replace(". ", '. <break time="400ms"/> ')
        processed = processed.replace("? ", '? <break time="400ms"/> ')
        processed = processed.replace("! ", '! <break time="400ms"/> ')

        # Step 3: Shorter pause after commas before a capital letter (clause boundary)
        processed = re.sub(r",(?=\s+[A-Z])", ', <break time="200ms"/>', processed)

        return processed
    
    def _estimate_audio_duration(self, text: str, speed: float) -> int:
        """Estimate audio duration in seconds based on word count and speed"""
        words = len(text.split())
        wpm = AUDIO_WPM_DEFAULT * speed
        minutes = words / wpm if wpm > 0 else 0
        return int(minutes * 60)
    
    def _extract_text_from_section(self, section: Dict, section_title: str = None) -> str:
        """
        Extract text from a single section for audio narration.
        Includes section title, content, and all concepts within the section.
        """
        text_parts = []
        
        # Add section title
        if section_title:
            text_parts.append(f"{section_title}.")
        elif "sectionTitle" in section:
            text_parts.append(f"{section['sectionTitle']}.")
        
        # Add section content
        if "content" in section and section["content"]:
            text_parts.append(section["content"])
        
        # Extract ALL concepts with full explanations
        if "concepts" in section:
            for concept in section["concepts"]:
                # Concept title
                if "conceptTitle" in concept:
                    text_parts.append(f"{concept['conceptTitle']}.")
                
                # FULL explanation (no truncation)
                if "explanation" in concept and concept["explanation"]:
                    text_parts.append(concept["explanation"])
                
                # FULL scenario with all details
                if "scenario" in concept:
                    scenario = concept["scenario"]
                    scenario_parts = []
                    
                    if scenario.get('description'):
                        scenario_parts.append(f"Real-world scenario: {scenario['description']}")
                    if scenario.get('whatToDo'):
                        scenario_parts.append(f"What you should do: {scenario['whatToDo']}")
                    if scenario.get('whyItMatters'):
                        scenario_parts.append(f"Why this matters: {scenario['whyItMatters']}")
                    
                    if scenario_parts:
                        text_parts.append(" ".join(scenario_parts))
        
        return " ".join(text_parts).strip()
    
    def generate_section_audio(self, section: Dict, section_title: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate audio for a single section (section title + content + concepts).
        Returns audio data and metadata for the section.
        """
        try:
            # Extract text from section
            text = self._extract_text_from_section(section, section_title)
            
            if not text:
                logger.warning(f"Section '{section_title}' has no text to generate audio for")
                return {
                    "audio_data": None,
                    "text": "",
                    "word_count": 0,
                    "duration_seconds": 0,
                    "estimated_duration": 0
                }
            
            word_count = len(text.split())
            estimated_duration = self._estimate_audio_duration(text, options.get("speed", 1.0) if options else 1.0)
            
            logger.info(f"Generating audio for section '{section_title}': {len(text)} chars, {word_count} words, ~{estimated_duration:.1f}s")
            
            # Generate audio (will auto-chunk if needed)
            audio_result = self.generate_audio(text, options)
            
            # Handle both single audio and chunked audio
            actual_duration = audio_result.get("duration_seconds", estimated_duration)
            
            # If chunked, calculate total duration from chunks
            if audio_result.get("is_chunked") and audio_result.get("audio_chunks"):
                logger.info(f"Section audio generated as {len(audio_result['audio_chunks'])} separate chunks")
                actual_duration = audio_result.get("duration_seconds", estimated_duration)
            
            logger.info(f"✅ Generated section audio: {actual_duration:.1f}s, {word_count} words")
            
            return {
                **audio_result,
                "text": text,
                "word_count": word_count,
                "estimated_duration": estimated_duration,
                "duration_seconds": actual_duration
            }
        except Exception as error:
            logger.error(f"Failed to generate section audio for '{section_title}': {error}", exc_info=True)
            raise
    
    def _extract_text_from_module(self, module_content: Dict) -> str:
        """
        Extract COMPLETE text from module content structure for audio narration.
        Reads ALL content including full explanations, scenarios, and summaries.
        Audio will be automatically chunked if it exceeds Gemini TTS character limits.
        """
        text_parts = []
        
        if isinstance(module_content, str):
            # If already a string, return as-is (will be chunked if needed)
            return module_content
        
        # Add module title
        if "moduleTitle" in module_content:
            text_parts.append(f"{module_content['moduleTitle']}.")
        
        # Extract ALL content from sections (no truncation)
        if "sections" in module_content:
            for section in module_content.get("sections", []):
                # Add section title
                if "sectionTitle" in section:
                    text_parts.append(f"{section['sectionTitle']}.")
                
                # Add section content
                if "content" in section and section["content"]:
                    text_parts.append(section["content"])
                
                # Extract ALL concepts with full explanations
                if "concepts" in section:
                    for concept in section["concepts"]:
                        # Concept title
                        if "conceptTitle" in concept:
                            text_parts.append(f"{concept['conceptTitle']}.")
                        
                        # FULL explanation (no truncation)
                        if "explanation" in concept and concept["explanation"]:
                            text_parts.append(concept["explanation"])
                        
                        # FULL scenario with all details
                        if "scenario" in concept:
                            scenario = concept["scenario"]
                            scenario_parts = []
                            
                            if scenario.get('description'):
                                scenario_parts.append(f"Real-world scenario: {scenario['description']}")
                            if scenario.get('whatToDo'):
                                scenario_parts.append(f"What you should do: {scenario['whatToDo']}")
                            if scenario.get('whyItMatters'):
                                scenario_parts.append(f"Why this matters: {scenario['whyItMatters']}")
                            
                            if scenario_parts:
                                text_parts.append(" ".join(scenario_parts))
        
        # Add full summary
        if "summary" in module_content and module_content["summary"]:
            text_parts.append(f"Summary: {module_content['summary']}")
        
        extracted_text = " ".join(text_parts).strip()
        final_word_count = len(extracted_text.split())
        estimated_duration = self._estimate_audio_duration(extracted_text, 1.0)
        
        logger.info(f"Extracted FULL content: {final_word_count} words (estimated duration: ~{estimated_duration}s). Audio will be chunked automatically if needed.")
        
        # No duration restrictions - log estimated duration only
        logger.info(f"Estimated audio duration: {estimated_duration}s (no restrictions)")
        
        return extracted_text if extracted_text else "No content available."
    
    def convert_speed_preference(self, speed_preference: Any) -> float:
        """Convert speed preference to numeric value"""
        if isinstance(speed_preference, (int, float)):
            return max(0.5, min(2.0, float(speed_preference)))
        
        speed_map = {
            "slow": 0.8,
            "normal": 1.0,
            "fast": 1.2
        }
        
        return speed_map.get(str(speed_preference).lower(), 1.0)
    
    def _split_text_into_chunks(self, text: str, max_bytes: int = 4000) -> List[str]:
        """
        Split text into chunks that respect sentence boundaries and BYTE limits
        Google Cloud TTS has a 5000 BYTE limit, so we use 4000 bytes as safe threshold
        """
        text_bytes = len(text.encode('utf-8'))
        if text_bytes <= max_bytes:
            return [text]
        
        chunks = []
        current_chunk = ""
        current_chunk_bytes = 0
        
        # Split by sentences (., !, ?)
        sentences = []
        current_sentence = ""
        for char in text:
            current_sentence += char
            if char in '.!?':
                sentences.append(current_sentence.strip())
                current_sentence = ""
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
        
        # Group sentences into chunks based on BYTE size
        for sentence in sentences:
            sentence_bytes = len(sentence.encode('utf-8'))
            space_bytes = len(" ".encode('utf-8'))
            
            if current_chunk_bytes + sentence_bytes + space_bytes <= max_bytes:
                current_chunk += sentence + " "
                current_chunk_bytes += sentence_bytes + space_bytes
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                # If single sentence is too long, split by words
                if sentence_bytes > max_bytes:
                    words = sentence.split()
                    temp_chunk = ""
                    temp_chunk_bytes = 0
                    for word in words:
                        word_bytes = len(word.encode('utf-8'))
                        if temp_chunk_bytes + word_bytes + space_bytes <= max_bytes:
                            temp_chunk += word + " "
                            temp_chunk_bytes += word_bytes + space_bytes
                        else:
                            if temp_chunk:
                                chunks.append(temp_chunk.strip())
                            temp_chunk = word + " "
                            temp_chunk_bytes = word_bytes + space_bytes
                    current_chunk = temp_chunk
                    current_chunk_bytes = temp_chunk_bytes
                else:
                    current_chunk = sentence + " "
                    current_chunk_bytes = sentence_bytes + space_bytes
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        logger.info(f"Split text into {len(chunks)} chunks (original: {len(text)} chars, {text_bytes} bytes)")
        return chunks
    
    def _generate_audio_chunked(self, text: str, voice_name: str, language_code: str, accent: str, gender: str, speed: float) -> Dict[str, Any]:
        """
        Generate audio by splitting text into chunks and returning chunks separately
        No FFmpeg needed - chunks will be saved separately and played sequentially
        """
        # Use 3200 bytes per chunk so that SSML markup added by _process_text_for_audio
        # (which adds ~<break time="400ms"/> after every sentence, ~22 bytes each) never
        # pushes an individual chunk past the 5000-byte Google Cloud TTS API limit.
        chunks = self._split_text_into_chunks(text, max_bytes=3200)
        audio_chunks = []
        total_duration_estimate = 0
        
        logger.info(f"Generating audio for {len(chunks)} chunks (will save separately, no concatenation needed)...")
        
        for i, chunk in enumerate(chunks, 1):
            logger.info(f"Processing chunk {i}/{len(chunks)} ({len(chunk)} chars)...")

            # Normalize text (acronym expansion, pauses) before sending to TTS
            processed_chunk = self._process_text_for_audio(chunk, speed)

            # Generate audio for this chunk using REST API
            chunk_audio = self._generate_audio_via_rest_api(
                processed_chunk,
                voice_name,
                language_code,
                speed,
                gender
            )
            
            # Store chunk audio data directly (no concatenation needed)
            audio_chunks.append({
                "audio_data": chunk_audio,
                "chunk_number": i,
                "text": chunk
            })
            
            # Estimate duration based on text length (rough estimate: ~150 words per minute)
            word_count = len(chunk.split())
            estimated_duration = (word_count / 150.0) * 60.0 / speed
            total_duration_estimate += estimated_duration
            
            # Small delay between chunks to avoid rate limiting
            if i < len(chunks):
                time.sleep(0.5)
        
        logger.info(f"Successfully generated {len(audio_chunks)} audio chunks (estimated total duration: {total_duration_estimate:.1f}s)")
        
        return {
            "audio_chunks": audio_chunks,  # List of chunk audio data
            "mime_type": "audio/mpeg",
            "duration_seconds": int(total_duration_estimate),
            "voice_id": voice_name,
            "accent": accent,
            "gender": gender,
            "chunks_used": len(chunks),
            "is_chunked": True  # Flag to indicate multiple chunks
        }
    
    def _generate_audio_via_rest_api(self, text: str, voice_name: str, language_code: str, speed: float = 1.0, gender: str = "male") -> bytes:
        """
        Generate audio using Google Cloud Text-to-Speech REST API
        Uses distinct voices for different accents (American, British, Indian)
        """
        try:
            # Prepare the request payload for Google Cloud Text-to-Speech API
            # Format: https://cloud.google.com/text-to-speech/docs/reference/rest/v1/text/synthesize
            # Wrap in <speak> tags if the text contains SSML markup from
            # _process_text_for_audio; otherwise send as plain text.
            _has_ssml = "<" in text and ">" in text
            if _has_ssml:
                ssml_input = f"<speak>{text}</speak>"
                input_field = {"ssml": ssml_input}
            else:
                input_field = {"text": text}

            payload = {
                "input": input_field,
                "voice": {
                    "languageCode": language_code,
                    "name": voice_name,  # Full voice name like "en-US-Wavenet-D"
                    # Determine gender from requested gender parameter
                    "ssmlGender": self._get_ssml_gender_from_voice_name(voice_name, gender)
                },
                "audioConfig": {
                    "audioEncoding": "MP3",
                    "speakingRate": max(0.25, min(4.0, speed)),  # Speed control (0.25 to 4.0)
                    "pitch": 0.0,  # Pitch adjustment (-20.0 to 20.0 semitones)
                    "volumeGainDb": 0.0  # Volume gain (-96.0 to 16.0 dB)
                }
            }
            
            # Log the payload for debugging (especially for American female)
            ssml_gender = self._get_ssml_gender_from_voice_name(voice_name, gender)
            logger.info(f"🔊 Google Cloud TTS API call - Voice: {voice_name}, Language: {language_code}, Requested Gender: '{gender}', SSMLGender: '{ssml_gender}'")
            
            # CRITICAL FIX: Ensure ssmlGender matches the requested gender
            # Sometimes the voice name detection might be wrong, so force it based on requested gender
            if gender.lower() == "female":
                payload["voice"]["ssmlGender"] = "FEMALE"
                logger.info(f"✅ Forced SSMLGender to FEMALE for requested gender: {gender}")
            elif gender.lower() == "male":
                payload["voice"]["ssmlGender"] = "MALE"
                logger.info(f"✅ Forced SSMLGender to MALE for requested gender: {gender}")
            
            logger.debug(f"Google Cloud TTS API payload: {json.dumps(payload, indent=2)}")
            
            # Make REST API request
            headers = {
                "Content-Type": "application/json",
            }
            
            # Use the same API key as Gemini (works for all Google Cloud services in the same project)
            params = {
                "key": self.api_key
            }
            
            logger.info(f"Calling Google Cloud TTS API: voice={voice_name}, language={language_code}, text_length={len(text)}")
            
            response = self._post_with_retry(
                headers=headers,
                params=params,
                payload=payload,
            )
            
            # Check for errors
            if response.status_code != 200:
                error_msg = f"Google Cloud TTS API error: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data.get('error', {}).get('message', str(error_data))}"
                except:
                    error_msg += f" - {response.text[:200]}"
                
                # If authentication error, fallback to free gTTS
                if response.status_code == 401 or response.status_code == 403 or response.status_code == 400:
                    logger.warning(
                        f"Google Cloud TTS API unavailable ({response.status_code}), falling back to free gTTS: {error_msg}\n"
                        f"⚠️  NOTE: gTTS does NOT support gender selection — both male and female will sound the same. "
                        f"Enable the Cloud Text-to-Speech API for your API key to get true gender voices."
                    )
                    try:
                        from gtts import gTTS
                        import io
                        # extract language code prefix (e.g. 'en-US' -> 'en', 'es-ES' -> 'es')
                        lang = language_code.split('-')[0] if language_code else 'en'

                        # gTTS does not support SSML — strip any markup before passing
                        plain_text = self._strip_ssml_tags(text)

                        # gTTS has limited gender support via TLD:
                        # 'com.au' / 'co.uk' sound slightly different but are not true gender voices.
                        # For English, use 'com' (neutral/male-ish) for male and default for female.
                        gtts_tld = "com" if (lang == "en" and gender.lower() == "male") else None

                        # Sometimes gtts doesn't support the specific dialect, fallback to base lang
                        try:
                            # Try the exact lang like 'en-us' or 'es-es'
                            gtts_lang = language_code.lower()
                            tts_kwargs = {"text": plain_text, "lang": gtts_lang, "slow": (speed < 0.8)}
                            if gtts_tld:
                                tts_kwargs["tld"] = gtts_tld
                            tts = gTTS(**tts_kwargs)
                        except ValueError:
                            # Fallback to base language code like 'en' or 'es'
                            tts_kwargs = {"text": plain_text, "lang": lang, "slow": (speed < 0.8)}
                            if gtts_tld:
                                tts_kwargs["tld"] = gtts_tld
                            tts = gTTS(**tts_kwargs)
                            
                        fp = io.BytesIO()
                        tts.write_to_fp(fp)
                        audio_bytes = fp.getvalue()
                        logger.info(f"✅ Successfully generated free fallback audio via gTTS ({len(audio_bytes)} bytes)")
                        return audio_bytes
                    except Exception as fallback_err:
                        logger.error(f"gTTS fallback failed: {fallback_err}")
                        pass
                
                # If voice is invalid/not available, try alternatives for the same locale+gender.
                if response.status_code == 400 and ("voice" in error_msg.lower() or "not found" in error_msg.lower() or "invalid" in error_msg.lower()):
                    logger.warning(f"Voice '{voice_name}' may not be available, trying locale/gender alternatives...")
                    for alt_voice in self._build_voice_candidates(voice_name, gender)[1:]:
                        logger.info(f"Trying alternative voice: {alt_voice}")
                        payload["voice"]["name"] = alt_voice
                        retry_response = self._post_with_retry(
                            headers=headers,
                            params=params,
                            payload=payload,
                        )
                        if retry_response.status_code == 200:
                            logger.info(f"✅ Successfully used alternative voice: {alt_voice}")
                            response = retry_response
                            break
                        logger.debug(f"Alternative voice {alt_voice} failed: {retry_response.status_code}")
                
                if response.status_code != 200:
                    raise ValueError(error_msg)
            
            # Parse response
            response_data = response.json()
            
            # Extract audio data from response
            # Response format: {"audioContent": "base64-encoded-audio-data"}
            if "audioContent" in response_data:
                # Decode base64 audio data
                audio_bytes = base64.b64decode(response_data["audioContent"])
                logger.info(f"Successfully extracted audio from Google Cloud TTS API response ({len(audio_bytes)} bytes)")
                return audio_bytes
            
            # If we get here, the response format is unexpected
            raise ValueError(f"Unexpected response format from Google Cloud TTS API: {json.dumps(response_data)[:500]}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"REST API request failed: {e}", exc_info=True)
            raise ValueError(f"Failed to connect to Google Cloud TTS API: {str(e)}") from e
        except Exception as e:
            logger.error(f"Failed to generate audio via REST API: {e}", exc_info=True)
            raise ValueError(f"Failed to generate audio: {str(e)}") from e

    def _post_with_retry(self, headers: Dict[str, str], params: Dict[str, str], payload: Dict[str, Any]):
        """POST with retry on network timeouts."""
        attempt = 0
        while True:
            try:
                return requests.post(
                    self.api_url,
                    headers=headers,
                    params=params,
                    json=payload,
                    timeout=self.timeout
                )
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
                if attempt >= self.max_retries:
                    raise
                sleep_for = self.retry_backoff ** attempt
                logger.warning(f"TTS request failed (attempt {attempt + 1}/{self.max_retries + 1}): {exc}. Retrying in {sleep_for:.1f}s.")
                time.sleep(sleep_for)
                attempt += 1
    
    def _extract_audio_from_response(self, response) -> bytes:
        """
        Extract audio data from Gemini TTS API response
        Response may contain audio in different formats (base64, file URI, etc.)
        """
        try:
            # Check if response has parts
            if hasattr(response, 'parts') and response.parts:
                for part in response.parts:
                    # Check for inline audio data (base64)
                    if hasattr(part, 'inline_data') and part.inline_data:
                        if hasattr(part.inline_data, 'data'):
                            # Decode base64 audio data
                            audio_bytes = base64.b64decode(part.inline_data.data)
                            logger.info(f"Extracted audio from inline_data ({len(audio_bytes)} bytes)")
                            return audio_bytes
                    
                    # Check for file URI
                    if hasattr(part, 'file_data') and part.file_data:
                        if hasattr(part.file_data, 'file_uri'):
                            # For file URIs, we'd need to download the file
                            # This is less common but handle it if needed
                            logger.warning("File URI audio format not yet implemented - using inline_data")
            
            # Fallback: try to get raw response data
            if hasattr(response, 'text'):
                # If response is text, it might contain base64 encoded audio
                # This is a fallback - shouldn't normally happen
                logger.warning("Unexpected response format - attempting to extract audio from text")
            
            raise ValueError("Could not extract audio data from the text-to-speech service response")
        except Exception as error:
            logger.error(f"Failed to extract audio from response: {error}", exc_info=True)
            raise ValueError(f"Failed to extract audio from text-to-speech service response: {str(error)}") from error
    
    def list_available_voices(self, language: Optional[str] = None) -> List[Dict[str, str]]:
        """
        List configured Google Cloud TTS voices.
        If language is provided, return only voices for that language selection.
        """
        languages = self.get_supported_course_languages()

        if language and language.strip() and language.strip().lower() not in {"all", "*"}:
            languages = [language.strip()]

        voices: List[Dict[str, str]] = []
        for language_label in languages:
            accent_key = self.normalize_language_key(language_label)
            accent_config = self.voice_configs.get(accent_key, self.voice_configs["english"])

            male_voice = accent_config.get("male", "")
            female_voice = accent_config.get("female", "")
            if male_voice:
                voices.append({
                    "name": male_voice,
                    "description": f"{language_label} male voice",
                    "gender": "male",
                    "accent": accent_key,
                    "language": language_label,
                })
            if female_voice:
                voices.append({
                    "name": female_voice,
                    "description": f"{language_label} female voice",
                    "gender": "female",
                    "accent": accent_key,
                    "language": language_label,
                })

        logger.info(f"Returning {len(voices)} configured TTS voices (language filter: {language or 'all'})")
        return voices

