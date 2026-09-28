"""Vercel Python entrypoint. Vercel's Python runtime serves any ASGI `app`
object exported from a file under api/ — this just re-exports the real
FastAPI app so app/main.py stays the single source of truth for routes."""

from app.main import app  # noqa: F401
