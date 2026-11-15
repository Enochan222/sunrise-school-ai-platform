"""Uvicorn startup: fail-start if required secrets missing."""
from vault_app import build_app
app = build_app()
