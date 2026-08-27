"""
Shared pytest fixtures for SupportMesh tests.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Generator

import pytest

from mcp.customer_support_server.tools import LocalDataStore, set_data_store

# ---------------------------------------------------------------------------
# Event loop
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ---------------------------------------------------------------------------
# Data store fixture pointing at the real demo data
# ---------------------------------------------------------------------------


DATA_DIR = Path(__file__).parent.parent / "data"


@pytest.fixture(autouse=True)
def use_local_data_store():
    """Replace the default store with one pointing at the local data dir."""
    store = LocalDataStore(data_dir=DATA_DIR)
    set_data_store(store)
    yield store
    # Reset so tests don't bleed into each other
    set_data_store(LocalDataStore(data_dir=DATA_DIR))
