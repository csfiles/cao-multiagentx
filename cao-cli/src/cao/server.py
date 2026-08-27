"""CAO Server — lightweight REST API for session and terminal management."""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def run() -> None:
    """Entry point for the cao-server command."""
    try:
        import uvicorn
    except ImportError:
        raise RuntimeError(
            "uvicorn not installed. Run: uv pip install 'cao[server]'"
        ) from None

    from cao._server_app import build_app

    host = os.environ.get("CAO_HOST", "127.0.0.1")
    port = int(os.environ.get("CAO_PORT", "8765"))
    log_level = os.environ.get("CAO_LOG_LEVEL", "info").lower()

    logger.info("CAO Server starting on %s:%d", host, port)
    app = build_app()
    uvicorn.run(app, host=host, port=port, log_level=log_level)
