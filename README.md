# Simple-LLM — Agente de pedidos

A small **tool-calling agent** that takes and validates customer orders against a provider
catalog. Sebastián (the agent) looks up prices and stock **live from PostgreSQL** via tools,
validates requests, and persists confirmed orders — no more hardcoded price lists.

## 🧠 What it does

- **Agent loop** (not a single LLM call): the model decides which tools to call, the server
  runs them, feeds results back, and loops until it has a final answer.
- **Tools**: `get_price`, `search_products`, `check_stock`, `create_order`, `get_order_status`.
- **PostgreSQL** stores the catalog, inventory, orders, and full conversation history
  (so memory survives restarts).
- **Groq** for inference (OpenAI-compatible), defaulting to `llama-3.3-70b-versatile`.

## 🌎 Structure

```
Simple-LLM/
├── main.py                 # ASGI entrypoint -> bot.app_factory.create_app()
├── app.py                  # Streamlit chat client
├── bot/
│   ├── config.py           # settings (env / .env)
│   ├── app_factory.py      # FastAPI app; creates tables + seeds catalog on startup
│   ├── api/                # routes (/chat, /health) + request schemas
│   ├── db/                 # SQLAlchemy engine, models, seed
│   ├── agent/              # llm client, conversation memory, tool-calling loop
│   └── tools/              # catalog / inventory / orders tools + registry
├── Dockerfile
├── docker-compose.yml      # db (postgres) + api + ui
└── .env.example
```

## 🚀 Run with Docker (recommended)

1. Clone, then create your env file:
   ```bash
   cp .env.example .env
   # edit .env and set GROQ_API_KEY
   ```
2. Start everything (Postgres + API + Streamlit UI):
   ```bash
   docker compose up --build
   ```
3. Open the UI at <http://localhost:8501>. The API is at <http://localhost:8000>
   (docs at `/docs`). Tables are auto-created and the catalog is seeded on startup.

> The Postgres container is exposed on host port **5433** (to avoid clashing with a local
> Postgres on 5432), e.g. `psql -h localhost -p 5433 -U chatbot chatbot`.

## 🧪 Quick API check

```bash
curl localhost:8000/health
# {"status":"ok"}

curl -X POST localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Quiero 3 camisas","session_id":"t1"}'
```

## 🌱 Seeding the catalog

The 3 default products are seeded automatically on startup. To add/update your own, use the
[seed.py](seed.py) CLI inside the running stack:

```bash
docker compose exec api python seed.py --list                          # show catalog
docker compose exec api python seed.py --add gorra 120 40 "Gorra deportiva"  # add/update one
docker compose exec api python seed.py --file seed_data.json           # bulk add/update from JSON
docker compose exec api python seed.py --reset                         # wipe products, reseed defaults
```

`--add` takes `NAME PRICE STOCK [DESCRIPTION...]`. `--file` expects a JSON list of objects with
`name`, `price`, `stock_quantity`, `description` (see [seed_data.json](seed_data.json)). Edits are
upserts (matched by name). `--reset` deletes all products but leaves existing orders intact.

## 💻 Local dev (without Docker)

Needs a running PostgreSQL. Point `DATABASE_URL` at it (e.g.
`postgresql+psycopg://chatbot:chatbot@localhost:5432/chatbot`).

```bash
python -m venv env && source env/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload          # API on :8000
streamlit run app.py               # UI on :8501  (set API_URL=http://127.0.0.1:8000)
```

## ⚙️ Configuration

All via environment / `.env` — see [.env.example](.env.example):
`GROQ_API_KEY`, `GROQ_MODEL`, `SYSTEM_PROMPT`, `MAX_AGENT_ITERS`, `DATABASE_URL`,
`POSTGRES_USER/PASSWORD/DB`, `API_URL`.

## 🗺️ Roadmap

- **RAG** over product descriptions / policies / FAQ (planned next phase).
- Alembic migrations (currently `create_all()` on startup).
- Auth / rate limiting.
