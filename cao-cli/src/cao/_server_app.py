"""Minimal FastAPI app powering cao-server."""

from __future__ import annotations

from typing import Any


def build_app():
    try:
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
    except ImportError:
        raise RuntimeError(
            "fastapi not installed. Run: uv pip install 'cao[server]'"
        ) from None

    from cao.session import create_session, get_session, _sessions

    app = FastAPI(title="CAO Server", version="1.0.0")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": "1.0.0"}

    @app.post("/sessions")
    async def new_session() -> dict[str, Any]:
        session = await create_session()
        return {"session_id": session.id, "created_at": session.created_at.isoformat()}

    @app.get("/sessions/{session_id}")
    async def get_session_info(session_id: str) -> JSONResponse:
        session = await get_session(session_id)
        if session is None:
            return JSONResponse({"error": "session not found"}, status_code=404)
        return JSONResponse(
            {
                "session_id": session.id,
                "terminals": len(session.terminals),
                "inbox_size": len(session.inbox),
            }
        )

    @app.get("/sessions/{session_id}/inbox")
    async def drain_inbox(session_id: str) -> JSONResponse:
        session = await get_session(session_id)
        if session is None:
            return JSONResponse({"error": "session not found"}, status_code=404)
        messages = list(session.inbox)
        session.inbox.clear()
        return JSONResponse({"messages": messages})

    @app.get("/sessions")
    async def list_sessions() -> dict[str, Any]:
        return {
            "sessions": [
                {"session_id": sid, "terminals": len(s.terminals)}
                for sid, s in _sessions.items()
            ]
        }

    return app
