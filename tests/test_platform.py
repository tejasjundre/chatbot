"""Tests for platform-level API and persistence helpers."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from bot.feedback_store import append_feedback, count_feedback
from main import app

client = TestClient(app)


def test_public_config_endpoint_shape() -> None:
    """Public config endpoint should expose non-sensitive runtime flags."""

    response = client.get("/config/public")
    assert response.status_code == 200
    payload = response.json()
    assert "auth_required" in payload
    assert "chat_rate_limit_per_minute" in payload


def test_transcript_endpoint_after_chat_turn() -> None:
    """Transcript endpoint should return messages after a chat interaction."""

    session_id = str(uuid4())
    chat = client.post(
        "/chat",
        json={"session_id": session_id, "message": "Track ORD-1042"},
    )
    assert chat.status_code == 200

    transcript = client.get(f"/transcript/{session_id}")
    assert transcript.status_code == 200
    payload = transcript.json()
    assert payload["session_id"] == session_id
    assert payload["message_count"] >= 2
    assert len(payload["messages"]) >= 2


def test_feedback_store_append_and_count(tmp_path: Path) -> None:
    """Feedback store should append JSONL entries and report count."""

    file_path = tmp_path / "feedback_test.jsonl"
    append_feedback({"rating": 5, "comment": "Great bot"}, str(file_path))
    append_feedback({"rating": 4, "comment": "Useful suggestions"}, str(file_path))
    assert count_feedback(str(file_path)) == 2
