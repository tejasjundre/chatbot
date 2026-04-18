# Plexi Bot

Plexi Bot is a modular shopping assistant built with Python + FastAPI and designed for production-oriented demos.
It supports Groq, Gemini, and Anthropic as pluggable LLM providers.

## Why This Version Is Sellable

- Multi-provider LLM runtime (`groq`, `gemini`, `anthropic`)
- Conversation workflows: product Q&A, order tracking, return policy, search, sentiment, comparison
- Guided UX: capability cards, sample prompts, follow-up suggestions
- Web-ready API hardening:
  - optional `x-api-key` auth
  - in-memory chat rate limiting
  - CORS configuration
  - request IDs and request logging
- Business endpoints:
  - transcript export per session
  - user feedback capture for product analytics
  - lightweight metrics endpoint
- Deployment artifacts: `Dockerfile`, `.dockerignore`, `Procfile`

## Project Structure

```text
plexi_bot/
├── main.py
├── bot/
│   ├── __init__.py
│   ├── conversation.py
│   ├── data_store.py
│   ├── feedback_store.py
│   ├── guidance.py
│   ├── llm.py
│   ├── prompts.py
│   ├── rate_limit.py
│   ├── router.py
│   └── settings.py
├── features/
│   ├── __init__.py
│   ├── product_qa.py
│   ├── order_status.py
│   ├── return_policy.py
│   ├── generative_search.py
│   ├── sentiment.py
│   ├── comparison.py
│   ├── add_to_cart.py
│   ├── price_tracking.py
│   └── auto_reorder.py
├── frontend/
│   └── index.html
├── data/
│   ├── products.json
│   ├── orders.json
│   └── return_policy.json
├── tests/
│   ├── test_features.py
│   ├── test_platform.py
│   └── test_rate_limit.py
├── .env.example
├── requirements.txt
├── Dockerfile
└── Procfile
```

## Setup

1. Create venv and install dependencies:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Create `.env`:
   ```bash
   copy .env.example .env
   ```
3. Choose one provider in `.env`:

   Groq (recommended):
   ```env
   LLM_PROVIDER=groq
   GROQ_MODEL=llama-3.1-8b-instant
   GROQ_API_KEY=your_real_groq_key
   ```

   Gemini:
   ```env
   LLM_PROVIDER=gemini
   GEMINI_MODEL=gemini-2.0-flash
   GEMINI_API_KEY=your_real_gemini_key
   ```

   Anthropic:
   ```env
   LLM_PROVIDER=anthropic
   ANTHROPIC_MODEL=claude-sonnet-4-20250514
   ANTHROPIC_API_KEY=your_real_anthropic_key
   ```

## Production Controls (`.env`)

```env
APP_ENV=production
APP_API_KEY=          # set to enable x-api-key protection
CORS_ORIGINS=*        # comma-separated origins in production
CHAT_RATE_LIMIT_PER_MINUTE=30
ENABLE_METRICS=true
FEEDBACK_LOG_PATH=data/feedback_log.jsonl
```

## Run

Local API:
```bash
python -m uvicorn main:app --reload
```

UI:
```text
http://127.0.0.1:8000/ui
```

CLI mode:
```bash
python main.py
```

## API Endpoints

- `GET /ui` browser chat workspace
- `GET /config/public` auth/rate-limit client hints
- `GET /capabilities` starter capabilities and prompt cards
- `GET /health` runtime provider/model/config + uptime
- `GET /metrics` operational summary (protected when `APP_API_KEY` set)
- `POST /chat`
  - body: `{"session_id":"uuid","message":"text"}`
- `POST /reset`
  - body: `{"session_id":"uuid"}`
- `GET /transcript/{session_id}` full session transcript
- `POST /feedback`
  - body: `{"session_id":"uuid","rating":1-5,"comment":"...","intent":"..."}`

## Docker Deployment

Build:
```bash
docker build -t plexi-bot:latest .
```

Run:
```bash
docker run --rm -p 8000:8000 --env-file .env plexi-bot:latest
```

## Fast Cloud Deploy (From GitHub)

Repo:
```text
https://github.com/tejasjundre/chatbot
```

Render (recommended fastest):
1. Open `https://dashboard.render.com/blueprints`
2. Click `New Blueprint Instance`
3. Select the `chatbot` repo (uses `render.yaml`)
4. Set secret env vars:
   - `GROQ_API_KEY`
   - `APP_API_KEY` (optional, for protected API)
5. Deploy

Railway:
1. Open `https://railway.app/new`
2. Choose `Deploy from GitHub repo`
3. Select `chatbot` repo (uses `railway.toml` + Docker/Nixpacks)
4. Add env vars from `.env.example`
5. Deploy

## Demo Script (Sales + Technical Round)

1. `Show me wireless headphones under 3000`
2. `What do people think about SoundMax Pro?`
3. `Compare SoundMax Pro vs AirMax 3000`
4. `Track ORD-1042`
5. `What is your return policy for refunds?`
6. Export transcript from UI and submit 5-star feedback

## Tests

Run:
```bash
python -m pytest -q
```

## Troubleshooting

- `AI is not configured yet...`:
  - set provider key in `.env`
  - restart the server
- `AI quota is exceeded...`:
  - check provider quota/billing
- `401 Unauthorized`:
  - set `x-api-key` header or configure UI with the key if `APP_API_KEY` is enabled
