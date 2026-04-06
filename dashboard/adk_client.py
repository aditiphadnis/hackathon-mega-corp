from __future__ import annotations

import os
import uuid

import requests

ADK_API_URL = os.getenv("ADK_API_URL", "http://localhost:8000")
APP_NAME    = "ceo_assistant"


def create_session(user_id: str) -> str:
    """Register a new session with ADK and return the session_id."""
    session_id = str(uuid.uuid4())
    try:
        resp = requests.post(
            f"{ADK_API_URL}/apps/{APP_NAME}/users/{user_id}/sessions/{session_id}",
            timeout=10,
        )
        resp.raise_for_status()
    except requests.RequestException:
        pass
    return session_id


def _ensure_session(user_id: str, session_id: str) -> None:
    """Ensure the session exists — recreate it if Cloud Run lost it."""
    try:
        resp = requests.get(
            f"{ADK_API_URL}/apps/{APP_NAME}/users/{user_id}/sessions/{session_id}",
            timeout=5,
        )
        if resp.status_code == 404:
            requests.post(
                f"{ADK_API_URL}/apps/{APP_NAME}/users/{user_id}/sessions/{session_id}",
                timeout=10,
            )
    except requests.RequestException:
        pass


def run_agent(user_id: str, session_id: str, message: str) -> str:
    """POST to /run and return the last model text from the event list."""
    # Always ensure session exists before running — critical for Cloud Run
    _ensure_session(user_id, session_id)

    resp = requests.post(
        f"{ADK_API_URL}/run",
        json={
            "app_name":    APP_NAME,
            "user_id":     user_id,
            "session_id":  session_id,
            "new_message": {"role": "user", "parts": [{"text": message}]},
            "streaming":   False,
        },
        timeout=120,
    )
    if resp.status_code == 500 and "RESOURCE_EXHAUSTED" in resp.text:
        return "⏳ Rate limit hit — please wait 30 seconds and try again."
    resp.raise_for_status()

    for event in reversed(resp.json()):
        content = event.get("content") or {}
        if content.get("role") != "model":
            continue
        for part in content.get("parts") or []:
            text = (part.get("text") or "").strip()
            if text:
                return text
    return "No response received from the agent."