"""LLM client helpers with Gemini, Anthropic, and Groq support."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

import httpx

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - fallback for minimal test envs
    def load_dotenv() -> bool:
        """No-op fallback when python-dotenv is unavailable."""

        return False

from bot.conversation import Message

DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
DEFAULT_GEMINI_MODEL = "gemini-2.0-flash"
DEFAULT_GROQ_MODEL = "llama-3.1-8b-instant"
VALID_PROVIDERS = {"anthropic", "gemini", "groq"}
load_dotenv()

if TYPE_CHECKING:
    from anthropic import Anthropic
    from google.genai.client import Client as GeminiClient
else:
    Anthropic = Any
    GeminiClient = Any


class LLMServiceError(RuntimeError):
    """Raised when the active LLM provider call cannot be completed."""


def _resolve_provider() -> str:
    """Resolve active provider from env or infer from available keys."""

    explicit = os.getenv("LLM_PROVIDER", "").strip().lower()
    if explicit == "grok":
        explicit = "groq"
    if explicit in VALID_PROVIDERS:
        return explicit
    has_groq = bool(os.getenv("GROQ_API_KEY"))
    has_gemini = bool(os.getenv("GEMINI_API_KEY"))
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
    if has_groq and not has_gemini and not has_anthropic:
        return "groq"
    if has_gemini and not has_anthropic:
        return "gemini"
    return "anthropic"


def _gemini_model_name() -> str:
    """Return configured Gemini model name."""

    return os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)


def _anthropic_model_name() -> str:
    """Return configured Anthropic model name."""

    return os.getenv("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL)


def _groq_model_name() -> str:
    """Return configured Groq model name."""

    return os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)


def get_anthropic_client() -> Anthropic:
    """Create an Anthropic client from environment configuration."""

    try:
        from anthropic import Anthropic as AnthropicClient
    except ImportError as exc:  # pragma: no cover - dependency/runtime layer
        raise LLMServiceError("anthropic package is not installed.") from exc

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise LLMServiceError("ANTHROPIC_API_KEY is missing.")
    return AnthropicClient(api_key=api_key)


def get_gemini_client() -> GeminiClient:
    """Create a Gemini client from environment configuration."""

    try:
        from google import genai
    except ImportError as exc:  # pragma: no cover - dependency/runtime layer
        raise LLMServiceError("google-genai package is not installed.") from exc

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise LLMServiceError("GEMINI_API_KEY is missing.")
    return genai.Client(api_key=api_key)


def build_messages(history: list[Message], user_message: str) -> list[dict[str, str]]:
    """Create Anthropic-formatted message history with latest user turn."""

    return [*history, {"role": "user", "content": user_message}]


def _build_gemini_prompt(system_prompt: str, messages: list[dict[str, str]]) -> str:
    """Build a single text prompt carrying full multi-turn conversation."""

    transcript_lines = [system_prompt, "", "Conversation Transcript:"]
    for msg in messages:
        role = msg["role"].upper()
        transcript_lines.append(f"{role}: {msg['content']}")
    transcript_lines.append("")
    transcript_lines.append("Reply as the assistant to the latest USER message only.")
    return "\n".join(transcript_lines)


def _extract_gemini_text(response: Any) -> str:
    """Extract text from Gemini SDK response robustly."""

    text = getattr(response, "text", None)
    if text:
        return str(text).strip()

    candidates = getattr(response, "candidates", None) or []
    extracted: list[str] = []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", None) or []
        for part in parts:
            part_text = getattr(part, "text", None)
            if part_text:
                extracted.append(str(part_text))
    return "\n".join(extracted).strip()


def _build_groq_messages(
    system_prompt: str, messages: list[dict[str, str]]
) -> list[dict[str, str]]:
    """Build OpenAI-style role messages for the Groq chat API."""

    payload_messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    for msg in messages:
        role = msg.get("role", "user")
        if role not in {"user", "assistant", "system"}:
            role = "user"
        payload_messages.append({"role": role, "content": msg.get("content", "")})
    return payload_messages


def _call_anthropic(
    system_prompt: str,
    history: list[Message],
    user_message: str,
    max_tokens: int,
    client: Anthropic | None = None,
) -> str:
    """Call Anthropic and return a text response."""

    active_client = client or get_anthropic_client()
    messages = build_messages(history, user_message)
    try:
        response = active_client.messages.create(
            model=_anthropic_model_name(),
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages,
        )
    except Exception as exc:  # pragma: no cover - network/service layer
        err = str(exc).lower()
        if "quota" in err or "rate limit" in err:
            raise LLMServiceError("AI quota exceeded for current Anthropic account.") from exc
        raise LLMServiceError("Unable to reach the AI service right now.") from exc

    chunks = [block.text for block in response.content if getattr(block, "text", None)]
    if not chunks:
        raise LLMServiceError("AI service returned an empty response.")
    return "\n".join(chunks).strip()


def _call_gemini(
    system_prompt: str,
    history: list[Message],
    user_message: str,
    client: GeminiClient | None = None,
) -> str:
    """Call Gemini and return a text response."""

    active_client = client or get_gemini_client()
    messages = build_messages(history, user_message)
    combined_prompt = _build_gemini_prompt(system_prompt, messages)
    try:
        response = active_client.models.generate_content(
            model=_gemini_model_name(),
            contents=combined_prompt,
        )
    except Exception as exc:  # pragma: no cover - network/service layer
        err = str(exc).lower()
        if "resource_exhausted" in err or "quota" in err:
            raise LLMServiceError("AI quota exceeded for current Gemini key/project.") from exc
        if "api key not valid" in err or "permission_denied" in err:
            raise LLMServiceError("GEMINI_API_KEY is invalid or lacks required permissions.") from exc
        raise LLMServiceError("Unable to reach the AI service right now.") from exc

    text = _extract_gemini_text(response)
    if not text:
        raise LLMServiceError("AI service returned an empty response.")
    return text


def _call_groq(
    system_prompt: str,
    history: list[Message],
    user_message: str,
    max_tokens: int,
) -> str:
    """Call Groq OpenAI-compatible API and return a text response."""

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise LLMServiceError("GROQ_API_KEY is missing.")

    messages = build_messages(history, user_message)
    payload = {
        "model": _groq_model_name(),
        "messages": _build_groq_messages(system_prompt, messages),
        "max_tokens": max_tokens,
        "temperature": 0.2,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    try:
        response = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60.0,
        )
    except Exception as exc:  # pragma: no cover - network/service layer
        raise LLMServiceError("Unable to reach the AI service right now.") from exc

    if response.status_code >= 400:
        body = response.text.lower()
        if response.status_code in {401, 403} or "api key" in body:
            raise LLMServiceError("GROQ_API_KEY is invalid or lacks required permissions.")
        if response.status_code == 429 or "quota" in body or "rate limit" in body:
            raise LLMServiceError("AI quota exceeded for current Groq key/project.")
        raise LLMServiceError("Unable to reach the AI service right now.")

    try:
        data = response.json()
        content = data["choices"][0]["message"]["content"]
    except Exception as exc:  # pragma: no cover - parsing layer
        raise LLMServiceError("AI service returned an empty response.") from exc

    text = str(content).strip()
    if not text:
        raise LLMServiceError("AI service returned an empty response.")
    return text


def get_runtime_ai_config() -> dict[str, object]:
    """Return current provider/model/key-status for diagnostics."""

    provider = _resolve_provider()
    if provider == "groq":
        return {
            "provider": provider,
            "model": _groq_model_name(),
            "configured": bool(os.getenv("GROQ_API_KEY")),
        }
    if provider == "gemini":
        return {
            "provider": provider,
            "model": _gemini_model_name(),
            "configured": bool(os.getenv("GEMINI_API_KEY")),
        }
    return {
        "provider": provider,
        "model": _anthropic_model_name(),
        "configured": bool(os.getenv("ANTHROPIC_API_KEY")),
    }


def call_llm(
    system_prompt: str,
    history: list[Message],
    user_message: str,
    max_tokens: int = 500,
    client: Any | None = None,
) -> str:
    """Call the configured provider and return model output text."""

    provider = _resolve_provider()
    if provider == "groq":
        return _call_groq(
            system_prompt=system_prompt,
            history=history,
            user_message=user_message,
            max_tokens=max_tokens,
        )
    if provider == "gemini":
        return _call_gemini(system_prompt, history, user_message, client=client)
    return _call_anthropic(
        system_prompt,
        history,
        user_message,
        max_tokens=max_tokens,
        client=client,
    )


def call_claude(
    system_prompt: str,
    history: list[Message],
    user_message: str,
    max_tokens: int = 500,
    client: Any | None = None,
) -> str:
    """Backward-compatible wrapper now routed through provider abstraction."""

    return call_llm(
        system_prompt=system_prompt,
        history=history,
        user_message=user_message,
        max_tokens=max_tokens,
        client=client,
    )
