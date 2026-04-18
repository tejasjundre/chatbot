"""Conversation history management for Plexi Bot."""

from __future__ import annotations

from collections import defaultdict
from typing import DefaultDict, TypedDict

MAX_HISTORY_MESSAGES = 40


class Message(TypedDict):
    """Conversation message object."""

    role: str
    content: str


class ConversationManager:
    """Stores and manages chat histories by session ID."""

    def __init__(self) -> None:
        """Initialize in-memory session storage."""

        self._sessions: DefaultDict[str, list[Message]] = defaultdict(list)

    def get_history(self, session_id: str) -> list[Message]:
        """Return a session's full conversation history."""

        return self._sessions[session_id]

    def get_snapshot(self, session_id: str) -> list[Message]:
        """Return a copy of one session's history without creating a new session."""

        return list(self._sessions.get(session_id, []))

    def append(self, session_id: str, role: str, content: str) -> None:
        """Append one message to a session history."""

        self._sessions[session_id].append({"role": role, "content": content})
        if len(self._sessions[session_id]) > MAX_HISTORY_MESSAGES:
            # Keep only the most recent messages to control memory usage.
            self._sessions[session_id] = self._sessions[session_id][-MAX_HISTORY_MESSAGES:]

    def reset(self, session_id: str) -> None:
        """Reset the conversation history for one session."""

        self._sessions[session_id] = []

    def message_count(self, session_id: str) -> int:
        """Return number of stored messages for a session."""

        return len(self._sessions.get(session_id, []))

    def stats(self) -> dict[str, int]:
        """Return high-level in-memory conversation statistics."""

        total_sessions = len(self._sessions)
        total_messages = sum(len(messages) for messages in self._sessions.values())
        active_sessions = sum(1 for messages in self._sessions.values() if messages)
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "total_messages": total_messages,
        }


conversation_manager = ConversationManager()


def reset_conversation(session_id: str) -> None:
    """Reset conversation helper used by API endpoints."""

    conversation_manager.reset(session_id)


def get_message_count(session_id: str) -> int:
    """Get total message count for a session."""

    return conversation_manager.message_count(session_id)


def get_conversation_snapshot(session_id: str) -> list[Message]:
    """Return a session transcript snapshot."""

    return conversation_manager.get_snapshot(session_id)


def get_conversation_stats() -> dict[str, int]:
    """Return aggregate conversation statistics."""

    return conversation_manager.stats()
