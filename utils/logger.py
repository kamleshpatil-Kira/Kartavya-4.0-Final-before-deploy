import logging
import json
from datetime import datetime
from pathlib import Path
from pythonjsonlogger import jsonlogger
from config import LOGS_DIR, LOG_LEVEL

# Create logs directory if it doesn't exist
LOGS_DIR.mkdir(exist_ok=True)

def setup_logger(name="course_generator"):
    """Setup structured logger"""
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
    
    # Clear existing handlers
    logger.handlers = []
    
    # Console handler with color formatting
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    
    # File handler with JSON formatting
    log_file = LOGS_DIR / f"{name}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    json_formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    file_handler.setFormatter(json_formatter)
    
    # Error file handler
    error_file = LOGS_DIR / "error.log"
    error_handler = logging.FileHandler(error_file)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(json_formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    
    return logger

# Create main logger instance
logger = setup_logger()

def log_activity(activity, data=None):
    """Log an activity"""
    logger.info(f"Activity: {activity}", extra={"activity": activity, "data": data or {}})

def log_error(error, context=None):
    """Log an error with context"""
    logger.error(
        f"Error: {str(error)}",
        extra={
            "error": str(error),
            "error_type": type(error).__name__,
            "context": context or {}
        },
        exc_info=True
    )

def log_generation_start(user_id, generation_type):
    """Log start of course generation"""
    logger.info(
        "Course generation started",
        extra={
            "user_id": user_id,
            "type": generation_type,
            "timestamp": datetime.now().isoformat()
        }
    )

def log_generation_progress(user_id, step, progress):
    """Log generation progress"""
    logger.info(
        "Generation progress",
        extra={
            "user_id": user_id,
            "step": step,
            "progress": progress,
            "timestamp": datetime.now().isoformat()
        }
    )

def log_generation_complete(user_id, duration, success=True):
    """Log completion of course generation"""
    logger.info(
        "Course generation completed",
        extra={
            "user_id": user_id,
            "duration": duration,
            "success": success,
            "timestamp": datetime.now().isoformat()
        }
    )

def log_api_call(service, endpoint, duration, success=True, error=None):
    """Log API call"""
    logger.info(
        "API call",
        extra={
            "service": service,
            "endpoint": endpoint,
            "duration": duration,
            "success": success,
            "error": str(error) if error else None,
            "timestamp": datetime.now().isoformat()
        }
    )

