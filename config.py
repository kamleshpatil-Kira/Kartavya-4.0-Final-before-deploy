import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
# override=True ensures .env file always takes precedence over any stale system env vars
# This prevents issues where an old GEMINI_API_KEY exported in a terminal session
# overrides the correct key in the .env file
load_dotenv(override=True)

# Base directory
BASE_DIR = Path(__file__).parent

# API Keys
# .env file is always the source of truth (see override=True above)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")  # Used for content generation

# Google Cloud Text-to-Speech API key.
# If set, this key is used for TTS (allows using a Cloud-project key with the
# Text-to-Speech API enabled, which supports true male/female voice selection).
# If not set, falls back to GEMINI_API_KEY (which may not have TTS API access,
# causing all audio to fall back to gTTS with no gender differentiation).
GOOGLE_TTS_API_KEY = os.getenv("GOOGLE_TTS_API_KEY", "") or GEMINI_API_KEY

# Server Configuration
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Paths
UPLOADS_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "temp"
LOGS_DIR = BASE_DIR / "logs"

# Create directories if they don't exist
for directory in [UPLOADS_DIR, OUTPUT_DIR, TEMP_DIR, LOGS_DIR]:
    directory.mkdir(exist_ok=True)

# Generation settings
# Module generation settings - generate 4-5 modules by default
MIN_MODULES = 4
MAX_MODULES = 5
QUIZ_QUESTIONS = 10
AUDIO_WPM_MIN = 140
AUDIO_WPM_MAX = 160
AUDIO_WPM_DEFAULT = 150
# Audio duration restrictions removed - no limits on audio length
# Audio can be any length based on content requirements
GENERATION_TIMEOUT = 600  # 10 minutes in seconds

# Gemini Model Configuration
# Options: 'gemini-2.5-flash' (fast, reliable), 'gemini-2.5-pro' (higher quality, slower)
# The GeminiService has automatic fallback logic if the selected model is unavailable.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_IMAGE_MODEL = os.getenv("GEMINI_IMAGE_MODEL", "gemini-3-pro-image-preview")
MAX_CONCURRENT_IMAGES = int(os.getenv("MAX_CONCURRENT_IMAGES", "2"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Validate required API keys
if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY not set (required for content generation and TTS)")

