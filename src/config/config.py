import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Server configuration
SERVER_HOST = os.environ.get('SERVER_HOST', '127.0.0.1')
SERVER_PORT = int(os.environ.get('SERVER_PORT', 5060))
DEBUG_MODE = os.environ.get('DEBUG_MODE', 'true').lower() == 'true'
CORS_ALLOW_ORIGINS = os.environ.get('CORS_ALLOW_ORIGINS', '*').split(',')

# AI configuration
USE_PLACEHOLDERS = os.environ.get('USE_PLACEHOLDERS', 'true').lower() == 'true'
TOGETHER_API_KEY = os.environ.get('TOGETHER_API_KEY', '')
STUDENT_MODEL = os.environ.get('STUDENT_MODEL', 'Qwen/Qwen3-235B-A22B-fp8-tput')
EDUCATOR_MODEL = os.environ.get('EDUCATOR_MODEL', 'Qwen/Qwen3-235B-A22B-fp8-tput')
MINI_AI_MODEL = os.environ.get('MINI_AI_MODEL', 'Qwen/Qwen3-235B-A22B-fp8-tput')

# Character configuration
STUDENT_NAME = os.environ.get('STUDENT_NAME', 'Alex')
EDUCATOR_NAME = os.environ.get('EDUCATOR_NAME', 'Ms. Morgan')
# Add config versions to avoid circular imports
STUDENT_NAME_CONFIG = STUDENT_NAME
EDUCATOR_NAME_CONFIG = EDUCATOR_NAME

# Timing configuration
TYPING_DELAY_STUDENT = int(os.environ.get('TYPING_DELAY_STUDENT', 2))  # seconds
TYPING_DELAY_EDUCATOR = int(os.environ.get('TYPING_DELAY_EDUCATOR', 3))  # seconds
LONG_POLLING_TIMEOUT = int(os.environ.get('LONG_POLLING_TIMEOUT', 30))  # seconds

# Logging configuration
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
LOG_FILE = os.environ.get('LOG_FILE', 'logs/backend.log')  # Updated path to logs directory

# Export all variables
__all__ = [
    'SERVER_HOST', 'SERVER_PORT', 'DEBUG_MODE', 'CORS_ALLOW_ORIGINS',
    'USE_PLACEHOLDERS', 'TOGETHER_API_KEY',
    'STUDENT_MODEL', 'EDUCATOR_MODEL', 'MINI_AI_MODEL',
    'STUDENT_NAME', 'EDUCATOR_NAME', 'STUDENT_NAME_CONFIG', 'EDUCATOR_NAME_CONFIG',
    'TYPING_DELAY_STUDENT', 'TYPING_DELAY_EDUCATOR', 'LONG_POLLING_TIMEOUT',
    'LOG_LEVEL', 'LOG_FILE'
] 