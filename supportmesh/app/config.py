"""
SupportMesh runtime configuration.

All values come from environment variables (see .env.example).
No hard-coded credentials — ever.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _bool(key: str, default: str = "false") -> bool:
    return os.getenv(key, default).lower() in ("1", "true", "yes")


def _int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


class Config:
    # --- AWS (optional) ---
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    aws_profile: str | None = os.getenv("AWS_PROFILE")

    # --- CAO ---
    cao_model: str = os.getenv("SUPPORTMESH_MODEL", "us.anthropic.claude-3-7-sonnet-20250219-v1:0")
    cao_max_tokens: int = _int("SUPPORTMESH_MAX_TOKENS", 4096)
    cao_timeout: int = _int("SUPPORTMESH_TIMEOUT_SECONDS", 120)

    # --- MCP server ---
    mcp_data_dir: Path = Path(os.getenv("SUPPORTMESH_DATA_DIR", "./data"))
    mcp_server_host: str = os.getenv("SUPPORTMESH_MCP_HOST", "127.0.0.1")
    mcp_server_port: int = _int("SUPPORTMESH_MCP_PORT", 8765)

    # --- Safety ---
    allow_mutations: bool = _bool("SUPPORTMESH_ALLOW_MUTATIONS", "false")
    dry_run: bool = _bool("SUPPORTMESH_DRY_RUN", "true")

    # --- Logging ---
    log_level: str = os.getenv("SUPPORTMESH_LOG_LEVEL", "INFO").upper()

    # --- Local demo ---
    demo_mode: bool = _bool("SUPPORTMESH_DEMO_MODE", "true")
    demo_customer_id: str = os.getenv("SUPPORTMESH_DEMO_CUSTOMER_ID", "CUST-001")


config = Config()
