"""Configuration and environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

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
ACCOUNT_FILE = Path(os.getenv("ACCOUNT_FILE", "antigravity.json"))

# Server port (loaded from .env)
PORT = int(os.getenv("PORT", "8000"))
