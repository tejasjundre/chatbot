"""FastAPI entrypoint and CLI runner for Plexi Bot."""

from __future__ import annotations

import logging
from pathlib import Path
from time import perf_counter, time
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel, Field

from bot.conversation import (
    get_conversation_snapshot,
    get_conversation_stats,
    get_message_count,
    reset_conversation,
)
from bot.feedback_store import append_feedback, count_feedback
from bot.guidance import build_help_message, capabilities_payload
from bot.llm import get_runtime_ai_config
from bot.rate_limit import SlidingWindowRateLimiter
from bot.router import route_message, route_message_with_meta
from bot.settings import get_settings

APP_START_TS = time()
SETTINGS = get_settings()
RATE_LIMITER = SlidingWindowRateLimiter(
    limit=SETTINGS.chat_rate_limit_per_minute,
    window_seconds=60,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
LOGGER = logging.getLogger("plexi_bot")

app = FastAPI(title="Plexi Bot", version="1.2.0")
FRONTEND_FILE = Path(__file__).resolve().parent / "frontend" / "index.html"

allow_credentials = "*" not in SETTINGS.cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=SETTINGS.cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    """Request body for the /chat endpoint."""

    session_id: UUID
    message: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    """Response body for the /chat endpoint."""

    reply: str
    intent: str
    suggestions: list[str]
    session_id: UUID
    message_count: int
    latency_ms: int
    request_id: str


class ResetRequest(BaseModel):
    """Request body for the /reset endpoint."""

    session_id: UUID


class FeedbackRequest(BaseModel):
    """Request body for user feedback capture."""

    session_id: UUID
    rating: int = Field(ge=1, le=5)
    comment: str = Field(default="", max_length=800)
    intent: str = Field(default="unknown", max_length=64)


def _request_id(request: Request) -> str:
    """Resolve per-request correlation ID."""

    return request.headers.get("x-request-id", str(uuid4()))


def _client_identity(request: Request, session_id: str | None = None) -> str:
    """Build a stable client identifier for rate limiting."""

    if session_id:
        return f"session:{session_id}"
    host = request.client.host if request.client else "unknown"
    return f"ip:{host}"


def _enforce_api_auth(request: Request) -> None:
    """Enforce optional API key auth for protected endpoints."""

    if not SETTINGS.auth_required:
        return
    presented = request.headers.get("x-api-key", "")
    if presented != SETTINGS.app_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized: invalid x-api-key.")


@app.middleware("http")
async def request_middleware(request: Request, call_next: callable) -> Response:
    """Attach request IDs and emit basic request logs."""

    req_id = _request_id(request)
    start = perf_counter()
    response = await call_next(request)
    latency_ms = int((perf_counter() - start) * 1000)
    response.headers["x-request-id"] = req_id
    LOGGER.info(
        "request path=%s method=%s status=%s latency_ms=%s request_id=%s",
        request.url.path,
        request.method,
        response.status_code,
        latency_ms,
        req_id,
    )
    return response


@app.get("/")
def index() -> RedirectResponse:
    """Redirect root URL to the web chat UI."""

    return RedirectResponse(url="/ui", status_code=307)


@app.get("/api-info")
def api_info() -> dict[str, object]:
    """Return API discovery metadata."""

    return {
        "service": "Plexi Bot",
        "status": "running",
        "version": app.version,
        "endpoints": [
            "/ui",
            "/config/public",
            "/capabilities",
            "/health",
            "/chat",
            "/reset",
            "/feedback",
            "/transcript/{session_id}",
            "/metrics",
            "/docs",
        ],
    }


@app.get("/config/public")
def public_config() -> dict[str, object]:
    """Return non-sensitive runtime config used by UI clients."""

    return {
        "auth_required": SETTINGS.auth_required,
        "chat_rate_limit_per_minute": SETTINGS.chat_rate_limit_per_minute,
        "environment": SETTINGS.app_env,
    }


@app.get("/ui")
def ui() -> FileResponse:
    """Serve the browser chat UI."""

    return FileResponse(FRONTEND_FILE)


@app.get("/capabilities")
def capabilities() -> dict[str, object]:
    """Return bot capabilities and starter examples for onboarding."""

    payload = capabilities_payload()
    payload["starter_help_message"] = build_help_message()
    return payload


@app.get("/health")
def health() -> dict[str, object]:
    """Return service health status and runtime AI configuration."""

    ai = get_runtime_ai_config()
    return {
        "status": "ok",
        "version": app.version,
        "uptime_seconds": int(time() - APP_START_TS),
        "ai_provider": ai["provider"],
        "ai_model": ai["model"],
        "ai_configured": ai["configured"],
    }


@app.get("/metrics")
def metrics(request: Request) -> dict[str, object]:
    """Return lightweight business and operational metrics."""

    _enforce_api_auth(request)
    if not SETTINGS.enable_metrics:
        raise HTTPException(status_code=404, detail="Metrics are disabled.")
    conversation = get_conversation_stats()
    return {
        "status": "ok",
        "conversation": conversation,
        "feedback_count": count_feedback(SETTINGS.feedback_log_path),
        "uptime_seconds": int(time() - APP_START_TS),
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: Request, payload: ChatRequest) -> ChatResponse:
    """Handle a chat request by routing to the correct feature."""

    _enforce_api_auth(request)
    req_id = _request_id(request)
    allowed, retry_after = RATE_LIMITER.check(
        _client_identity(request, str(payload.session_id))
    )
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Retry after {retry_after} seconds.",
        )

    start = perf_counter()
    result = route_message_with_meta(str(payload.session_id), payload.message.strip())
    elapsed_ms = int((perf_counter() - start) * 1000)
    return ChatResponse(
        reply=str(result["reply"]),
        intent=str(result["intent"]),
        suggestions=list(result["suggestions"]),
        session_id=payload.session_id,
        message_count=get_message_count(str(payload.session_id)),
        latency_ms=elapsed_ms,
        request_id=req_id,
    )


@app.post("/reset")
def reset(request: Request, payload: ResetRequest) -> dict[str, str]:
    """Reset a specific session's conversation history."""

    _enforce_api_auth(request)
    reset_conversation(str(payload.session_id))
    return {"status": "conversation reset"}


@app.get("/transcript/{session_id}")
def transcript(request: Request, session_id: UUID) -> dict[str, object]:
    """Return full conversation transcript for one session."""

    _enforce_api_auth(request)
    items = get_conversation_snapshot(str(session_id))
    return {
        "session_id": str(session_id),
        "message_count": len(items),
        "messages": items,
    }


@app.post("/feedback")
def feedback(request: Request, payload: FeedbackRequest) -> dict[str, str]:
    """Persist a feedback record for analytics and product iteration."""

    _enforce_api_auth(request)
    req_id = _request_id(request)
    entry = {
        "timestamp": int(time()),
        "request_id": req_id,
        "session_id": str(payload.session_id),
        "rating": payload.rating,
        "intent": payload.intent,
        "comment": payload.comment,
    }
    append_feedback(entry, SETTINGS.feedback_log_path)
    return {"status": "feedback recorded"}


def run_cli() -> None:
    """Run a local terminal chat loop for quick manual testing."""

    session_id = str(uuid4())
    print("Plexi Bot CLI mode. Commands: /help, /reset, /new, /exit")
    print(f"Session ID: {session_id}")
    while True:
        user_message = input("You: ").strip()
        if not user_message:
            continue
        if user_message.lower() in {"/exit", "exit", "quit"}:
            print("Bye!")
            break
        if user_message.lower() == "/reset":
            reset_conversation(session_id)
            print("Conversation reset.")
            continue
        if user_message.lower() == "/help":
            print(build_help_message())
            continue
        if user_message.lower() == "/new":
            session_id = str(uuid4())
            print(f"New session: {session_id}")
            continue
        intent, reply = route_message(session_id, user_message)
        print(f"Plexi Bot [{intent}]: {reply}")


if __name__ == "__main__":
    run_cli()
