#!/usr/bin/env python3
"""Entry point for the Antigravity Quota API server."""

import uvicorn

from src.api import app
from src.config import PORT


def main():
    uvicorn.run(app, host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()
