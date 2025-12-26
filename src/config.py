"""Configuration and environment variables."""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Google Cloud Code API URLs
API_URL = "https://cloudcode-pa.googleapis.com/v1internal:fetchAvailableModels"
PROJECT_API_URL = "https://cloudcode-pa.googleapis.com/v1internal:loadCodeAssist"
TOKEN_URL = "https://oauth2.googleapis.com/token"

# User agent (loaded from .env)
USER_AGENT = os.getenv("USER_AGENT", "antigravity/1.13.3 Darwin/arm64")

# Google OAuth credentials (loaded from .env)
# https://github.com/lbjlaq/Antigravity-Manager/blob/main/src-tauri/src/modules/oauth.rs
CLIENT_ID = os.getenv("CLIENT_ID", "")
CLIENT_SECRET = os.getenv("CLIENT_SECRET", "")

# Account file path (loaded from .env)
# Resolve relative paths against the project root (parent of src/)
_account_file_value = os.getenv("ACCOUNT_FILE", "antigravity.json").strip("'\"")
_account_file_path = Path(_account_file_value)
if not _account_file_path.is_absolute():
    _account_file_path = Path(__file__).parent.parent / _account_file_path
ACCOUNT_FILE = _account_file_path
logger.info(f"ACCOUNT_FILE: {ACCOUNT_FILE}")

# Server port (loaded from .env)
PORT = int(os.getenv("PORT", "8000"))

# Query debounce time in minutes (loaded from .env)
# Cache googleapis responses for this many minutes to avoid spamming
QUERY_DEBOUNCE = int(os.getenv("QUERY_DEBOUNCE", "1"))
