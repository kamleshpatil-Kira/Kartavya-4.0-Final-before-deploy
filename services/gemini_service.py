import google.generativeai as genai
import json
import re
from typing import Dict, Any, List
from config import GEMINI_API_KEY, GEMINI_MODEL, GENERATION_TIMEOUT
from utils.logger import logger, log_api_call
from utils.qa_validator import qa_validator
from utils.nerc_patches import get_nerc_patches, get_nerc_outline_patches, get_nerc_quiz_patches, get_nerc_kc_patches
import time

# ── Number word → digit converter (post-processing safety net) ──────────────
_NUM_ONES = {
    'zero':0,'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,
    'seven':7,'eight':8,'nine':9,'ten':10,'eleven':11,'twelve':12,
    'thirteen':13,'fourteen':14,'fifteen':15,'sixteen':16,
    'seventeen':17,'eighteen':18,'nineteen':19,
}
_NUM_TENS = {
    'twenty':20,'thirty':30,'forty':40,'fifty':50,
    'sixty':60,'seventy':70,'eighty':80,'ninety':90,
}
_ORDINALS = {
    'first':'1st','second':'2nd','third':'3rd','fourth':'4th',
    'fifth':'5th','sixth':'6th','seventh':'7th','eighth':'8th',
    'ninth':'9th','tenth':'10th','eleventh':'11th','twelfth':'12th',
    'thirteenth':'13th','fourteenth':'14th','fifteenth':'15th',
    'sixteenth':'16th','seventeenth':'17th','eighteenth':'18th',
    'nineteenth':'19th','twentieth':'20th','thirtieth':'30th',
    'fortieth':'40th','fiftieth':'50th','sixtieth':'60th',
    'seventieth':'70th','eightieth':'80th','ninetieth':'90th',
    'hundredth':'100th','thousandth':'1000th',
}

def _words_to_digits(text: str) -> str:
    """Convert written number words to digit form in a string."""
    if not isinstance(text, str):
        return text

    # Step 1: Compound ordinals e.g. "twenty-first" → "21st"
    compound_ord = re.compile(
        r'\b(twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)'
        r'[-\s](first|second|third|fourth|fifth|sixth|seventh|eighth|ninth)\b',
        re.IGNORECASE
    )
    def _replace_compound_ord(m):
        tens_val = _NUM_TENS[m.group(1).lower()]
        ones_map = {'first':1,'second':2,'third':3,'fourth':4,'fifth':5,
                    'sixth':6,'seventh':7,'eighth':8,'ninth':9}
        ones_val = ones_map[m.group(2).lower()]
        n = tens_val + ones_val
        suffix = {1:'st',2:'nd',3:'rd'}.get(n % 10, 'th')
        if 11 <= (n % 100) <= 13: suffix = 'th'
        return f"{n}{suffix}"
    text = compound_ord.sub(_replace_compound_ord, text)

    # Step 2: Simple ordinals ("first", "second", etc.)
    ord_pattern = re.compile(
        r'\b(' + '|'.join(_ORDINALS.keys()) + r')\b', re.IGNORECASE
    )
    text = ord_pattern.sub(lambda m: _ORDINALS[m.group(1).lower()], text)

    # Step 3: Compound cardinal "forty-three", "twenty one"
    compound_card = re.compile(
        r'\b(twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)'
        r'[-\s](one|two|three|four|five|six|seven|eight|nine)\b',
        re.IGNORECASE
    )
    def _replace_compound_card(m):
        return str(_NUM_TENS[m.group(1).lower()] + _NUM_ONES[m.group(2).lower()])
    text = compound_card.sub(_replace_compound_card, text)

    # Step 4: Hundreds — "one hundred", "three hundred"
    hundreds = re.compile(
        r'\b(one|two|three|four|five|six|seven|eight|nine)\s+hundred\b',
        re.IGNORECASE
    )
    text = hundreds.sub(lambda m: str(_NUM_ONES[m.group(1).lower()] * 100), text)

    # Step 5: Thousands — "one thousand", "ten thousand"
    thousands = re.compile(
        r'\b(one|two|three|four|five|six|seven|eight|nine|ten)\s+thousand\b',
        re.IGNORECASE
    )
    def _replace_thousands(m):
        w = m.group(1).lower()
        val = _NUM_ONES.get(w, 0) or _NUM_TENS.get(w, 0)
        return str(val * 1000)
    text = thousands.sub(_replace_thousands, text)

    # Step 6: Simple tens ("twenty", "thirty", etc.) — standalone
    tens_pattern = re.compile(
        r'\b(twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)\b',
        re.IGNORECASE
    )
    text = tens_pattern.sub(lambda m: str(_NUM_TENS[m.group(1).lower()]), text)

    # Step 7: Simple ones/teens ("zero" through "nineteen")
    ones_pattern = re.compile(
        r'\b(zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve'
        r'|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen)\b',
        re.IGNORECASE
    )
    text = ones_pattern.sub(lambda m: str(_NUM_ONES[m.group(1).lower()]), text)

    return text

def _clean_str(text: str) -> str:
    """Remove * and # then convert number words to digits."""
    return _words_to_digits(text.replace("*", "").replace("#", "").strip())

class GeminiService:
    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not configured")
        
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Try to get available models first
        available_models = self._get_available_models()

        # Use configured model or default to gemini-3-pro-preview (latest pro model)
        requested_model = GEMINI_MODEL or 'gemini-3-pro-preview'
        model_name = self._select_best_model(requested_model, available_models)
        
        try:
            self.model = genai.GenerativeModel(model_name)
            self.model_name = model_name
            logger.info(f"✅ Successfully initialized Gemini model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize model {model_name}: {e}")
            # Fallback to gemini-3-flash-preview which is most reliable
            logger.info("Attempting fallback to gemini-3-flash-preview...")
            try:
                self.model = genai.GenerativeModel('gemini-3-flash-preview')
                self.model_name = 'gemini-3-flash-preview'
                logger.info("✅ Successfully initialized fallback model: gemini-3-flash-preview")
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
                raise ValueError(f"Could not initialize any Gemini model. Available models: {available_models}")
        
        # Fallback models in order of preference (if quota issues occur)
        # Filter to only include models that are actually available
        all_fallbacks = ['gemini-3-flash-preview', 'gemini-3-pro-preview']
        self.fallback_models = [m for m in all_fallbacks if m in available_models and m != self.model_name]
        if not self.fallback_models:
            # If no fallbacks found, at least try gemini-3-flash-preview
            self.fallback_models = ['gemini-3-flash-preview'] if 'gemini-3-flash-preview' != self.model_name else []
        
        self.fallback_index = 0  # Track which fallback we're using
        self.generation_timeout = GENERATION_TIMEOUT
        logger.info(f"Initialized Gemini model: {self.model_name} with configured timeout: {GENERATION_TIMEOUT}s")
        logger.info(f"Available fallback models: {self.fallback_models}")
    
    def _get_available_models(self) -> list:
        """Get list of available models from the API"""
        try:
            models = genai.list_models()
            available = [m.name.split('/')[-1] for m in models if 'generateContent' in m.supported_generation_methods]
            logger.info(f"Found {len(available)} available models: {available}")
            return available
        except Exception as e:
            logger.warning(f"Could not list available models: {e}. Using default list.")
            # Return common model names as fallback
            return ['gemini-3-pro-preview', 'gemini-3-flash-preview', 'gemini-2.5-pro', 'gemini-2.5-flash']
    
    def _select_best_model(self, requested_model: str, available_models: list) -> str:
        """Select the best available model matching the request"""
        # Exact match
        if requested_model in available_models:
            return requested_model
        
        # Try variations
        variations = [
            requested_model,
            requested_model.replace('-pro', '-flash'),
            requested_model.replace('-flash', '-pro'),
            'gemini-3-pro-preview',     # Latest pro model
            'gemini-3-flash-preview',   # Latest flash model
            'gemini-2.5-pro',   # Previous pro model
            'gemini-2.5-flash', # Previous flash model
        ]
        
        for variant in variations:
            if variant in available_models:
                logger.info(f"Using {variant} instead of requested {requested_model}")
                return variant
        
        # If nothing matches, return the requested model anyway (will fail with clear error)
        logger.warning(f"Requested model {requested_model} not in available models. Will attempt anyway.")
        return requested_model
    
    def _switch_to_fallback_model(self):
        """Switch to fallback model if quota issues occur - tries fallback models in order"""
        # Skip fallback models that are the same as current model
        while self.fallback_index < len(self.fallback_models):
            fallback_model = self.fallback_models[self.fallback_index]
            if self.model_name == fallback_model:
                # Already using this model, try next one
                self.fallback_index += 1
                continue
            
            logger.warning(f"Switching from {self.model_name} to {fallback_model} due to quota/timeout issues")
            try:
                self.model = genai.GenerativeModel(fallback_model)
                old_model = self.model_name
                self.model_name = fallback_model
                self.fallback_index += 1
                logger.info(f"✅ Successfully switched from {old_model} to {fallback_model}")
                return True
            except Exception as e:
                logger.warning(f"Failed to switch to {fallback_model}: {e}. Trying next fallback...")
                self.fallback_index += 1
                continue
        
        logger.warning("No more fallback models available")
        return False
    
    def _generate_content_with_timeout(self, prompt: str, timeout: int = None, generation_config: Dict = None) -> Any:
        """Generate content with extended timeout handling"""
        try:
            # Set default generation config if not provided
            if generation_config is None:
                generation_config = {
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 32768,
                }
                
            # FORCE JSON mode at the API level to permanently solve structure errors (quotes/commas)
            generation_config["response_mime_type"] = "application/json"
            
            # Use configured timeout (default 600s) to override the SDK's default gRPC timeout (~60s)
            # This is critical for non-English content generation which takes significantly longer
            actual_timeout = timeout or self.generation_timeout
            logger.info(f"Calling Gemini API with timeout={actual_timeout}s...")
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config,
                request_options={'timeout': actual_timeout}
            )
            return response
        except Exception as e:
            # Re-raise to let retry logic handle it
            raise
    
    def generate_course_outline(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """Generate course outline with 4-5 modules"""
        start_time = time.time()
        log_api_call("Gemini", "generate_course_outline", 0, False)
        
        max_retries = 3  # Three retry attempts (non-English languages may need more retries)
        retry_delay = 10  # 10 second delay between retries (timeout is handled by request_options)
        
        for attempt in range(max_retries):
            try:
                prompt = self._build_outline_prompt(user_input)
                
                # Validate prompt is not empty
                if not prompt or not prompt.strip():
                    error_msg = "Generated prompt is empty. Check user_input data."
                    logger.error(f"{error_msg} User input keys: {list(user_input.keys())}")
                    raise ValueError(error_msg)
                
                logger.info(f"Generated prompt length: {len(prompt)} characters")
                logger.debug(f"Prompt preview (first 200 chars): {prompt[:200]}")
                
                # Validate prompt format
                if not isinstance(prompt, str):
                    error_msg = f"Prompt must be a string, got {type(prompt)}"
                    logger.error(error_msg)
                    raise TypeError(error_msg)
                
                # Check prompt size before sending
                prompt_size = len(prompt)
                if prompt_size > 50000:  # Warn if prompt is very large
                    logger.warning(f"Large prompt detected: {prompt_size} characters. This may cause quota issues.")
                
                logger.info(f"Generating course outline (attempt {attempt + 1}/{max_retries})...")
                outline_generation_config = {
                    "temperature": 0.2,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 32768,
                }
                response = self._generate_content_with_timeout(prompt, generation_config=outline_generation_config)
                
                duration = time.time() - start_time
                log_api_call("Gemini", "generate_course_outline", duration, True)
                logger.info(f"✅ Successfully generated course outline in {duration:.2f} seconds")
                
                return self._parse_outline_response(response.text)
                
            except Exception as error:
                duration = time.time() - start_time
                error_str = str(error).lower()
                error_details = str(error)
                prompt_size = len(prompt) if 'prompt' in locals() else 'unknown'
                
                # Check for quota/rate limit errors FIRST (before timeout/network checks)
                is_quota_error = (
                    'quota' in error_str or 
                    '429' in error_details or 
                    'rate limit' in error_str or
                    'quota_exceeded' in error_str or
                    'exceeded your current quota' in error_str or
                    ('quota' in error_str and ('10739' in error_details or '10000' in error_details or 'limit' in error_str))
                )
                
                # Track model switching state
                model_switched = False
                old_model_before_switch = self.model_name
                
                if is_quota_error:
                    # Try switching to fallback model (flash models use fewer credits/tokens)
                    model_switched = self._switch_to_fallback_model()
                    if model_switched and attempt < max_retries - 1:
                        logger.info(f"🔄 Switched to {self.model_name} model (uses fewer credits) - retrying on attempt {attempt + 1}/{max_retries}")
                        wait_time = retry_delay * (2 ** attempt)
                        time.sleep(wait_time)
                        continue
                    elif not model_switched and attempt < max_retries - 1:
                        # Already using fallback, but still getting quota error - wait and retry
                        logger.warning(f"Quota error with {self.model_name} model - waiting and retrying (attempt {attempt + 1}/{max_retries})")
                        wait_time = retry_delay * (2 ** attempt)
                        time.sleep(wait_time)
                        continue
                
                # Check for model not found errors (404)
                is_model_not_found = (
                    '404' in error_details or 
                    'not found' in error_str or 
                    'is not found for API version' in error_str or
                    'is not supported' in error_str
                )
                
                if is_model_not_found:
                    logger.error(f"Model not found error: {error}", exc_info=True)
                    # Try to switch to a known working model
                    old_model = self.model_name
                    model_switched = self._switch_to_fallback_model()
                    if model_switched and attempt < max_retries - 1:
                        logger.info(f"🔄 Model {old_model} not found. Switched to {self.model_name} - retrying on attempt {attempt + 1}/{max_retries}")
                        wait_time = retry_delay * (2 ** attempt)
                        time.sleep(wait_time)
                        continue
                    else:
                        # No fallback available or already tried
                        error_message = (
                            f"❌ **Model Not Found Error**\n\n"
                            f"The model '{old_model}' is not available or not supported.\n\n"
                            f"**Error:** {error_details}\n\n"
                            f"**Solutions:**\n"
                            f"1. The model name may be incorrect - check Google AI Studio for available models\n"
                            f"2. Set GEMINI_MODEL environment variable to a valid model\n"
                            f"3. Check your API key has access to the requested model\n"
                            f"4. Try using a flash model which is the most reliable"
                        )
                        raise ValueError(error_message) from error
                
                # Check for timeout errors (retryable) - but exclude quota-related "exceeded" messages
                is_timeout = (
                    ('timeout' in error_str or '504' in error_str or 'timed out' in error_str or 'deadline' in error_str) and
                    not is_quota_error  # Don't treat quota errors as timeouts
                )
                
                # Check for network/connection errors (retryable)
                is_network_error = ('failed to connect' in error_str or 'unavailable' in error_str or 
                                   '503' in error_details or 'socket is null' in error_str)
                
                # Retry on timeout or network errors - switch to flash model on timeout if using pro
                if (is_timeout or is_network_error) and attempt < max_retries - 1:
                    # On timeout, try switching to flash model if using pro (flash is faster)
                    if is_timeout and not model_switched:  # Only switch if not already switched for quota
                        old_model_before_switch = self.model_name
                        timeout_model_switched = self._switch_to_fallback_model()
                        if timeout_model_switched:
                            model_switched = True
                            logger.info(f"🔄 Switched to {self.model_name} model (faster) due to timeout - retrying on attempt {attempt + 1}/{max_retries}")
                    
                    wait_time = retry_delay * (2 ** attempt)  # Exponential backoff: 30s, 60s
                    logger.warning(
                        f"⏱️ {'Timeout' if is_timeout else 'Network'} error on attempt {attempt + 1}/{max_retries} "
                        f"(after {duration:.1f}s). Retrying in {wait_time} seconds..."
                    )
                    time.sleep(wait_time)
                    continue
                
                # Log error if not retrying
                log_api_call("Gemini", "generate_course_outline", duration, False, error)
                
                # Check for network/connection errors first (most common)
                if is_network_error:
                    logger.error(f"Network/connection error: {error}", exc_info=True)
                    raise ValueError(
                        f"❌ **Network Connection Error**\n\n"
                        f"Unable to connect to the content generation service. This is a connection issue, NOT about prompt size.\n\n"
                        f"Prompt size: {prompt_size} characters (this is normal/small).\n\n"
                        f"**Attempted {attempt + 1} times with retries.**\n\n"
                        f"**Solutions:**\n"
                        f"1. Check your internet connection\n"
                        f"2. Wait 30-60 seconds and try again\n"
                        f"3. Check if Google API services are temporarily down\n"
                        f"4. Try disabling VPN/firewall if active"
                    ) from error
                
                # Handle quota errors (already checked above, but handle final error message here)
                if is_quota_error:
                    logger.error(f"Quota exceeded error: {error}", exc_info=True)
                    error_message = f"❌ **API Quota Limit Reached**\n\n"
                    
                    # Extract specific quota info if available
                    if '10739' in error_details or '10000' in error_details:
                        error_message += f"Request exceeds the per-request credit limit.\n\n"
                    else:
                        error_message += f"API quota or rate limit exceeded.\n\n"
                    
                    # Check if we switched models
                    switched_model_name = self.model_name if model_switched and old_model_before_switch != self.model_name else None
                    error_message += (
                        f"Prompt size: {prompt_size} characters.\n\n"
                        f"**Attempted {attempt + 1} times with retries.**\n"
                        f"{f'✅ Automatically switched to {switched_model_name} model (uses fewer credits)' if model_switched and switched_model_name else ''}\n\n"
                        f"**Solutions:**\n"
                        f"1. Wait 1-2 minutes and retry (quota may reset)\n"
                        f"2. Try using a flash model (uses fewer credits)\n"
                        f"3. Check quota/usage in Google AI Studio dashboard\n"
                        f"4. For free tier: Check daily/monthly limits in Google AI Studio"
                    )
                    raise ValueError(error_message) from error
                
                # Check for timeout errors
                elif is_timeout:
                    logger.error(f"Timeout error: {error}", exc_info=True)
                    switched_model_name = self.model_name if model_switched and old_model_before_switch != self.model_name else None
                    error_message = (
                        f"❌ **Request Timeout**\n\n"
                        f"The API request took too long to respond.\n\n"
                        f"Prompt size: {prompt_size} characters.\n\n"
                        f"**Attempted {attempt + 1} times with retries.**\n"
                        f"{f'✅ Automatically switched to {switched_model_name} model (faster)' if model_switched and switched_model_name else ''}\n\n"
                        f"**Solutions:**\n"
                        f"1. Wait a moment and try again\n"
                        f"2. Check your connection speed\n"
                        f"3. The API may be slow - retry in a minute\n"
                        f"{'4. Already using flash model - the service may be experiencing high load' if model_switched else '4. Consider using a flash model (faster)'}"
                    )
                    raise ValueError(error_message) from error
                
                logger.error(f"Failed to generate course outline: {error}", exc_info=True)
                raise
    
    def generate_module_content(self, module_number: int, module_title: str, 
                               course_context: Dict, user_input: Dict, 
                               previous_content: Dict = None,
                               interactive_type: str = None,
                               is_regeneration: bool = False,
                               modules_covered_so_far: list = None,
                               law_ownership_map: dict = None,
                               scenario_type: str = "BAD_DECISION") -> Dict[str, Any]:
        """Generate detailed module content with retry logic for timeouts"""
        start_time = time.time()
        log_api_call("Gemini", "generate_module_content", 0, False)
        
        max_retries = 3  # Three retry attempts (non-English languages may need more retries)
        retry_delay = 10  # 10 second delay between retries (timeout is handled by request_options)
        
        for attempt in range(max_retries):
            try:
                prompt = self._build_module_content_prompt(
                    module_number, module_title, course_context, user_input, 
                    previous_content, interactive_type, is_regeneration,
                    modules_covered_so_far, law_ownership_map, scenario_type
                )
                
                logger.info(f"Generating Module {module_number} content (attempt {attempt + 1}/{max_retries})... This may take a few minutes.")
                
                # Generate content with extended timeout handling
                response = self._generate_content_with_timeout(prompt)
                
                duration = time.time() - start_time
                log_api_call("Gemini", "generate_module_content", duration, True)
                logger.info(f"✅ Successfully generated Module {module_number} content in {duration:.2f} seconds")
                
                return self._parse_module_content_response(response.text)
                
            except Exception as error:
                duration = time.time() - start_time
                error_str = str(error).lower()
                error_details = str(error)
                
                # Check for quota/rate limit errors first (comprehensive detection - before timeout check)
                is_quota_error = (
                    'quota' in error_str or 
                    '429' in error_details or 
                    'rate limit' in error_str or
                    'quota_exceeded' in error_str or
                    'exceeded your current quota' in error_str or
                    ('quota' in error_str and ('10739' in error_details or '10000' in error_details or 'limit' in error_str))
                )
                
                # Track model switching state
                model_switched = False
                old_model_before_switch = self.model_name
                
                if is_quota_error:
                    # Try switching to fallback model (flash models use fewer credits/tokens)
                    model_switched = self._switch_to_fallback_model()
                    if model_switched and attempt < max_retries - 1:
                        logger.info(f"🔄 Switched to {self.model_name} model (uses fewer credits) - retrying on attempt {attempt + 1}/{max_retries}")
                        wait_time = retry_delay * (2 ** attempt)
                        time.sleep(wait_time)
                        continue
                    elif not model_switched and attempt < max_retries - 1:
                        # Already using fallback, but still getting quota error - wait and retry
                        logger.warning(f"Quota error with {self.model_name} model - waiting and retrying (attempt {attempt + 1}/{max_retries})")
                        wait_time = retry_delay * (2 ** attempt)
                        time.sleep(wait_time)
                        continue
                        
                # Check for model not found errors (404)
                is_model_not_found = (
                    '404' in error_details or 
                    'not found' in error_str or 
                    'is not found for api version' in error_str or
                    'is not supported' in error_str
                )
                
                if is_model_not_found:
                    logger.error(f"Model not found error: {error}", exc_info=True)
                    # Try to switch to a known working model
                    old_model = self.model_name
                    model_switched = self._switch_to_fallback_model()
                    if model_switched and attempt < max_retries - 1:
                        logger.info(f"🔄 Model {old_model} not found. Switched to {self.model_name} - retrying on attempt {attempt + 1}/{max_retries}")
                        wait_time = retry_delay * (2 ** attempt)
                        time.sleep(wait_time)
                        continue
                    else:
                        error_message = (
                            f"❌ **Model Not Found Error**\n\n"
                            f"The model '{old_model}' is not available or not supported.\n\n"
                            f"**Error:** {error_details}\n\n"
                            f"**Solutions:**\n"
                            f"1. The model name may be incorrect - check Google AI Studio for available models\n"
                            f"2. Set GEMINI_MODEL environment variable to a valid model\n"
                            f"3. Check your API key has access to the requested model\n"
                            f"4. Try using a flash model which is the most reliable"
                        )
                        raise ValueError(error_message) from error

                if is_quota_error:  # Final fallback if quota failed
                    log_api_call("Gemini", "generate_module_content", duration, False, error)
                    logger.error(f"Quota exceeded error: {error}", exc_info=True)
                    error_message = f"❌ **API Quota Limit Reached**\n\n"
                    
                    # Extract specific quota info if available
                    if '10739' in error_details or '10000' in error_details:
                        error_message += f"Request exceeds the per-request credit limit.\n\n"
                    else:
                        error_message += f"API quota or rate limit exceeded.\n\n"
                    
                    switched_model_name = self.model_name if model_switched and old_model_before_switch != self.model_name else None
                    error_message += (
                        f"**Attempted {attempt + 1} times with retries.**\n"
                        f"{f'✅ Automatically switched to {switched_model_name} model (uses fewer credits)' if model_switched and switched_model_name else ''}\n\n"
                        f"**Solutions:**\n"
                        f"1. Wait 1-2 minutes and retry (quota may reset)\n"
                        f"2. Try using a flash model (uses fewer credits)\n"
                        f"3. Check quota/usage in Google AI Studio dashboard\n"
                        f"4. For free tier: Check daily/monthly limits in Google AI Studio"
                    )
                    raise ValueError(error_message) from error
                
                # Check for timeout errors (retryable) - but exclude quota-related "exceeded" messages
                is_timeout = (
                    ('timeout' in error_str or '504' in error_str or 'timed out' in error_str or 'deadline' in error_str) and
                    not is_quota_error  # Don't treat quota errors as timeouts
                )
                
                if is_timeout and attempt < max_retries - 1:
                    # On timeout, try switching to fallback model (flash is faster) if not already switched
                    if not model_switched:
                        old_model_before_switch = self.model_name
                        timeout_model_switched = self._switch_to_fallback_model()
                        if timeout_model_switched:
                            model_switched = True
                            logger.info(f"🔄 Switched to {self.model_name} model (faster) due to timeout - retrying on attempt {attempt + 1}/{max_retries}")
                    
                    # Exponential backoff with longer delays for content generation
                    wait_time = retry_delay * (2 ** attempt)  # 30s, 60s
                    logger.warning(
                        f"⏱️ Timeout error on attempt {attempt + 1}/{max_retries} "
                        f"(after {duration:.1f}s). Generating comprehensive content takes time. "
                        f"Retrying in {wait_time} seconds... (This is normal for large content)"
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    log_api_call("Gemini", "generate_module_content", duration, False, error)
                    logger.error(f"Failed to generate module content: {error}", exc_info=True)
                    
                    if is_timeout:
                        switched_model_name = self.model_name if model_switched and old_model_before_switch != self.model_name else None
                        error_message = (
                            f"❌ **Request Timeout (504)**\n\n"
                            f"The API request timed out after {duration:.1f} seconds.\n"
                            f"This can happen when generating comprehensive content.\n\n"
                            f"**Attempted {attempt + 1} times with retries.**\n"
                            f"{f'✅ Automatically switched to {switched_model_name} model (faster)' if model_switched and switched_model_name else ''}\n\n"
                            f"**Solutions:**\n"
                            f"1. The API may be experiencing high load - wait 2-3 minutes and try again\n"
                            f"2. Check your internet connection speed (slower connections may timeout)\n"
                            f"{'3. Already using flash model - the service may be experiencing high load' if model_switched else '3. Consider using a flash model (faster)'}\n"
                            f"4. Try generating during off-peak hours when API load is lower"
                        )
                        raise ValueError(error_message) from error
                    raise
    
    def generate_knowledge_check(self, module_content: Dict, module_title: str, language: str = "English", course_title: str = "", scenario: dict = None) -> Dict[str, Any]:
        """Generate knowledge check question for module"""
        start_time = time.time()
        log_api_call("Gemini", "generate_knowledge_check", 0, False)
        
        max_retries = 3
        retry_delay = 5

        for attempt in range(max_retries):
            try:
                prompt = self._build_knowledge_check_prompt(module_content, module_title, language, course_title, scenario)
                response = self._generate_content_with_timeout(prompt)
                
                duration = time.time() - start_time
                log_api_call("Gemini", "generate_knowledge_check", duration, True)
                
                parsed = self._parse_knowledge_check_response(response.text)
                # Clean symbols from knowledge check
                parsed = self._clean_knowledge_check_symbols(parsed)
                
                # Strict structural validation
                from utils.qa_validator import qa_validator
                kc_issues = qa_validator.validate_quiz_question(parsed, 1)
                if kc_issues:
                    raise ValueError(f"Strict knowledge check validation failed: {kc_issues}")
                
                return parsed
            except Exception as error:
                duration = time.time() - start_time
                error_str = str(error).lower()
                error_details = str(error)
                
                is_quota_error = ('quota' in error_str or '429' in error_details or 'rate limit' in error_str)
                is_timeout = (('timeout' in error_str or '504' in error_str or 'timed out' in error_str) and not is_quota_error)

                if (is_timeout or is_quota_error or "validation failed" in error_str) and attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    logger.warning(f"⏱️ Knowledge check generation failure on attempt {attempt+1}/{max_retries}. Retrying in {wait_time}s... Error: {error_details}")
                    if is_quota_error:
                        self._switch_to_fallback_model()
                    time.sleep(wait_time)
                    continue

                log_api_call("Gemini", "generate_knowledge_check", duration, False, error)
                logger.error(f"Failed to generate knowledge check after {attempt+1} attempts: {error}", exc_info=True)
                raise
    
    def generate_quiz(self, all_module_content: List[Dict], course_title: str, language: str = "English", num_questions: int = 10) -> Dict[str, Any]:
        """Generate final quiz with retry logic"""
        start_time = time.time()
        log_api_call("Gemini", "generate_quiz", 0, False)
        
        max_retries = 3
        retry_delay = 10

        for attempt in range(max_retries):
            try:
                prompt = self._build_quiz_prompt(all_module_content, course_title, language, num_questions)
                
                logger.info(f"Generating quiz with {num_questions} questions (attempt {attempt + 1}/{max_retries})...")
                
                # Use JSON mode and higher token limit for quiz generation
                generation_config = {
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 32768,
                    "response_mime_type": "application/json"
                }
                
                response = self._generate_content_with_timeout(prompt, generation_config=generation_config)
                
                duration = time.time() - start_time
                log_api_call("Gemini", "generate_quiz", duration, True)
                logger.info(f"✅ Quiz generated in {duration:.2f}s")
                
                parsed_quiz = self._parse_quiz_response(response.text)
                
                # Strict structural validation (Fix 10: Failure Control)
                from utils.qa_validator import qa_validator
                quiz_issues = qa_validator.validate_quiz(parsed_quiz)
                if quiz_issues:
                    raise ValueError(f"Strict quiz validation failed: {quiz_issues}")
                
                return parsed_quiz

            except Exception as error:
                duration = time.time() - start_time
                error_str = str(error).lower()
                error_details = str(error)
                
                is_quota_error = ('quota' in error_str or '429' in error_details or 'rate limit' in error_str)
                is_timeout = (('timeout' in error_str or '504' in error_str or 'timed out' in error_str) and not is_quota_error)

                if (is_timeout or is_quota_error) and attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    logger.warning(f"⏱️ Quiz generation {'timeout' if is_timeout else 'quota'} on attempt {attempt+1}/{max_retries}. Retrying in {wait_time}s...")
                    if is_quota_error:
                        self._switch_to_fallback_model()
                    time.sleep(wait_time)
                    continue

                log_api_call("Gemini", "generate_quiz", duration, False, error)
                logger.error(f"Failed to generate quiz after {attempt+1} attempts: {error}", exc_info=True)
                raise
    
    def scramble_quiz(self, existing_quiz: Dict, all_module_content: List[Dict], course_title: str, language: str = "English") -> Dict[str, Any]:
        """Scramble/regenerate quiz with new questions while keeping context relevant"""
        start_time = time.time()
        log_api_call("Gemini", "scramble_quiz", 0, False)
        
        try:
            prompt = self._build_scramble_quiz_prompt(existing_quiz, all_module_content, course_title, language)
            response = self._generate_content_with_timeout(prompt)
            
            duration = time.time() - start_time
            log_api_call("Gemini", "scramble_quiz", duration, True)
            
            return self._parse_quiz_response(response.text)
        except Exception as error:
            duration = time.time() - start_time
            log_api_call("Gemini", "scramble_quiz", duration, False, error)
            logger.error(f"Failed to scramble quiz: {error}", exc_info=True)
            raise
            
    def analyze_document_metadata(self, text: str) -> Dict[str, str]:
        """Analyze uploaded document text to extract verbatim course metadata for auto-fill.
        Anti-hallucination: all fields must be directly quoted from the source text.
        """
        start_time = time.time()

        # Word-count truncation — safer than char-count for multi-byte scripts (Devanagari=3 bytes/char)
        words = text.split()
        word_count = len(words)
        if word_count < 30:
            # Too little text to extract anything meaningful — skip Gemini, return empty
            logger.warning(
                f"Document text has only {word_count} words — content likely garbled/image-based. "
                "Skipping metadata extraction to avoid hallucination."
            )
            return {"detectedLanguage": "", "courseTitle": "", "targetAudience": "", "institute": "", "relevantLaws": ""}

        truncated_text = ' '.join(words[:3000]) if word_count > 3000 else text

        prompt = f"""You are a strict metadata extractor. Your ONLY job is to extract specific fields
from the SOURCE TEXT below. You must NEVER invent, infer, or hallucinate information
that is not explicitly present in the source text.

SOURCE TEXT (may be in any language — Hindi, English, Arabic, French, Chinese, etc.):
---
{truncated_text}
---

TASK: Extract the following fields from the SOURCE TEXT above.

FIELD RULES:

1. courseTitle:
   - If an exact title is written in the text, use it exactly as written.
   - If no title exists, formulate a clear, professional title describing the main topic (max 12 words).
   - Write the title in the SAME LANGUAGE as the source text.

2. targetAudience:
   - Identify who this document is intended for based on the context (e.g., "All Employees", "Racing Drivers", "Safety Officers", "Students").
   - If not explicitly stated, logically infer it based on the document's subject matter.

3. institute:
   - Extract any organization, company, or institution name mentioned. Return "" if none.

4. relevantLaws:
   - Locate any mention of laws, regulations, compliance standards, or guidelines (e.g., "FMVSS 126", "OSHA 29 CFR 1910", "ISO 9001").
   - Ensure the EXACT standard name or perfect match is fetched based on the text. If the text mentions "FMVSS 126", output exactly that.

5. detectedLanguage:
   - The primary language of the SOURCE TEXT (e.g., "Hindi", "English", "Arabic").

6. analysisNotes:
   - 1-2 sentences explaining what gave away the audience or context, or stating 'No clear audience found'.
   - This prevents silent hallucination of an audience when none is present.

CRITICAL RULES:
- Return ONLY this JSON — no explanation, no extra text before or after:
- NO markdown fences or trailing commas.
{{
  "courseTitle": "...",
  "targetAudience": "...",
  "institute": "...",
  "relevantLaws": "...",
  "detectedLanguage": "...",
  "analysisNotes": "..."
}}
"""

        try:
            generation_config = {
                "temperature": 0.0,  # zero temp — purely extractive, no creativity
                "top_p": 1.0,
                "response_mime_type": "application/json"
            }

            response = self._generate_content_with_timeout(prompt, generation_config=generation_config)

            duration = time.time() - start_time
            log_api_call("Gemini", "analyze_document_metadata", duration, True)

            result = self._parse_json_response(response.text)
            logger.info(
                f"Document metadata extracted: lang={result.get('detectedLanguage')} "
                f"title='{result.get('courseTitle')}' audience='{result.get('targetAudience')}'"
            )
            return result
        except Exception as error:
            duration = time.time() - start_time
            log_api_call("Gemini", "analyze_document_metadata", duration, False, error)
            logger.error(f"Failed to analyze document metadata: {error}", exc_info=True)
            return {}
    
    def analyze_existing_course(self, extracted_content: str, file_type: str = 'unknown') -> Dict[str, Any]:
        """Deep analysis of extracted course content to build a CourseBlueprint for seeded regeneration"""
        start_time = time.time()
        log_api_call("Gemini", "analyze_existing_course", 0, False)

        truncated = extracted_content[:20000] if len(extracted_content) > 20000 else extracted_content

        prompt = f"""You are an expert instructional designer and course analyst.
You have been given the full extracted content of an existing course (file type: {file_type}).
Your task is to PRECISELY analyze and extract data from this content. You must NOT hallucinate, invent, or guess — only report what is explicitly present in the content.

Extracted Course Content:
---
{truncated}
---

Analyze the content above and return a JSON object with EXACTLY this structure:
{{
  "courseTitle": "The exact original course title as found in the content",
  "courseSubject": "One-line description of the subject domain",
  "detectedAudience": "Who this course is for — only if explicitly stated, else empty string",
  "detectedTone": "The tone/style of the original content (e.g., Professional, Conversational, Formal)",
  "complianceRefs": ["Only laws/standards explicitly mentioned in the content — do NOT invent"],
  "detectedModules": [
    {{
      "moduleTitle": "Exact module title as found in content",
      "keyTopics": ["Only topics explicitly covered in this module"],
      "learningObjectives": ["Objectives explicitly stated for this module"]
    }}
  ],
  "suggestedImprovements": "Write 3–5 sentences describing what is specifically missing,\nunclear, or weak in this course. Name the actual topics or sections that are absent.\nDo not write generic praise followed by soft suggestions.",
  "detectedLanguage": "The language of the original content (e.g., English, Spanish)",
  "estimatedModuleCount": 0
}}

CRITICAL RULES — VIOLATION = FAILURE:
1. COUNT THE ACTUAL MODULES: Set estimatedModuleCount to the EXACT number of distinct modules/chapters/units you can count in the provided content. Do NOT default to 4. If there is 1 module, return 1. If there are 7, return 7. If there are 10, return 10.
2. The detectedModules array MUST have exactly estimatedModuleCount items — one per detected module/chapter/unit.
3. NEVER hallucinate. Only report content that actually exists in the extracted text above.
4. If a field cannot be determined from the content, return an empty string or empty array for it.
5. Return ONLY valid JSON. No markdown fences, no commentary."""

        try:
            generation_config = {
                "temperature": 0.3,
                "top_p": 0.95,
                "max_output_tokens": 8192,
                "response_mime_type": "application/json"
            }
            response = self._generate_content_with_timeout(prompt, generation_config=generation_config)
            duration = time.time() - start_time
            log_api_call("Gemini", "analyze_existing_course", duration, True)
            blueprint = self._parse_json_response(response.text)
            logger.info(f"Course blueprint extracted: '{blueprint.get('courseTitle')}' with {len(blueprint.get('detectedModules', []))} modules")
            return blueprint
        except Exception as error:
            duration = time.time() - start_time
            log_api_call("Gemini", "analyze_existing_course", duration, False, error)
            logger.error(f"Failed to analyze existing course: {error}", exc_info=True)
            return {}

    def _acronym_shortform_rule(self) -> str:
        """Shared prompt rule for acronym expansion clarity — cross-module, title-aware."""
        return """ACRONYM & SHORTFORM CLARITY RULE — MANDATORY:

RULE 1 — FIRST-USE EXPANSION:
Whenever any shortform or acronym appears for the first time anywhere in the course, write its full form first, then the shortform in parentheses.
   CORRECT: "North American Electric Reliability Corporation (NERC) sets the standards..."
   CORRECT: "Food and Drug Administration (FDA) requires..."
   WRONG:   "NERC sets the standards..." (no full form on first use)
After the first mention, the shortform alone is permitted for the rest of the course.

RULE 2 — COURSE TITLE SCOPE (CRITICAL):
If the course title itself contains an abbreviation (e.g., "NERC Compliance Training", "OSHA Safety Course"), that abbreviation MUST be expanded the very FIRST time it appears in the body content — even though it was already in the title.
The title does NOT count as a first-mention definition. The expansion MUST appear in the actual course text.

RULE 3 — CROSS-MODULE FIRST-USE (CRITICAL):
"First mention" means ACROSS THE ENTIRE COURSE, not per module or per section.
Once an acronym has been expanded in Module 1, it must NEVER be re-expanded in Module 2, 3, or any later module.
Later modules must use the shortform only.
   WRONG: Defining "NERC" in Module 1 AND again in Module 3.
   RIGHT:  Defining "NERC" once in Module 1; Modules 2, 3, 4... use "NERC" only.

RULE 4 — MODULE 1 OWNERSHIP:
All acronyms that appear in the course title or course description MUST be fully expanded in Module 1 on their first appearance.
Module 1 owns the definitions. Subsequent modules inherit them.
If a new acronym appears for the first time in Module 3, expand it there — only once.

RULE 5 — APPLIES TO ALL SHORTFORMS:
Apply this rule to ALL shortforms without exception: technical, legal, compliance, organizational, domain-specific, and regulatory terms.
Never assume the learner already knows any shortform."""

    def _number_as_digits_rule(self) -> str:
        """Shared prompt rule: smart number formatting based on context."""
        return """NUMBER FORMAT RULE — MANDATORY:
Use DIGITS (numeric) when the number represents:
   - Measurements or technical values: 100 degrees, 5 mg, 8 hours
   - Counts above 10: 12 modules, 25 questions, 150 participants
   - Ages, dates, years: 18 years old, 2024, January 3
   - Ordered lists, rankings, or step numbers: Step 1, 3rd attempt, Module 4
   - Ranges: 10–20 items, 5–7 minutes

Use WORDS (written out) when the number represents:
   - Small counts (1–10) in flowing narrative prose: "one important reason", "two key factors", "three main areas"
   - The start of a sentence: "Three modules cover this topic." (never start a sentence with a digit)
   - Idiomatic or formal expressions: "one-on-one meeting", "first impressions", "zero tolerance"

CONSISTENCY RULE: Within the same sentence or paragraph, do NOT mix digit and word formats for the same type of number.
   WRONG: "You have 3 quiz attempts... until all three attempts are used."
   RIGHT: "You have 3 quiz attempts... until all 3 attempts are used."
   RIGHT: "There are three key principles... each of these three principles..."

Only exception: proper names containing numbers (e.g., "Seven-Eleven", "Catch-22")."""

    def _sentence_simplicity_rule(self) -> str:
        """Shared prompt rule: prefer simple/compound sentences and plain words."""
        return """SENTENCE & VOCABULARY SIMPLICITY RULE — MANDATORY:
1. SENTENCE STRUCTURE — use in this order of preference:
   a. Simple sentence (1 main clause): "Employees must wash hands before handling food."
   b. Compound sentence (2 main clauses, joined by and/but/so/or): "Wash your hands, and then put on gloves."
   c. Complex sentence (main + subordinate clause): use ONLY when the relationship cannot be stated simply.
   NEVER write more than 2 clauses in a single sentence.
2. SENTENCE LENGTH: Keep every sentence under 20 words. If a sentence exceeds 20 words, split it into 2.
3. WORD CHOICE — always pick the simpler word:
   utilise → use | endeavour → try | subsequently → then/next | facilitate → help
   demonstrate → show | terminate → end/stop | ascertain → find out | commence → start
   optimal → best | fundamental → basic/key | implement → do/apply | comprehensive → full/complete
   If a shorter everyday word means the same thing, use it.
4. JARGON: Technical terms are allowed only if required for the job role.
   Every technical term must be explained in plain language on first use.
5. Do NOT sacrifice accuracy — if a technical term has no simple equivalent, keep it but explain it plainly."""

    def _build_outline_prompt(self, user_input: Dict) -> str:
        # Ensure all required fields have valid values - handle None values safely
        target_audience = (user_input.get('targetAudience') or '').strip() if user_input.get('targetAudience') else 'General'
        institute = (user_input.get('institute') or '').strip() if user_input.get('institute') else 'Not specified'
        relevant_laws = (user_input.get('relevantLaws') or '').strip() if user_input.get('relevantLaws') else 'US Federal Guidelines'
        tone = (user_input.get('tone') or '').strip() if user_input.get('tone') else 'Professional'
        course_title = (user_input.get('courseTitle') or '').strip() if user_input.get('courseTitle') else 'Course Title'
        processed_docs = user_input.get('processedDocuments')
        processed_docs = processed_docs.strip() if processed_docs and isinstance(processed_docs, str) else ''
        
        # Limit processed documents to avoid quota issues (max 2000 chars)
        docs_summary = ""
        if processed_docs:
            if len(processed_docs) > 2000:
                docs_summary = processed_docs[:1900] + "... [truncated - full content available during module generation]"
            else:
                docs_summary = processed_docs
        
        # Get number of modules from user input, default to 4 if not specified
        num_modules = user_input.get('numModules', 4)
        if not isinstance(num_modules, int) or num_modules < 1:
            num_modules = 1  # Default to 1 if invalid value
        elif num_modules > 20:
            num_modules = 20
        
        modules_template = '    {\n      "moduleNumber": 1,\n      "moduleTitle": "Module 1 Title (Introductory/Foundational concepts)",\n      "moduleRole": "FOUNDATION",\n      "estimatedDurationMinutes": 10,\n      "learningObjectives": ["objective1", "objective2", "objective3"],\n      "outlineSections": [{"sectionTitle": "1.1 Introduction..."}, {"sectionTitle": "1.2 Core Principle..."}]\n    }'
        if num_modules > 1:
            additional_modules = []
            for i in range(2, num_modules + 1):
                additional_modules.append(f'    {{\n      "moduleNumber": {i},\n      "moduleTitle": "Module {i} Title (Description of this module\'s focus)",\n      "moduleRole": "FRAMEWORK | BEHAVIOUR | CULTURE",\n      "estimatedDurationMinutes": 15,\n      "learningObjectives": ["objective1", "objective2", "objective3"],\n      "outlineSections": [{{"sectionTitle": "{i}.1 Intro..."}}, {{"sectionTitle": "{i}.2 Topic..."}}]\n    }}')
            modules_template += ',\n' + ',\n'.join(additional_modules)
        
        # ── Existing Course Blueprint (Regenerate mode) ──────────────────────────
        existing_blueprint = user_input.get('existingCourseBlueprint')
        blueprint_context = ""
        if existing_blueprint and isinstance(existing_blueprint, dict):
            detected_modules = existing_blueprint.get('detectedModules', [])
            module_list = "\n".join(
                f"  {i+1}. {m.get('moduleTitle', 'Unknown')} — Topics: {', '.join(m.get('keyTopics', [])[:3])}"
                for i, m in enumerate(detected_modules)
            )
            blueprint_context = f"""

=== ORIGINAL COURSE ANALYSIS (Regeneration Seed) ===
You are regenerating an IMPROVED VERSION of an existing course. Use this analysis as your foundation:
- Original Title: {existing_blueprint.get('courseTitle', 'Unknown')}
- Subject Domain: {existing_blueprint.get('courseSubject', '')}
- Original Audience: {existing_blueprint.get('detectedAudience', '')}
- Original Tone: {existing_blueprint.get('detectedTone', '')}
- Original Module Structure ({len(detected_modules)} modules detected):
{module_list}
- Compliance References: {', '.join(existing_blueprint.get('complianceRefs', [])) or 'None detected'}
- Key Improvements Required: {existing_blueprint.get('suggestedImprovements', '')}

INSTRUCTIONS FOR REGENERATION:
1. Keep the SAME subject domain and audience — this is an improved version, not a different course
2. Expand and deepen all key topics from the original
3. Improve learning objective quality — align each to Bloom's taxonomy action verbs
4. Add real-world scenarios and practical applications that were missing or shallow in the original
5. Generate exactly {num_modules} modules that logically cover the same domain with superior structure
6. The regenerated course should feel like a premium, professionally authored version of the original
=== END ORIGINAL COURSE ANALYSIS ==="""

        base_prompt = f"""You are an expert instructional designer creating a course outline. Generate a comprehensive course outline with exactly {num_modules} module{'s' if num_modules != 1 else ''}.

PRE-REASONING (do this silently before generating):
1. What does "{course_title}" actually refer to? If it references a framework, standard,
   regulation, character, or technical system — identify its real-world definition precisely.
2. Who is the least-experienced person in "{target_audience}"? What do they NOT already know?
3. What are the real-world consequences if someone in this audience ignores this topic?

CRITICAL CONTEXT UNDERSTANDING:
- Course Title/Topic: {course_title}
- You MUST thoroughly understand what this topic actually refers to
- If the topic mentions a character, show, movie, book, or cultural reference (e.g., "Shinchan", "Harry Potter", "Star Wars"), research and understand what it is
- Ensure you create content DIRECTLY related to the actual topic, not generic or unrelated content
- Properly identify if the topic is a cartoon character, educational concept, professional skill, etc.
- Pronounce and reference names correctly (e.g., "Shinchan" is a Japanese cartoon character named "Crayon Shin-chan", not "arts and supplies")

FULL COURSE CONFIGURATION — HONOUR EVERY ITEM:
- Modules requested     : EXACTLY {num_modules} module{'s' if num_modules != 1 else ''}
- Tone & Style          : {tone}
- Target Audience       : {target_audience}
- Organisation          : {institute}
- Laws/Compliance       : {relevant_laws}
- Flashcards enabled    : {'Yes — ' + str(user_input.get('numFlashcards', 0)) + ' total across course' if user_input.get('addFlashcards') else 'No'}
- Final Quiz enabled    : {'Yes — ' + str(user_input.get('numQuizQuestions', 10)) + ' questions' if user_input.get('addQuizzes') else 'No'}
- Language              : {user_input.get('courseLanguage', 'English')}
{f'- Reference Materials Summary: {docs_summary}' if docs_summary else ''}
{blueprint_context}

NO STATISTICS RULE — STRICT BAN:
Do NOT include any statistical data, percentages from studies or surveys, growth figures, year-specific data points, or numerical claims attributed to research.
BANNED: "43% of workers...", "In 2019, the rate increased by...", "A study found that 75%...", "According to a survey, 60%...", "Research shows a 30% decline..."
ALLOWED: Laws, regulations, legal references, definitions, procedures, best practices, institutional guidelines, and named standards.
If you need to emphasize importance, use qualitative language such as "a significant number of cases" or cite the law/regulation directly — NEVER invent a percentage or figure.

ANTI-HALLUCINATION RULES — VIOLATION = FAILURE:
1. Every law, statute, or compliance reference must actually exist. Do not invent regulation numbers or agency names.
2. If you are uncertain whether a law applies, describe the general principle without citing a specific code.
3. Do NOT fabricate historical events or quotes.
4. Module titles and learning objectives must precisely reflect what will be taught — no vague or generic filler.
5. Reference materials (if provided above) must be reflected accurately — do not extrapolate beyond what was provided.
6. CRITICAL TITLE LIMIT: All module titles MUST strictly be 5-6 words or fewer. DO NOT generate long titles.
TONE ENFORCEMENT — MANDATORY:
The selected tone is: {tone}
- "Professional": precise language, formal structure, authoritative voice.
- "Fun" / "Engaging": humor, upbeat phrasing, informal "you", relatable pop-culture analogies. Do NOT use emojis anywhere in the content.
- "Academic": rigorous citations, precise vocabulary (plain where possible), Bloom's-level objectives, formal structure.
- "Conversational": warm, direct, first and second person — like briefing a trusted colleague.
- Mixed tones: blend proportionally, lean slightly toward the first listed.
Do NOT use a bland, neutral AI voice. The persona is fully defined by the tone above.

COURSE QUALITY STANDARDS:
01. Design for the specific audience above. Write to the least-experienced person in the target group.
02. Identify the real-world stakes EARLY. What happens if the learner ignores this topic?
03. If laws/guidelines are provided, plan to cite them precisely in each relevant module.
04. Every module must have a clear "so what" — a reason the learner should care about THIS
    module's content specifically, not just the course in general.
    Example: not "This module covers safety procedures" but "Without these procedures, a single
    missed step caused the 2013 Lac-Mégantic rail disaster."
05. PROGRESSIVE COMPLEXITY — MANDATORY: Modules must form a logical escalation in cognitive complexity.
    - Module 1: Foundational concepts
    - Middle Modules: Application, nuance, and grey areas
    - Final Module: High-stakes synthesis and complex decision-making
    Module N must be tangibly harder and deeper than Module 1. Do not let the course feel flat or repetitive.
06. WHY AWARENESS: The outline must include a clear rationale for why this topic requires awareness — the specific gap, harm, or cost that exists without it. "It is important" is not acceptable. Name the actual consequence.
07. CULTURE & COMPETENCY: Frame the subject as a professional competency that affects performance evaluations, team effectiveness, and career trajectory — not a one-time compliance checkbox or optional soft skill.
08. BIAS RECOGNITION: At least one module must be structured to help learners surface and examine their own preconceptions about this topic — not just teaching facts, but actively shifting perspective.
09. MULTI-DIMENSIONAL STAKES: The course structure must connect to ALL of the following angles across its modules:
    a. Personal growth and career impact — how this competency affects the learner's performance and advancement
    b. Financial and legal risk — what it costs the organisation and the individual to get this wrong
    c. Necessity — why ignoring this topic has active consequences, not a neutral choice
    d. Skills — how mastering this topic directly develops a concrete, transferable professional skill
10. POLICY ANCHOR: The outline must plan for at least one section that references documented organisational policies (equal opportunity employer commitments, harassment prevention procedures) and what compliance looks like in daily behaviour.
11. TITLE CAPITALIZATION: Course and Module titles MUST be formatted using standard Title Case. CRITICAL: You MUST correctly and fully capitalize acronyms (e.g., "LGBTQIA+", "HIPAA", "OSHA", "AI", "IT") even if the user input provided them in lowercase (e.g., "lgbtQIA+"). Do not blindly echo the user's incorrect casing.
12. STRICT TITLE RULE: Do NOT append, merge, or combine the relevant law or standard name into the course title. The course title must remain short, punchy, and focused purely on the topic (e.g., "Hazardous Waste Safety Training", NOT "Hazardous Waste Safety Training: A Guide to RCRA Compliance"). If the user provided a title, preserve its core intent without bloating it.

REQUIREMENTS:
1. Generate EXACTLY {num_modules} module{'s' if num_modules != 1 else ''} — no more, no fewer
2. SPLIT course content LOGICALLY across all {num_modules} module{'s' if num_modules != 1 else ''} — no module should duplicate another

MODULE ROLE RULE — MANDATORY:
Each module must have ONE primary role. Assign it from these roles only:
  FOUNDATION — defines core terms and establishes baseline understanding
  FRAMEWORK  — explains the legal, policy, or structural context
  BEHAVIOUR  — shows what to DO and how to act in real situations
  CULTURE    — addresses team dynamics, psychological safety, and long-term habits

No two adjacent modules may share the same role.
The progression across modules MUST follow: FOUNDATION → FRAMEWORK → BEHAVIOUR → CULTURE (for 4+ module courses).
Write each module's role in the outline so the content generator knows what type it is.

3. Each module covers a COMPLETELY DISTINCT topic. No concept, definition, or example may be
   repeated from another module. If a concept was introduced in an earlier module, the later
   module must BUILD ON it — not restate it.
4. Each module must have 3–5 learning objectives written using simple, learner-friendly verbs.
   Use verbs that describe what the learner will KNOW or RECOGNISE after reading the course.
   APPROVED verbs: Understand, Recognize, Identify, Describe, Explain, Learn, Distinguish, Recall, Outline, Summarize.
   Do NOT use action/hands-on verbs like "Implement", "Analyze", "Evaluate", "Draft", "Calculate", "Self-Assess", "Apply", "Demonstrate", "Practice" — the learner is reading a course, not performing tasks.
   DO write: "Understand the key principles of X" or "Recognize the warning signs of Y" or "Identify the steps involved in Z".
   Do NOT write: "Implement X in your workflow" or "Analyze Y to identify Z" — these imply hands-on work that is not part of this course.
5. Content must be factually correct, contextually relevant to the SPECIFIC TOPIC
6. CRITICAL: Remove all asterisks (*) and hash symbols (#) from content
7. No hallucinations — especially around laws, compliance, and named references
8. If the topic is about a specific character/show/book/movie, modules must be about THAT specific topic
9. If laws are provided, plan how each module will integrate the legal context naturally
10. CRITICAL TITLE LIMIT: Module titles MUST be short, punchy, and maximum 5-6 words.
PLANNING FIELDS — MANDATORY:
1. REGULATORY OWNERSHIP MAP:
Assign each law/standard from {relevant_laws} to EXACTLY ONE module.
That module explains the law fully. All other modules reference it in application only — never re-explain it.
Format: "Full Law Name": "Module N: Title"

2. SCENARIO TYPE PLAN:
Assign one scenario type to each module. Enforce these rules:
- No two consecutive modules may use the same type.
- BAD_DECISION may appear in at most 40% of all modules.
Types: BAD_DECISION, TRADEOFF, GOOD_DECISION, CONSEQUENCE, AMBIGUOUS

3. CRITICAL ADJACENT TOPICS:
Identify 2-3 real-world situations where this course's topic inevitably intersects
with adjacent professional responsibilities. These must appear in at least one module.

4. TIME ESTIMATES:
Provide a realistic "estimatedDurationMinutes" for each module (typically between 5 and 15 minutes) based on how long it takes to read, comprehend, and complete a knowledge check for the objectives.

CONTENT SYNC RULE — MANDATORY:
The "courseDescription", "courseOverview", and "courseLearningObjectives" fields will be displayed together on a single page under "Purpose of this Training". They MUST be contextually aligned:
- courseDescription: A concise summary of the course (2-3 sentences).
- courseOverview: An expanded explanation that builds on the description — covering key topics, course structure, and what learners will gain (3-5 sentences). It must NOT contradict or repeat the description word-for-word but must feel like a natural continuation.
- courseLearningObjectives: Each bullet point must directly reflect a topic or skill mentioned in the description or overview. No objective should introduce a concept not covered in the paragraphs above it.
All three must read as one coherent, flowing section — not three disconnected blocks.

Format your response as JSON with this structure:
{{
  "courseTitle": "Short, punchy Course Title (do NOT merge the law/standard name into this)",
  "courseDescription": "Brief description (2-3 sentences summarizing the course)",
  "courseOverview": "Expanded overview that builds on the description — what learners will gain, key topics, course structure. 3-5 sentences. Must align with description.",
  "courseLearningObjectives": ["objective1", "objective2", "objective3", "objective4", "objective5"],
  "standardName": "The exact name, edition, and date of the standard (e.g., 'HIPAA 45 CFR Part 164', 'SQF Code Edition 9'). If none, put 'None'.",
  "jurisdiction": "The legal context or country (e.g., 'United States federal', 'European Union'). If not applicable, put 'Global'.",
  "requiredTopics": ["Topic 1 required by standard", "Topic 2 required by standard"],
  "roleConstraints": {{
    "allowed": ["Allowed practices or tools for the target audience"],
    "forbidden": ["Practices explicitly forbidden or out of scope for the target audience"]
  }},
  "regulatoryOwnershipMap": {{"Full Law Name": "Module N: Title"}},
  "scenarioTypePlan": {{"1": "CONSEQUENCE", "2": "TRADEOFF", "3": "BAD_DECISION"}},
  "criticalAdjacentTopics": ["Adjacent real-world topic 1", "Adjacent real-world topic 2"],
  "modules": [
{modules_template}
  ]
}}

EXAMPLE OF CORRECT OUTPUT (shown with 2 modules — scale up proportionally for {num_modules} module{'s' if num_modules != 1 else ''}):
{{
  "courseTitle": "Workplace Safety Essentials",
  "courseDescription": "This course equips employees with the foundational knowledge to identify and respond to workplace hazards. It covers legal obligations, safe practices, and team responsibilities.",
  "courseOverview": "Workplace Safety Essentials takes employees through the core principles of occupational health and safety. Starting with definitions and the legal framework under OSHA, the course progresses to hands-on recognition of hazards and the cultural habits that sustain a safe environment. By the end, learners can identify their responsibilities and apply the correct procedures when a hazard arises.",
  "courseLearningObjectives": ["Understand the key provisions of OSHA standards", "Recognize common workplace hazards", "Identify the correct reporting procedure for incidents", "Describe the role of personal protective equipment"],
  "standardName": "OSHA 29 CFR 1910 General Industry Standards",
  "jurisdiction": "United States federal",
  "requiredTopics": ["Hazard identification", "PPE requirements", "Incident reporting"],
  "roleConstraints": {{
    "allowed": ["Reporting hazards to a supervisor", "Using provided personal protective equipment"],
    "forbidden": ["Bypassing lockout/tagout procedures", "Ignoring posted safety signage"]
  }},
  "regulatoryOwnershipMap": {{"OSHA 29 CFR 1910 General Industry Standards": "Module 1: OSHA and the Law"}},
  "scenarioTypePlan": {{"1": "CONSEQUENCE", "2": "TRADEOFF"}},
  "criticalAdjacentTopics": ["Emergency evacuation procedures", "Workers compensation claims"],
  "modules": [
    {{
      "moduleNumber": 1,
      "moduleTitle": "OSHA and the Law",
      "moduleRole": "FOUNDATION",
      "estimatedDurationMinutes": 10,
      "learningObjectives": ["Understand what OSHA is and who it protects", "Recognize employer obligations under OSHA", "Identify the key rights employees have under the General Duty Clause"],
      "outlineSections": [{{"sectionTitle": "1.1 What Is OSHA and Why It Exists"}}, {{"sectionTitle": "1.2 Employer Obligations and Employee Rights"}}, {{"sectionTitle": "1.3 Consequences of Non-Compliance"}}]
    }},
    {{
      "moduleNumber": 2,
      "moduleTitle": "Recognizing Workplace Hazards",
      "moduleRole": "FRAMEWORK",
      "estimatedDurationMinutes": 12,
      "learningObjectives": ["Identify the 5 main categories of workplace hazards", "Describe the hierarchy of hazard controls", "Recognize when a hazard requires immediate reporting"],
      "outlineSections": [{{"sectionTitle": "2.1 The 5 Hazard Categories"}}, {{"sectionTitle": "2.2 Hierarchy of Controls"}}, {{"sectionTitle": "2.3 When and How to Report"}}]
    }}
  ]
}}
END OF EXAMPLE — Your response must follow this exact JSON structure for {num_modules} module{'s' if num_modules != 1 else ''}.

IMPORTANT: Generate EXACTLY {num_modules} module{'s' if num_modules != 1 else ''} in the modules array. Do not generate more or fewer.
{f'LANGUAGE REQUIREMENT: Generate ALL content (titles, descriptions, objectives, overview) in {user_input.get("courseLanguage", "English")}. Do not mix languages.' if user_input.get('courseLanguage', 'English') != 'English' else ''}"""

        nerc_outline = get_nerc_outline_patches(course_title)
        if nerc_outline:
            base_prompt += f"\n\n{nerc_outline}"

        return base_prompt
    
    def _build_module_content_prompt(self, module_number: int, module_title: str,
                                    course_context: Dict, user_input: Dict,
                                    previous_content: Dict = None,
                                    interactive_type: str = None,
                                    is_regeneration: bool = False,
                                    modules_covered_so_far: list = None,
                                    law_ownership_map: dict = None,
                                    scenario_type: str = "BAD_DECISION") -> str:
        # Normalize interactive_type to lowercase so schema_map lookup always works
        # (stored values may be "Tabs", "Accordion" etc. from older Gemini responses)
        if interactive_type:
            interactive_type = interactive_type.lower()
        # Pull ALL user-specified settings so Gemini knows exactly what was requested
        total_modules   = user_input.get('numModules', 4)
        tone_raw        = user_input.get('tone', 'Professional')
        tone            = tone_raw if isinstance(tone_raw, str) else (', '.join(tone_raw) if isinstance(tone_raw, list) else 'Professional')
        target_audience = (user_input.get('targetAudience') or 'General').strip()
        institute       = (user_input.get('institute') or 'Not specified').strip()
        relevant_laws   = (user_input.get('relevantLaws') or 'None provided').strip()
        course_language = user_input.get('courseLanguage', 'English')
        course_title    = course_context.get('title') or course_context.get('courseTitle') or user_input.get('courseTitle', 'Course')
        add_flashcards  = user_input.get('addFlashcards', False)
        add_quizzes     = user_input.get('addQuizzes', False)
        num_flashcards  = user_input.get('numFlashcards', 0)

        # Extract Dynamic Blueprint fields
        standard_name = course_context.get('standardName', 'None')
        jurisdiction = course_context.get('jurisdiction', 'Global')
        required_topics = course_context.get('requiredTopics', [])
        role_constraints = course_context.get('roleConstraints', {})
        role_allowed = ", ".join(role_constraints.get('allowed', [])) if role_constraints.get('allowed') else "All standard practices"
        role_forbidden = ", ".join(role_constraints.get('forbidden', [])) if role_constraints.get('forbidden') else "None specified"

        # Describe how this module fits in the full sequence — prevents overlap and thin content
        if module_number == 1:
            position_desc = "This is the FIRST module — it must lay the foundational knowledge and clearly set the stage for all subsequent modules."
        elif module_number == total_modules:
            position_desc = f"This is the FINAL module ({module_number} of {total_modules}) — it must synthesise, apply and cement everything learned in earlier modules. No need to re-introduce basics."
        else:
            position_desc = f"This is module {module_number} of {total_modules} — it must build directly on Module {module_number - 1} and prepare the learner for Module {module_number + 1}."

        # Build conditional regeneration block outside the f-string (Python 3.10 compat)
        _regen_block = ""
        if previous_content and user_input.get('preserve_topics'):
            _topics = ', '.join(user_input.get('preserve_topics', []))
            _regen_block = f"""
REGENERATION REQUIREMENT:
- Preserve these key topics from the previous version: {_topics}
- Expand and improve them -- do not just copy them.
"""

        nerc_instructions = get_nerc_patches(course_title, module_number)
        domain_patches = ""  # Placeholder for industry-specific rule injection

        # DO-NOT-REPEAT block
        _covered_block = ""
        if modules_covered_so_far:
            covered_list = "\n".join(f"  - {s}" for s in modules_covered_so_far)
            _covered_block = f"""
PREVIOUSLY COVERED — READ THIS BEFORE WRITING A SINGLE SENTENCE:
{covered_list}
For any concept above: if it is a law — only show how it applies to "{module_title}",
never re-explain it.
If it is a concept — BUILD ON IT or contrast it. Never restate its definition.
Self-check: "Did an earlier module define or introduce this?" If yes — skip the
definition and start from the NEXT step.
"""

        # Law ownership block
        _law_block = ""
        if law_ownership_map:
            module_owns = [law for law, mod in law_ownership_map.items()
                           if str(module_number) in mod.split(":")[0]]
            already_explained = [law for law, mod in law_ownership_map.items()
                                 if law not in module_owns]
            if module_owns:
                _law_block += f"\nLAWS TO EXPLAIN FULLY HERE: {', '.join(module_owns)}\n"
            if already_explained:
                _law_block += f"\nLAWS ALREADY EXPLAINED — reference in application only: {', '.join(already_explained)}\n"

        if is_regeneration:
            task_intro = f'Your ONLY task right now is to REGENERATE accurate, focused content for Module {module_number} — \nproduce completely new text for the same topic while preserving the exact existing structure.'
        else:
            task_intro = f'Your ONLY task right now is to generate rich, high-quality content for Module {module_number}: "{module_title}".'

        base_prompt = f"""Stay entirely within the scope of this module. Do not introduce concepts that belong in
other modules and do not repeat content already covered in earlier modules.
You are an expert instructional designer. {task_intro}

══════════════════════════════════════════════════════
COURSE CONFIGURATION — YOU MUST HONOUR ALL OF THESE
══════════════════════════════════════════════════════
Course Title        : {course_title}
Module              : {module_number} of {total_modules} — "{module_title}"
Target Audience     : {target_audience}
Organisation        : {institute}
Tone & Style        : {tone}
Course Language     : {course_language}
Relevant Laws       : {relevant_laws}
Flashcards enabled  : {'Yes — ' + str(num_flashcards) + ' total across course' if add_flashcards else 'No'}
Final Quiz enabled  : {'Yes' if add_quizzes else 'No'}

MODULE POSITION
{position_desc}
{_covered_block}{_law_block}
══════════════════════════════════════════════════════

TONE ENFORCEMENT — THIS IS MANDATORY:
The selected tone is: {tone}
- "Professional": precise language, formal structure, authoritative voice, third-person where suitable.
- "Fun" / "Engaging": humor, upbeat phrasing, informal "you", relatable pop-culture analogies. Do NOT use emojis anywhere in the content.
- "Academic": rigorous citations, precise vocabulary (plain where possible), passive voice acceptable, Bloom's-level objectives.
- "Conversational": write as if briefing a trusted colleague — warm, direct, first and second person.
- Mixed tones (e.g., "Professional, Fun"): blend both. Lean slightly toward the first listed.
Do NOT default to a bland, neutral AI voice. The persona is set by the tone above.

LEGAL REFERENCE LIMIT — MANDATORY:
Maximum 2 legal references per module. After each legal reference, write exactly 1 sentence
showing the human experience it protects — not the penalty for non-compliance.

BANNED frame: "Violation of Title VII can result in legal liability for the organisation."
REQUIRED frame: "Title VII exists because [specific person type] was being excluded from
[specific opportunity] — the law names that harm so workplaces can stop it."

Focus: workplace respect, psychological safety, and team effectiveness.
Legal context is background. Human experience is foreground.

CRITICAL TOPIC ACCURACY:
- ALL content in this module must be DIRECTLY about: {module_title}
- It must fit coherently within the course: {course_title}
- Audience: {target_audience} — write for their knowledge level and daily context.
- NEVER use placeholder content. NEVER reference generic situations unrelated to the topic.
- If the topic involves a specific law, person, place, show, character, or technique — verify it is real and accurate before writing about it.

NO STATISTICS RULE — STRICT BAN:
Do NOT include any statistical data, percentages from studies or surveys, growth figures, year-specific data points, or numerical claims attributed to research.
BANNED: "43% of workers...", "In 2019, the rate increased by...", "A study found that 75%...", "According to a survey, 60%..."
ALLOWED: Laws, regulations, legal references, definitions, procedures, best practices, institutional guidelines.
If you need to emphasize importance, use qualitative language or cite the law/regulation directly — NEVER invent a percentage or figure.

ANTI-HALLUCINATION RULES — VIOLATION = FAILURE:
1. Every fact, law reference, or claim you make must be something you can verify is real.
2. If you are uncertain about a fact, DO NOT state it as fact — rephrase to "evidence suggests" or omit it.
3. Laws: only cite laws that actually exist. If {relevant_laws} is vague, explain the topic's importance without inventing specific statute numbers.
4. No fictional case studies presented as real. Scenarios must be clearly illustrative, not fake news.
5. Do NOT copy boilerplate from other courses. Every sentence must be specific to this course and module.

COMPLIANCE & DOMAIN BLUEPRINT:
- Standard/Law Governing this Course: {standard_name}
- Jurisdiction / Legal Context: {jurisdiction}
- Target Audience Allowed Actions/Scope: {role_allowed}
- Target Audience Forbidden Actions/Scope: {role_forbidden}

UNIVERSAL COURSE GENERATION RULES — MANDATORY:
1. STATE THE STANDARD: If this is Module 1, you MUST state the full official name of the standard ({standard_name}) and its context. Reference it by name on first mention in every module.
2. VERIFY LAWS: Every law, acronym, and regulation must actually exist and strictly apply to the jurisdiction: {jurisdiction}. Do not invent laws or cite out-of-jurisdiction regulations.
3. ROLE BOUNDARIES: You must NEVER instruct the audience to perform actions listed in their "Forbidden Actions". Only teach within their "Allowed Actions".
4. IMPLEMENTATION DEPTH: Teach to implementation depth, not awareness. A learner must be able to perform the task after reading. 
5. METHODOLOGY SETUP: If teaching a multi-step methodology, always cover WHO is responsible and WHAT inputs/setup are needed before listing the steps.
6. CONCEPT STRUCTURE: Every major concept must follow this depth requirement: 1. Definition, 2. Real Example, 3. Decision Scenario, and 4. Failure Consequence.
7. COMPLIANCE INTEGRATION: If Relevant Laws are provided ({relevant_laws}), explain why the law was created (the real gap), state what happens to the individual/facility that ignores it, and show how it applies to what {target_audience} actually does. Do NOT just quote the regulation.
8. AMBIGUITY BAN: When teaching laws or policies, explicitly delineate the rights, protections, and responsibilities of ALL distinct parties involved.
9. HARM REDUCTION TACTICS: Whenever safety, compliance, or risk is discussed, you MUST provide practical, real-world harm reduction tactics and safe alternatives.

{nerc_instructions}
{domain_patches}
{_regen_block}

{self._acronym_shortform_rule()}
{self._number_as_digits_rule()}
{self._sentence_simplicity_rule()}

CONTENT QUALITY STANDARDS:
01. ROLE-BASED TARGETING: Design for the specific audience above ({target_audience}). Speak DIRECTLY to them. Tailor ALL examples, scenarios, and actionable steps specifically to their daily reality and responsibilities.

CONTENT RATIO RULE — MANDATORY:
Maintain a strict content balance: 70% practical application (what to do/how to do it), 20% explanation (why it matters), 10% background/theory. Focus heavily on executable steps.

FLEXIBLE LANGUAGE RULE — MANDATORY:
Unless describing a strict legal violation or fatal safety hazard, avoid rigid absolutes like "Always" or "Never". Instead, use nuanced phrasing such as "In most cases", "Best practice is to", or "Generally".

REAL-WORLD COMPLEXITY — MANDATORY (1 per module):
Include at least one situation where:
- The right answer is not immediately obvious
- A well-meaning person could genuinely get it wrong
- The mistake comes from confusion or habit, not bad intention

After showing this situation, explain:
1. WHY the mistake is natural (what instinct or assumption leads there)
2. WHAT changes the outcome (the specific habit or check that helps)

Do NOT write idealized scenarios where the right answer is obvious.
A learner who has never thought about this topic should be able to see themselves
making the mistake — that recognition is what makes the learning stick.

WHAT / WHY / WHAT NOW — every section must answer all three:
  WHAT: clearly define the concept
  WHY: state the real-world consequence of not knowing/doing this
  WHAT NOW: give the learner a concrete, executable next action
  
  POSITIVE CONSEQUENCE — add to WHAT NOW:
  For every behavioral guideline, include 1 sentence showing what improves when the
  learner applies it — not just what goes wrong if they don't.
  The positive outcome must be specific to a real workplace context (a meeting, an email,
  a one-on-one, a team conversation).

  BANNED: "This creates a more inclusive workplace."
  REQUIRED: "When a manager corrects a pronoun error in a team meeting, the affected
  colleague can focus on contributing instead of managing their discomfort."

CONCRETE BEFORE ABSTRACT: open each section with a real situation or example, then state the
principle, then the rule. Never open a section with a definition.
The pattern is: Story → Principle → Rule. Not: Definition → Explanation → Example.

NO ANSWER GIVEAWAYS: Do not pre-answer upcoming or potential knowledge check questions verbatim in the text. Teach the underlying principles thoroughly, but force the learner to apply logic during assessments rather than relying on verbatim reading comprehension.

EXECUTABLE STEPS: every instruction must be actionable by a stranger from your words alone. "Be careful" is never an instruction.

DAILY-WORK ANCHOR — MANDATORY for every concept:
Every concept must be anchored in one of these four contexts:
  - A MEETING (team standup, 1:1, all-hands)
  - AN EMAIL or written communication
  - A TEAM CONVERSATION (informal, hallway, Slack/Teams)
  - A MANAGER INTERACTION (feedback, task assignment, escalation)

State the context explicitly: "In a team meeting, when..." / "When writing an email to..."
Generic workplace references ("at work", "in the office") are NOT acceptable.

FAILURE AND RECOVERY — MANDATORY:
At least one concept per module must show:
1. Exactly what goes wrong when the correct procedure is skipped.
2. The specific real-world consequence — not a vague risk statement.
3. The step-by-step recovery action.
Do NOT write: "failure to comply may result in serious consequences."
DO write: "skipping step X causes Y to happen — to recover, do A, then B, then notify C."

HUMAN FACTORS — MANDATORY IN EVERY MODULE:
Include at least one concept that addresses how human behaviour affects this topic.
The treatment MUST include all three of these elements:
1. Name the specific cognitive bias or pressure affecting the learner in this module's context.
2. Explain WHY it leads to the error — describe the causal mechanism, not just the symptom.
3. Provide one specific procedural control that prevents the error — not "be more careful"
   but a concrete check, step, or habit.

AWARENESS & PERSONAL RELEVANCE — MANDATORY IN EVERY MODULE:
Address at least 3 of these 5 angles in your module content:

1. WHY AWARENESS: Name the specific gap or harm that exists when THIS module's topic is not understood — not a generic "it is important" statement, but the exact consequence of unawareness.
   BAD:  "Awareness of this topic matters in the workplace."
   GOOD: "When a hiring manager is unaware of affinity bias, they consistently pass over equally qualified candidates, the vacancy stays open longer, and the team loses diversity of thinking — all without anyone noticing the pattern."

2. CULTURE & COMPETENCY: Show how competence in this module's topic is a measurable professional skill that affects performance reviews, team output, and career trajectory — not a soft skill or nice-to-have.

3. BIAS RECOGNITION: Name at least one preconception or assumption that a typical {target_audience} member might hold about this topic. Then show the specific evidence or reasoning that corrects it. Do not lecture — let the correction follow naturally from a real situation.

4. MULTI-DIMENSIONAL STAKES: Connect the module's topic to at least 2 of the following:
   a. Individual career or financial impact (promotions, legal exposure, professional reputation)
   b. Organisational financial or legal risk (liability, turnover cost, regulatory penalty)
   c. Personal skill growth — how mastering this topic makes the learner concretely better at their job
   d. Necessity — name the specific negative outcome that happens when this competency is absent

5. POLICY ANCHOR: Reference that organisations maintain documented commitments — equal opportunity employer status, anti-harassment procedures, conduct policies — and show exactly what the learner's daily behaviour looks like when they honour or violate those commitments. Do NOT just cite policy numbers. Show the human action that policy describes.



VERBOSITY CONTROL — SENTENCE BUDGET SYSTEM:
Instead of word counts, every element of content follows a strict sentence-role budget.
Each sentence must serve exactly ONE of these four roles — no sentence may exist outside a role:

  [D] DEFINE    — state precisely what the concept/term is (1–2 sentences per concept max)
  [E] EVIDENCE  — give a concrete example or real-world proof (1–2 per concept). Do NOT use statistics or made-up percentages.
  [A] ACT       — tell the learner exactly what to do (1–2 actionable steps per concept)
  [C] CONSEQUENCE — what happens if they get it wrong, and how to recover (1 per concept)

Budget per concept explanation: exactly 2-3 sentences total.
Budget per section content:     exactly 3-4 sentences total.
Budget per scenario:            optional, exactly 3 sentences if used (description, whatToDo, whyItMatters).

STYLE GUIDE — ACTIVE VOICE ENFORCEMENT:
- Write in direct, active voice throughout.
- Open paragraphs with concrete subjects, not abstract nouns.
- Use specific verbs: "inspect," "record," "isolate," "verify" — not "ensure," "address," "utilise."
- One idea per sentence. Split any sentence with two clauses joined by "and."
- Replace hedge words ("may," "might," "could potentially") with committal language ("will," "causes," "requires").
- Do not open any sentence with: "It is important...", "It is worth mentioning...", "As we can see...", "In today's world...", "In conclusion...", "At the end of the day...", "This ensures that...", "It goes without saying..."

SPECIFICITY GATE — EVERY FACTUAL CLAIM:
When making a factual claim a learner should remember, attach exactly 1 specificity anchor:
  TIER 1: An institutional consensus statement or official definition ("The WHO defines a standard drink as...", "OSHA requires...")
  TIER 2: A directional claim with named authority ("Research in occupational health consistently shows...")
  BANNED: Any specific statistic, percentage, or numerical data point ("58% of...", "a 30% increase...")
  BANNED: Modal vagueness without any tier ("Research shows...", "Studies suggest...", "Many experts believe...")
Always use Tier 1 or Tier 2 — NEVER fabricate a figure or cite a percentage.

MODULE BOUNDARIES (prevents cross-module duplication):
- ONLY cover what belongs in Module {module_number} ("{module_title}")
NO-REPEAT RULE — MANDATORY:
If a concept was introduced in any earlier module, you MUST NOT define it again.
Reference it by name only. The only permitted exception: a 1-sentence callback if it directly
triggers the new concept.

BAD (Module 3 redefining what Module 1 already covered):
"Misgendering occurs when someone uses the wrong pronoun for a person..."

GOOD (Module 3 building on Module 1):
"When misgendering happens — even unintentionally — here is the recovery sequence..."

Apply this test before writing any sentence: "Did an earlier module already say this?"
If yes, cut it and start from the NEXT step.

TABLE UTILITY GATE — MANDATORY:
Tables are PROHIBITED unless the information meets at least ONE of:
  (a) Comparing 3 or more items across 2 or more attributes simultaneously (a real comparison table)
  (b) A decision matrix where row x column intersections each carry unique meaning
  (c) A quick-reference checklist a learner would print and keep at their desk
If your table just lists terms and definitions already in the surrounding prose —
DELETE IT and use a flipcard interactive block instead.

SELF-REFLECTION — MANDATORY (1 per module, optional per section):
At least one section per module must include a "reflectionPrompt" field — a genuine question
that asks the learner to connect the concept to their own experience.
This is NOT a quiz question. It has no right answer.
GOOD: "Think about the last time you were in a situation where this applied to you.
       What would you know now that you didn't then?"
BAD:  "What is the definition of X?" — this is a quiz question, not a reflection.
Add the field at the section level as: "reflectionPrompt": "Your question here?"

FORMATTING RULES:
No two consecutive sections within the same module may open with the same sentence pattern.
Vary the opening: use scenario, question, or direct instruction — not the same
type twice in a row.

Also: not every section should follow Story → Principle → Rule. Use that pattern for
the first section. For subsequent sections, lead with the consequence or the action first.
- USE MARKDOWN FORMATTING: You MUST use bold text (**text**) for emphasis, bullet points (-) for lists, and short subheadings (###) to break up large walls of text.
- READABILITY & TEXT DENSITY: Reduce overall text density by 30%. Paragraphs MUST be short (maximum 3 sentences). Use simple, conversational language (Grade 8 reading level). Avoid complex academic jargon.
"""

        if interactive_type:
            schema_map = {
                "tabs": '"tabs": [{"title": "Overview", "content": "string (2-3 sentences covering what this topic is)"}, {"title": "Deep Dive", "content": "string (2-3 sentences explaining the key mechanism or detail)"}, {"title": "Application", "content": "string (2-3 sentences on how to apply this in practice)"}]',
                "accordion": '"items": [{"question": "What is [key concept from this module]? (unique question covering aspect 1)", "answer": "Specific factual answer (1-2 sentences)"}, {"question": "Why does [key process/reason from this module] matter? (unique question covering aspect 2)", "answer": "Specific factual answer (1-2 sentences)"}, {"question": "How should [key action/application from this module] be done? (unique question covering aspect 3)", "answer": "Specific factual answer (1-2 sentences)"}]',
                "note": '"variant": "info" | "warning" | "tip", "text": "string (1-2 sentences)"',
                "table": '"headers": ["string"], "rows": [["string"]]',
                "flipcard": '"cards": [{"front": "Key Term 1 (short)", "back": "Definition or explanation (1-2 sentences)"}, {"front": "Key Term 2 (short)", "back": "Definition or explanation (1-2 sentences)"}, {"front": "Key Term 3 (short)", "back": "Definition or explanation (1-2 sentences)"}]'
            }
            schema_for_type = schema_map.get(interactive_type, '"data": "content"')
            
            interactive_block_json = f"""
  "interactiveBlock": {{
    "type": "{interactive_type}",
    "data": {{ {schema_for_type} }}
  }},"""
            if interactive_type == "tabs":
                interactive_block_json += """
TABS RULES (MANDATORY):
- Generate EXACTLY 3 tabs — no more, no less.
- Tab 1 (Overview): explain what the concept IS.
- Tab 2 (Deep Dive): explain HOW or WHY it works in detail.
- Tab 3 (Application): explain how to APPLY or USE it in practice.
- Each tab MUST have a unique title and unique content.
- Do NOT repeat content across tabs.
- Write in plain prose. You MAY use markdown for bold text, but do NOT use bullet lists within tabs."""
            if interactive_type == "flipcard":
                interactive_block_json += """
FLIPCARD RULES (MANDATORY):
- Generate EXACTLY 3 cards — no more, no less.
- Each card MUST cover a DIFFERENT key term or concept from THIS module.
- Front: a single short term, name, or concept (max 4 words).
- Back: a clear, factual definition or explanation (1-2 sentences).
- Do NOT repeat terms or definitions across cards.
- Ground every back in this module's specific facts."""
            if interactive_type == "accordion":
                interactive_block_json += """
ACCORDION RULES (MANDATORY):
- Generate EXACTLY 3 items — no more, no less.
- Each item MUST cover a DIFFERENT aspect of this module's topic (e.g. definition, reason, process).
- Each question and answer must be UNIQUE — do not repeat or rephrase another item.
- Ground every answer in the specific facts of this module — no generic filler.
- Remove the parenthetical role hints ("aspect 1", "aspect 2" etc.) from the final question text."""
        else:
            interactive_block_json = ""

        structure_lock = ""
        if is_regeneration:
            if interactive_type:
                structure_lock = f"""
REGENERATION MODE — STRUCTURE LOCK (HIGHEST PRIORITY):
══════════════════════════════════════════════════════
This is a REGENERATION. Produce completely fresh content. Preserve exact structure.

INTERACTIVE BLOCK: PRESENT — type "{interactive_type}"
  ✓ REQUIRED: You MUST include "interactiveBlock" in your JSON response exactly as shown in the template.
  ✓ Generate BRAND NEW text content for it — completely different from what was there before.
  ✗ Do NOT change the type from "{interactive_type}" to anything else.
  ✗ Do NOT omit the interactiveBlock — it is mandatory.

SECTION FLASHCARDS:
  ✗ Do NOT add 'flashcards' field to any section object.

OUTPUT RULES:
1. Only include JSON fields that appear in the template below.
2. "interactiveBlock" IS in the template — you MUST include it with new content.
3. Do NOT add 'flashcards' to sections.
4. Match the sentence budget exactly — do not expand.

Self-check before finalising your response:
✓ Did you include "interactiveBlock" with type "{interactive_type}" and fresh content? → GOOD
✗ Did you change the interactiveBlock type? → REVERT IT
✗ Did you omit interactiveBlock from the JSON? → ADD IT BACK
✗ Did you write more than 3-4 sentences in section 'content'? → TRIM IT
══════════════════════════════════════════════════════
"""
            else:
                structure_lock = """
REGENERATION MODE — STRUCTURE LOCK (HIGHEST PRIORITY):
══════════════════════════════════════════════════════
This is a REGENERATION. Produce completely fresh content. Preserve exact structure.

INTERACTIVE BLOCK: NOT PRESENT
  ✗ Do NOT add "interactiveBlock" anywhere in the JSON — not as empty object, not as null.

SECTION FLASHCARDS:
  ✗ Do NOT add 'flashcards' field to any section object.

OUTPUT RULES:
1. Only include JSON fields that appear in the template below.
2. Do NOT add "interactiveBlock" — it is not in the template.
3. Do NOT add 'flashcards' to sections.
4. Match the sentence budget exactly — do not expand.

Self-check before finalising your response:
✗ Did you add "interactiveBlock"? → REMOVE IT
✗ Did you add 'flashcards' to sections? → REMOVE THEM
✗ Did you write more than 3-4 sentences in section 'content'? → TRIM IT
══════════════════════════════════════════════════════
"""

        base_prompt += f"""
For content generation:
- FACT CHECKING: All content must be benchmark-level quality, accurate, and verifiably true. No false information or hallucinations.
- CONTENT VARIETY: Do not be repetitive. Mix explanations, bullet point data, notes, and different structural styles across concepts.
- SCENARIOS RULE (STRICT — follow exactly):
  • MAXIMUM ONE (1) scenario per section. Only the single concept in each section that benefits most from a real-world illustration may include the "scenario" field. Every other concept in that section MUST NOT include a "scenario" field at all.
  • MINIMUM ONE (1) scenario per module. The module as a whole must contain at least one scenario distributed across its sections. Do not produce a module with zero scenarios.
  • Only add a scenario where the concept is abstract, high-risk, or genuinely hard to understand without a concrete example. Do not add scenarios to self-evident or simple concepts.
  • VARY SCENARIO STRUCTURE: Do not use instances that are overly simplistic or formulaic. Inject high-stakes "Grey Areas" where choices are difficult.
  • CALCULATION/CHARTS: If the topic or objective involves calculations (e.g., BAC limit calculations, financial formulas), you MUST practically demonstrate the calculation step-by-step or include a structured markdown chart using the 'explanation' field.
  • SCENARIO CONTENT QUALITY — the "description" field MUST include:
    (a) A named character in a specific role (not "an employee" — use "Carlos, the receiving clerk")
    (b) A realistic pressure situation (time pressure, understaffing, conflicting priorities)
    (c) The cognitive reason the person makes the mistake (habit, overconfidence, assumption)

TYPED SCENARIO SYSTEM — MANDATORY:
The assigned scenario type for THIS module is: {scenario_type}

Use the type-specific instructions below to populate the 4 scenario fields:

BAD_DECISION (classic — character makes a mistake):
  description  = named character + pressure situation + cognitive reason for mistake
  whatToDo     = the specific correct action, stated as a direct instruction
  whyItMatters = the specific harm prevented by taking the correct action
  howToPrevent = one proactive habit that stops this from happening in the first place

TRADEOFF (two reasonable options with genuine costs — no obvious winner):
  description  = the situation + both options clearly stated, with the real constraint
  whatToDo     = "The principle that tips this decision is: [X]. Neither option is costless."
  whyItMatters = "Option A costs [X]. Option B costs [Y]. The difference is [what matters most]."
  howToPrevent = "Use this check before deciding: [specific question to ask yourself]"

GOOD_DECISION (positive modeling — character does it RIGHT under pressure):
  description  = the situation + the pressure that could have led to a mistake
  whatToDo     = what the character actually did that was correct
  whyItMatters = the specific positive outcome that resulted
  howToPrevent = "Continue this habit by: [the specific practice they used]"

CONSEQUENCE (outcome-first — reveal harm before cause):
  description  = the harm that occurred — do NOT reveal the cause yet
  whatToDo     = how to recover after this situation has already happened
  whyItMatters = the root cause now revealed: what decision or omission led here
  howToPrevent = the single action that would have prevented the root cause

AMBIGUOUS (no single right answer — builds judgment, not compliance):
  description  = a genuinely complex situation where two valid principles conflict
  whatToDo     = "There is no single correct answer here. The competing considerations are: [...]"
  whyItMatters = "What matters is your reasoning process. Apply [specific principle] to weigh options."
  howToPrevent = "Develop judgment in situations like this by: [a specific practice]"

{structure_lock}
Format your response as strict JSON representing the course module:
{{
  "moduleNumber": {module_number},
  "moduleTitle": "{module_title}",{interactive_block_json}
  "sections": [
    {{
      "sectionTitle": "Section Title",
      "content": "3-4 sentences introducing the core principles.",
      "reflectionPrompt": "OPTIONAL — include in at least ONE section per module. A genuine question connecting this section's concept to the learner's own experience. NOT a quiz question — no right answer. Omit this field entirely from sections that don't carry the module's reflection.",
      "concepts": [
        {{
          "conceptTitle": "Concept Name",
          "explanation": "2-3 sentences explaining the concept. Use bullet points if applicable.",
          "scenario": {{
            // OPTIONAL. Include in AT MOST ONE concept per section.
            // Omit the entire "scenario" field for all other concepts in the same section.
            // Only include when the concept is abstract or genuinely needs illustration.
            // When included, ALL 4 fields below are MANDATORY. Never leave any blank.
            
            "description": "Describe the situation clearly — who is involved, what happened, and enough context for the learner to understand the problem. Use as many sentences as needed, but every sentence must add new information. Do NOT include the action or outcome here.",
            // EXAMPLE: "A new employee, Alex, prefers to use their chosen name. The HR system displays only their legal name. A well-meaning colleague sends an email using the name from the system, not realising it differs from Alex's preferred name. Alex feels unseen from their very first day at work."
            
            "whatToDo": "Exactly ONE sentence. The specific action the learner should take in this situation.",
            // EXAMPLE: "Always verify names directly with the individual before using system records."
            
            "whyItMatters": "Exactly ONE sentence. The consequence if the action is NOT taken.",
            // EXAMPLE: "Using the wrong name signals that colleagues do not see the person as they are, damaging trust from day one."
            
            "howToPrevent": "Exactly ONE sentence. A proactive step to stop this from happening in the first place.",
            // EXAMPLE: "Check preferred name fields in your HR system, or ask directly during onboarding introductions."
          }}
        }}
      ]
    }}
  ],
  "summary": "Write a strong conclusion. (1) Provide a 'Key Takeaways' bulleted list of 2-3 points. (2) Provide an 'Action Checklist' of 1-3 specific things the learner should do TODAY. (3) End with one forward-looking question that primes them for the next module. You MAY use markdown for lists and bolding."
}}
{f'LANGUAGE REQUIREMENT: Generate ALL content in {course_language}. Do not mix languages.' if course_language != 'English' else ''}"""

        return qa_validator.enhance_prompts_with_qa(base_prompt)
    
    def _build_knowledge_check_prompt(self, module_content: Dict, module_title: str, language: str = "English", course_title: str = "", scenario: dict = None) -> str:
        # Summarize module content to avoid quota issues (don't send full JSON)
        sections = module_content.get('sections', [])
        content_summary = []
        for section in sections[:2]:  # Limit to first 2 sections
            section_title = section.get('sectionTitle', '')
            concepts = section.get('concepts', [])[:3]  # Limit concepts per section
            for concept in concepts:
                concept_title = concept.get('conceptTitle', '')
                explanation = concept.get('explanation', '')[:400]  # Limit explanation length
                if concept_title:
                    content_summary.append(f"{concept_title}: {explanation}")
        
        content_text = "\n".join(content_summary[:6])  # Limit to 6 key concepts
        
        scenario_coupling_block = ""
        if scenario:
            scenario_coupling_block = f"""
SCENARIO COUPLING — MANDATORY:
The module's teaching scenario is:
  Situation: {scenario.get('description', '')}
  The lesson demonstrated: {scenario.get('whyItMatters', '')}

Your knowledge check question MUST test the specific judgment skill demonstrated in
this scenario.
Do NOT ask about a different concept from the module.
The scenario is the learning anchor — your question must confirm the learner absorbed
its lesson.
"""
        
        prompt = f"""Generate a knowledge check question for this module content. Create ONE high-quality multiple-choice question with ONE correct answer.

Module Title: {module_title}
Key Content Points:
{content_text}
{scenario_coupling_block}
QUESTION DESIGN RULES:

GREY-AREA QUESTION — MANDATORY (at least 1 per quiz/knowledge check):
At least one question must present a situation where:
- The learner's first instinct would be to choose a "reasonable-sounding" wrong answer
- The correct answer requires knowing a specific principle, not just good intentions
- Options B and C are BOTH plausible to someone without training

Mark this question internally (it needs to be genuinely harder than the others).

1. Test application, not recall.
   EXAMPLE OF A BAD QUESTION — do not write like this:
   "What does ESP stand for in the context of NERC CIP?"
   This tests recall of a definition. A learner can pass it without understanding anything.

   EXAMPLE OF A GOOD QUESTION — write like this:
   "A technician requests direct internet access to a protection relay inside the control center during an emergency. What is the correct action and why?"
   This describes a real situation, requires a decision, and has a consequence attached to
   the wrong choice. Apply this standard to every topic — not just compliance courses.

   VERBATIM BAN: Do NOT ask a question whose exact answer was given verbatim in the preceding paragraph in the module. The question MUST test the application of the concept, not mere reading comprehension.

2. Write a single, clear question. One sentence. Ends with a question mark.

3. All 4 options must be plausible. Wrong answers should represent real mistakes a
   competent but rushed person might make — not obvious nonsense.

4. Only one answer is correct.

5. Each option must have feedback that:
   - Names the exact principle or rule from the module that makes it right or wrong.
   - Does not just restate the answer.
   - Tells the learner what to review if they chose incorrectly.
   - FEEDBACK LOOPS: The feedback must explain the specific cascading real-world consequence of that incorrect choice, showing them *why* it fails.
   FEEDBACK QUALITY — WRITE LIKE THIS:
   "The corrective action procedure requires isolating affected product before investigating
   the cause. Adjusting the thermostat first delays the product safety decision."
   NOT like this: "This is incorrect." — these say nothing useful.
   Tell the learner what they got wrong and which specific concept from this module to revisit.

6. The question must reflect real consequences — the learner should feel why it matters.

7. Expand all abbreviations on first use within the question and options.

8. Do not repeat a question that has already appeared in this course.

{self._acronym_shortform_rule()}
{self._number_as_digits_rule()}
{self._sentence_simplicity_rule()}

QUESTION LENGTH RULE — MANDATORY:
- Question: 1 sentence, maximum 15 words. No preamble ("In a situation where...", "Consider the following...") — go straight to the question.
- Options A/B/C/D: maximum 10 words each. One idea per option only.
- Test exactly ONE concept per question — no compound questions.
- WRONG: "In a workplace scenario where an employee notices a colleague not following hand-washing protocols, what is the most appropriate first step?"
- RIGHT: "What should you do first if a colleague skips hand-washing?"

Format your response as JSON:
{{
  "question": "One-liner question text?",
  "options": {{
    "A": "Option A",
    "B": "Option B",
    "C": "Option C",
    "D": "Option D"
  }},
  "correctAnswer": "A",
  "feedback": {{
    "correct": "Detailed explanation of why the correct answer is right...",
    "incorrect": "General explanation for incorrect answers...",
    "A": "Specific feedback explaining why option A is correct/incorrect...",
    "B": "Specific feedback explaining why option B is correct/incorrect...",
    "C": "Specific feedback explaining why option C is correct/incorrect...",
    "D": "Specific feedback explaining why option D is correct/incorrect..."
  }}
}}
{f'LANGUAGE REQUIREMENT: Generate the question, all options, and all feedback in {language}. Do not mix languages.' if language != 'English' else ''}"""

        module_number = module_content.get('moduleNumber', 0)
        nerc_kc = get_nerc_kc_patches(course_title, module_number)
        if nerc_kc:
            prompt += f"\n\n{nerc_kc}"
        return prompt

    def _build_scramble_quiz_prompt(self, existing_quiz: Dict, all_module_content: List[Dict], course_title: str, language: str = "English") -> str:
        """Build prompt to scramble quiz with new questions"""
        # Extract content summary from modules
        content_summary = ""
        for idx, module in enumerate(all_module_content, 1):
            module_title = module.get("moduleTitle", f"Module {idx}")
            content_summary += f"\n\nModule {idx}: {module_title}\n"
            
            # Limit to first 3 sections per module
            sections = module.get("sections", [])
            for section in sections[:3]:
                section_title = section.get("sectionTitle", "")
                concepts = section.get("concepts", [])
                if section_title:
                    content_summary += f"- {section_title}\n"
                for concept in concepts[:2]:  # Limit to first 2 concepts per section
                    concept_title = concept.get("conceptTitle", "")
                    if concept_title:
                        content_summary += f"  * {concept_title}\n"
        
        # Extract existing quiz structure for reference
        existing_questions = existing_quiz.get("questions", [])
        existing_question_count = len(existing_questions)
        
        # Get sample questions for context (first 3)
        sample_questions = []
        for q in existing_questions[:3]:
            question_text = q.get('question', '')[:100]  # First 100 chars
            if question_text:
                sample_questions.append(question_text)
        
        return f"""You are an expert instructional designer. You need to SCRAMBLE/REGENERATE a quiz with COMPLETELY NEW QUESTIONS while keeping the context and topics relevant.

Your job is to write entirely new questions that cover the same topics and test the same
learning objectives — but are completely different from the original questions.

Do not rephrase the original questions. Do not change only a few words.
Write fresh questions that a learner who memorised the first quiz would not recognise.

SELF-CHECK BEFORE SUBMITTING:
Read each new question alongside the original question it replaces.
Ask: "Would a learner who memorised the original question and its answer immediately
know the answer to this new question without thinking?"
If yes — rewrite the question. It is not sufficiently different.

The new questions must:
1. Cover the SAME topics proportionally
2. Test the SAME learning objectives
3. Maintain the same difficulty level

Course Title: {course_title}

Original Quiz Context:
- Number of questions: {existing_question_count}
- Sample original questions (for context only - create NEW questions): {', '.join(sample_questions)}...

Current Module Content Summary:
{content_summary}

Requirements:
1. Generate exactly {existing_question_count} NEW questions (same number as original)
2. Questions must cover the SAME topics/concepts as the original quiz but be COMPLETELY DIFFERENT
3. Each question must have exactly 4 options (A, B, C, D)
4. Only ONE correct answer per question
5. Provide detailed feedback for correct and incorrect answers
6. Questions must be contextually relevant to the course content
7. DO NOT copy or rephrase existing questions - create NEW questions that test the same concepts
8. Mix of question types (understanding, application, analysis)
9. Cover content from all modules proportionally
10. CRITICAL: Remove all asterisks (*) and hash symbols (#) from content
11. If any acronym appears for the first time in the quiz output, include full form followed by acronym in brackets

{self._acronym_shortform_rule()}
{self._number_as_digits_rule()}
{self._sentence_simplicity_rule()}

QUIZ QUESTION FORMAT — MANDATORY:
Use one of these 3 types for every question. Types 1 and 2 are preferred (at least 60% combined).

TYPE 1 — SCENARIO-BASED (preferred):
  A real person in a real situation faces a decision.
  Structure: [Who + what happened, max 20 words] [Decision question, max 10 words]
  Total question: max 30 words.
  EXAMPLE: "A food supervisor finds the walk-in cooler at 48°F at opening time. What must she do first?"

TYPE 2 — CONDITION-BASED (for thresholds, classifications, rules):
  A specific measurable condition is stated, then a consequence is asked.
  Structure: [Condition/state, max 20 words] [Consequence question, max 10 words]
  Total question: max 30 words.
  EXAMPLE: "A substation has 3 lines at 345 kV and connects to 4 stations at 200 kV. How must it be classified?"

TYPE 3 — DIRECT (only when the concept cannot be scenario-tested):
  Single sentence, max 15 words. Use for at most 20% of questions.

OPTIONS — MANDATORY:
- Each option: max 25 words.
- Options must be specific — name the action, system, or timeframe.
- WRONG: "Report it" (too vague). RIGHT: "Report the deviation to your supervisor and log it before service begins."
- Do NOT include obviously wrong options (e.g. "Do nothing", "Ignore it").
- All 4 options must be plausible to someone with partial knowledge.

Format your response as JSON:
{{
  "quizTitle": "Course Quiz",
  "questions": [
    {{
      "questionNumber": 1,
      "question": "Scenario/condition setup (max 20 words). Decision question (max 10 words)?",
      "options": {{
        "A": "Option A",
        "B": "Option B",
        "C": "Option C",
        "D": "Option D"
      }},
      "correctAnswer": "A",
      "feedback": {{
        "correct": "Explanation...",
        "incorrect": "Explanation..."
      }}
    }}
  ]
}}
{f'LANGUAGE REQUIREMENT: Generate ALL scrambled quiz content (questions, options, feedback) in {language}. Do not mix languages.' if language != 'English' else ''}"""

    def _extract_key_topics(self, module_content: Dict) -> List[str]:
        """Extract key topics and concepts from module content to preserve during regeneration"""
        topics = []
        
        if isinstance(module_content, dict):
            # Extract section titles
            for section in module_content.get("sections", []):
                if "sectionTitle" in section:
                    topics.append(section["sectionTitle"])
                # Extract concept titles
                for concept in section.get("concepts", []):
                    if "conceptTitle" in concept:
                        topics.append(concept["conceptTitle"])
        return topics
    
    def _build_quiz_prompt(self, all_module_content: List[Dict], course_title: str, language: str = "English", num_questions: int = 10) -> str:
        # Summarize module content to avoid quota issues (don't send full JSON)
        module_summaries = []
        for idx, module in enumerate(all_module_content, 1):
            module_title = module.get('moduleTitle', f'Module {idx}')
            # Extract key content points (limit size)
            sections = module.get('sections', [])
            key_points = []
            for section in sections[:3]:  # Limit to first 3 sections
                section_title = section.get('sectionTitle', '')
                concepts = section.get('concepts', [])[:2]  # Limit concepts
                concept_titles = [c.get('conceptTitle', '') for c in concepts]
                if section_title or concept_titles:
                    key_points.append(f"{section_title}: {', '.join(concept_titles)}")

            summary = f"Module {idx}: {module_title}\n" + "\n".join(key_points[:5])
            module_summaries.append(summary)
        
        content_summary = "\n\n".join(module_summaries)
        
        quiz_prompt = f"""Generate a comprehensive quiz with exactly {num_questions} questions covering all module content. Ensure questions are contextually relevant and not repeated from knowledge checks.

Course Title: {course_title}

COURSE QUALITY STANDARDS — PHASE 3 (ASSESSMENT):
11. Every wrong answer must be a mistake a real learner could genuinely make. No absurd distractors. All 4 options must look plausible to someone with partial knowledge.
12. ASSESSMENT QUALITY RATIO (40/20/40) — MANDATORY:
    - 40% minimum of the questions MUST be scenario-based (learner makes a decision in a real situation).
    - 20% minimum MUST be application-based (learner applies a rule to a new example).
    - 40% maximum can be recall/recognition (definitions, multiple-choice facts).
    Never write a question answerable by copying one sentence from the module text. Questions must require the learner to think.

DIFFICULTY ANCHOR — CALIBRATING FOR 80% PASS RATE:
Do NOT write questions where the right answer is obvious by process of elimination.
The quiz passing threshold in the app is 80%.
This means a learner must genuinely understand the nuances of the content to pass.
If a learner only skimmed the material, they should score around 50-60%.
Therefore, for every question:
  - Generate one distractor (incorrect option) that represents a common, plausible misconception.
  - Generate one distractor that is factually true but does not answer the specific question asked.

Module Content Summary:
{content_summary}

Requirements:
GREY-AREA QUESTION — MANDATORY (at least 1 per quiz/knowledge check):
At least one question must present a situation where:
- The learner's first instinct would be to choose a "reasonable-sounding" wrong answer
- The correct answer requires knowing a specific principle, not just good intentions
- Options B and C are BOTH plausible to someone without training

Mark this question internally (it needs to be genuinely harder than the others).
1. Exactly {num_questions} questions (no more, no less)
2. Mix of question types strictly following the 40/20/40 ratio defined above
3. Each question must have exactly 4 options (A, B, C, D)
4. STRICTLY ONLY ONE correct answer per question. The correct answer must perfectly match the underlying explanation, and incorrect answers must be clearly wrong but highly plausible.
   VERBATIM BAN: Do NOT ask a question whose exact answer was given verbatim in the module text. The question MUST test the application of the concept, not mere reading comprehension.
5. Provide detailed feedback for correct and incorrect answers
6. Questions must be contextually relevant to the course content
7. NO repeated questions from knowledge checks
8. NO plagiarism
9. Cover content from all modules proportionally. No module may be skipped.
   If you are generating 10 questions for a 9-module course, at least
   8 modules must be represented. Before submitting your output, check
   your question list and confirm every module has at least one question.
10. If any acronym appears for the first time in the quiz output, include full form followed by acronym in brackets

{self._acronym_shortform_rule()}
{self._number_as_digits_rule()}
{self._sentence_simplicity_rule()}

QUIZ QUESTION FORMAT — MANDATORY:
Use one of these 3 types for every question. Types 1 and 2 are preferred (at least 60% combined).

TYPE 1 — SCENARIO-BASED (preferred):
  A real person in a real situation faces a decision.
  Structure: [Who + what happened, max 20 words] [Decision question, max 10 words]
  Total question: max 30 words.
  EXAMPLE: "A food supervisor finds the walk-in cooler at 48°F at opening time. What must she do first?"

TYPE 2 — CONDITION-BASED (for thresholds, classifications, rules):
  A specific measurable condition is stated, then a consequence is asked.
  Structure: [Condition/state, max 20 words] [Consequence question, max 10 words]
  Total question: max 30 words.
  EXAMPLE: "A substation has 3 lines at 345 kV and connects to 4 stations at 200 kV. How must it be classified?"

TYPE 3 — DIRECT (only when the concept cannot be scenario-tested):
  Single sentence, max 15 words. Use for at most 20% of questions.

OPTIONS — MANDATORY:
- Each option: max 25 words.
- Options must be specific — name the action, system, or timeframe.
- WRONG: "Report it" (too vague). RIGHT: "Report the deviation to your supervisor and log it before service begins."
- Do NOT include obviously wrong options (e.g. "Do nothing", "Ignore it").
- All 4 options must be plausible to someone with partial knowledge.

Format your response as JSON:
{{
  "quizTitle": "Course Quiz",
  "questions": [
    {{
      "questionNumber": 1,
      "question": "Scenario/condition setup (max 20 words). Decision question (max 10 words)?",
      "options": {{
        "A": "Option A",
        "B": "Option B",
        "C": "Option C",
        "D": "Option D"
      }},
      "correctAnswer": "A",
      "feedback": {{
        "correct": "Explanation...",
        "incorrect": "Explanation..."
      }}
    }}
  ]
}}
{f'LANGUAGE REQUIREMENT: Generate ALL quiz content (questions, options, feedback) in {language}. Do not mix languages.' if language != 'English' else ''}"""

        nerc_quiz = get_nerc_quiz_patches(course_title)
        if nerc_quiz:
            quiz_prompt += f"\n\n{nerc_quiz}"
        return quiz_prompt

    def _escape_newlines_in_strings(self, text: str) -> str:
        """Escape literal newlines/carriage-returns inside JSON string values.
        Gemini sometimes writes multi-line text directly in JSON strings without
        using \\n escape sequences, causing 'Unterminated string' errors."""
        result = []
        in_string = False
        escaped = False
        for ch in text:
            if escaped:
                result.append(ch)
                escaped = False
            elif ch == '\\' and in_string:
                result.append(ch)
                escaped = True
            elif ch == '"':
                in_string = not in_string
                result.append(ch)
            elif ch == '\n' and in_string:
                result.append('\\n')
            elif ch == '\r' and in_string:
                result.append('\\r')
            else:
                result.append(ch)
        return ''.join(result)

    def _clean_json_text(self, json_text: str) -> str:
        """Clean JSON text to handle trailing commas and unescaped quotes"""
        # Remove trailing commas before closing braces/brackets
        json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
        # Remove trailing commas at end of lines
        json_text = re.sub(r',\s*\n\s*([}\]])', r'\n\1', json_text)

        return json_text.strip()
    
    def _parse_json_response(self, text: str) -> Dict:
        """Parse JSON from response, handling markdown code blocks and trailing commas"""
        try:
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', text) or re.search(r'```\s*([\s\S]*?)\s*```', text)
            json_text = json_match.group(1) if json_match else text

            # Clean up the JSON string
            json_text = json_text.strip()

            # Escape literal newlines inside JSON strings (Gemini often emits raw \n in string values)
            json_text = self._escape_newlines_in_strings(json_text)

            # Clean trailing commas and other common JSON issues
            json_text = self._clean_json_text(json_text)

            return json.loads(json_text)
        except json.JSONDecodeError as e:
            error_str = str(e)
            # Handle "Extra data" - Gemini returned extra text after valid JSON
            if "Extra data" in error_str:
                try:
                    decoder = json.JSONDecoder()
                    result, _ = decoder.raw_decode(json_text)
                    logger.info("Recovered from 'Extra data' JSON error by parsing first object only")
                    return result
                except json.JSONDecodeError:
                    pass
            # Fallback: extract the first complete JSON object by finding balanced braces
            try:
                start = json_text.find('{')
                if start == -1:
                    start = json_text.find('[')
                if start != -1:
                    end = json_text.rfind('}')
                    if end == -1:
                        end = json_text.rfind(']')
                    if end != -1 and end > start:
                        extracted = self._clean_json_text(json_text[start:end + 1])
                        result = json.loads(extracted)
                        logger.info("Recovered from JSON error by extracting balanced braces")
                        return result
            except json.JSONDecodeError:
                pass
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text: {text[:500]}")
            raise ValueError(f"Invalid JSON response from Kartavya: {e}")
    
    def _parse_outline_response(self, text: str) -> Dict:
        """Parse course outline response"""
        parsed = self._parse_json_response(text)
        # Clean symbols from outline
        parsed = self._clean_outline_symbols(parsed)
        return parsed
    
    def _clean_outline_symbols(self, content: Dict) -> Dict:
        """Remove * and # symbols and convert number words to digits in outline content"""
        if not isinstance(content, dict):
            return content
        
        # Clean course title
        if "courseTitle" in content and isinstance(content["courseTitle"], str):
            content["courseTitle"] = _clean_str(content["courseTitle"])
        
        # Clean course description and overview
        for field in ["courseDescription", "courseOverview"]:
            if field in content and isinstance(content[field], str):
                content[field] = _clean_str(content[field])
        
        # Clean learning objectives
        if "courseLearningObjectives" in content and isinstance(content["courseLearningObjectives"], list):
            content["courseLearningObjectives"] = [
                _clean_str(obj) if isinstance(obj, str) else obj
                for obj in content["courseLearningObjectives"]
            ]
        
        # Clean modules
        if "modules" in content and isinstance(content["modules"], list):
            for module in content["modules"]:
                if isinstance(module, dict):
                    if "moduleTitle" in module and isinstance(module["moduleTitle"], str):
                        module["moduleTitle"] = _clean_str(module["moduleTitle"])
                    if "learningObjectives" in module and isinstance(module["learningObjectives"], list):
                        module["learningObjectives"] = [
                            _clean_str(obj) if isinstance(obj, str) else obj
                            for obj in module["learningObjectives"]
                        ]
        
        return content
    
    def _parse_module_content_response(self, text: str) -> Dict:
        """Parse module content response and validate word count"""
        parsed = self._parse_json_response(text)
        
        # Clean content to remove * and # symbols
        parsed = self._clean_content_symbols(parsed)
        
        # Extract all text content to count words
        full_text = self._extract_text_from_parsed_content(parsed)
        word_count = len(full_text.split())
        
        logger.info(f"Parsed module content: {word_count} words (no restrictions - audio can be any length)")
        
        return parsed
    
    def _clean_content_symbols(self, content: Dict) -> Dict:
        """Remove * and # symbols and convert number words to digits in all text content"""
        if not isinstance(content, dict):
            return content
        
        # Clean sections
        if "sections" in content:
            for section in content["sections"]:
                if "sectionTitle" in section and isinstance(section["sectionTitle"], str):
                    section["sectionTitle"] = _clean_str(section["sectionTitle"])
                if "content" in section and isinstance(section["content"], str):
                    section["content"] = _clean_str(section["content"])
                if "concepts" in section:
                    # Enforce max 1 scenario per section: keep only the first valid one
                    scenario_used = False
                    for concept in section["concepts"]:
                        if "conceptTitle" in concept and isinstance(concept["conceptTitle"], str):
                            concept["conceptTitle"] = _clean_str(concept["conceptTitle"])
                        if "explanation" in concept and isinstance(concept["explanation"], str):
                            concept["explanation"] = _clean_str(concept["explanation"])
                        if "scenario" in concept and isinstance(concept["scenario"], dict):
                            if scenario_used:
                                # Drop extra scenarios beyond the first in this section
                                del concept["scenario"]
                            else:
                                for key, value in concept["scenario"].items():
                                    if isinstance(value, str):
                                        concept["scenario"][key] = _clean_str(value)
                                scenario_used = True
                        elif "scenario" in concept:
                            # Remove malformed scenario fields
                            del concept["scenario"]
        
        # Clean summary
        if "summary" in content and isinstance(content["summary"], str):
            content["summary"] = _clean_str(content["summary"])
        
        # Clean module title
        if "moduleTitle" in content and isinstance(content["moduleTitle"], str):
            content["moduleTitle"] = _clean_str(content["moduleTitle"])
            
        # Clean interactive block
        if "interactiveBlock" in content:
            def clean_recursive(obj):
                if isinstance(obj, dict):
                    return {k: clean_recursive(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [clean_recursive(x) for x in obj]
                elif isinstance(obj, str):
                    return _clean_str(obj)
                return obj
            content["interactiveBlock"] = clean_recursive(content["interactiveBlock"])
            
        return content
    
    def _extract_text_from_parsed_content(self, content: Dict) -> str:
        """Extract all text from parsed module content for word counting"""
        text_parts = []
        
        if isinstance(content, dict):
            # Extract from sections
            if "sections" in content:
                for section in content["sections"]:
                    if "sectionTitle" in section:
                        text_parts.append(str(section["sectionTitle"]))
                    if "content" in section:
                        text_parts.append(str(section["content"]))
                    if "concepts" in section:
                        for concept in section["concepts"]:
                            if "conceptTitle" in concept:
                                text_parts.append(str(concept["conceptTitle"]))
                            if "explanation" in concept:
                                text_parts.append(str(concept["explanation"]))
                            if "scenario" in concept:
                                scenario = concept["scenario"]
                                if isinstance(scenario, dict):
                                    text_parts.extend([str(v) for v in scenario.values() if v])
                                else:
                                    text_parts.append(str(scenario))
            
            # Extract summary
            if "summary" in content:
                text_parts.append(str(content["summary"]))
            
            # Extract module title
            if "moduleTitle" in content:
                text_parts.append(str(content["moduleTitle"]))
        
        return " ".join(text_parts)
    
    def _parse_knowledge_check_response(self, text: str) -> Dict:
        """Parse knowledge check response"""
        return self._parse_json_response(text)
    
    def _clean_knowledge_check_symbols(self, content: Dict) -> Dict:
        """Remove * and # symbols and convert number words to digits in knowledge check content"""
        if not isinstance(content, dict):
            return content
        
        # Clean question
        if "question" in content and isinstance(content["question"], str):
            content["question"] = _clean_str(content["question"])
        
        # Clean options
        if "options" in content and isinstance(content["options"], dict):
            for key, value in content["options"].items():
                if isinstance(value, str):
                    content["options"][key] = _clean_str(value)
        
        # Clean feedback
        if "feedback" in content and isinstance(content["feedback"], dict):
            for key, value in content["feedback"].items():
                if isinstance(value, str):
                    content["feedback"][key] = _clean_str(value)
        
        return content
    
    def _parse_quiz_response(self, text: str) -> Dict:
        """Parse quiz response"""
        parsed = self._parse_json_response(text)
        # Clean symbols from quiz content
        parsed = self._clean_quiz_symbols(parsed)
        return parsed
    
    def _clean_quiz_symbols(self, content: Dict) -> Dict:
        """Remove * and # symbols and convert number words to digits in quiz content"""
        if not isinstance(content, dict):
            return content
        
        # Clean quiz title
        if "quizTitle" in content and isinstance(content["quizTitle"], str):
            content["quizTitle"] = _clean_str(content["quizTitle"])
        
        # Clean questions
        if "questions" in content and isinstance(content["questions"], list):
            for question in content["questions"]:
                if isinstance(question, dict):
                    # Clean question text
                    if "question" in question and isinstance(question["question"], str):
                        question["question"] = _clean_str(question["question"])
                    
                    # Clean options
                    if "options" in question and isinstance(question["options"], dict):
                        for key, value in question["options"].items():
                            if isinstance(value, str):
                                question["options"][key] = _clean_str(value)
                    
                    # Clean feedback
                    if "feedback" in question and isinstance(question["feedback"], dict):
                        for key, value in question["feedback"].items():
                            if isinstance(value, str):
                                question["feedback"][key] = _clean_str(value)

        return content

    def suggest_guidelines_for_title(self, course_title: str) -> Dict[str, Any]:
        """
        Given any course title, ask Gemini to return relevant real-world laws,
        regulations, standards, or industry guidelines as clickable suggestions.

        Returns: { "domain": str, "suggestions": List[str] }
        """
        if not course_title or len(course_title.strip()) < 3:
            return {"domain": "", "suggestions": []}

        # Plain-text prompt — one item per line, no JSON required.
        # We bypass _generate_content_with_timeout (which forces JSON mode)
        # and call the model directly to avoid schema/parsing fragility.
        prompt = (
            f'A training course is titled: "{course_title}"\n\n'
            "List 6 to 10 real, citable laws, regulations, standards, or industry guidelines "
            "that are directly relevant to this course topic.\n\n"
            "Rules:\n"
            "- Every item must actually exist. Do NOT invent regulation codes or agency names.\n"
            "- Be specific: prefer exact citation codes over vague names "
            "(e.g. '29 CFR 1910.119', 'ISO 45001:2018', 'FERPA 20 U.S.C. § 1232g').\n"
            "- Cover niche topics too: alcohol → liquor control acts + DOT rules; "
            "drugs → DEA schedules + Drug-Free Workplace Act; "
            "students → FERPA + Title IX; cartoons → FTC COPPA + trademark law.\n"
            "- Do NOT write 'company policy' or 'best practices'.\n"
            "- Sort results: most recently enacted or updated guidelines FIRST, oldest last.\n\n"
            "Output format — plain text only, one item per line, no bullets, no numbers, no JSON:\n"
            "DOMAIN: <two-to-four word domain label>\n"
            "<standard 1>\n"
            "<standard 2>\n"
            "..."
        )

        try:
            # Call model directly so we get plain text (not JSON-mode)
            generation_config = genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=800,
            )
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config,
                request_options={"timeout": 30},
            )

            raw = (response.text or "").strip()
            if not raw:
                logger.error("suggest_guidelines_for_title: empty response from Gemini")
                return {"domain": "", "suggestions": []}

            logger.info(f"suggest_guidelines_for_title raw: {raw[:300]}")

            # Parse: first line is "DOMAIN: ..." rest are suggestions
            lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
            domain = ""
            suggestions = []
            for line in lines:
                if line.upper().startswith("DOMAIN:"):
                    domain = line.split(":", 1)[1].strip()
                else:
                    # Strip only proper list markers (e.g. "1. ", "- ", "• ")
                    # NOT bare leading digits — that would corrupt codes like "29 CFR 1910.119"
                    clean = re.sub(r'^(\d+[\.\)]\s+|[\-\*\•]\s*)', '', line).strip()
                    if clean:
                        suggestions.append(clean)

            return {"domain": domain, "suggestions": suggestions[:12]}
        except Exception as exc:
            logger.error(f"suggest_guidelines_for_title failed: {exc}")
            return {"domain": "", "suggestions": []}
