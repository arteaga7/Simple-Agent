# Simple-Agent

A small **tool-calling agent** that takes and validates customer orders against a provider
catalog (stored in a database). Sebastián (the agent) looks up prices and stock **live from PostgreSQL** via tools,
validates requests, and persists confirmed orders. **Gemini API Key** is needed.

## ✨ Details

- **Agent loop** (not a single LLM call): the model decides which tools to call, the server
  runs them, feeds results back, and loops until it has a final answer.
- **Tools**: `get_price`, `search_products`, `check_stock`, `create_order`, `get_order_status`.
- **PostgreSQL** stores the catalog, inventory, orders, and full conversation history
  (so memory survives restarts).
- **Gemini** for inference, defaulting to `gemini-2.5-flash`.

## 🌎 Structure

```
Simple-Agent/
├── main.py                 # Entrypoint, FastAPI app. Creates tables and seeds catalog on startup
├── app.py                  # Streamlit chat client
├── bot/
│   ├── config.py           # settings (lm model, api url, databse url, etc.)
│   ├── prompts.py          # promts
│   ├── api/                # routes (/chat, /health) + request schemas
│   ├── db/                 # SQLAlchemy engine, models, seed
│   ├── agent/              # llm client, conversation memory, tool-calling loop
│   └── tools/              # catalog / inventory / orders tools + registry
├── img/                    # Some pictures
├── Dockerfile
├── docker-compose.yml      # db (postgres) + api + ui
└── requirements.txt
└── .env                    # Contains API Key (not provided)
└── start.sh                # For deploying to Render.com
```

## ⚙️ Configuration
1. Clone this repository:
   ```bash
   git clone https://github.com/arteaga7/Simple-Agent.git
   ```
2. Create your .env file, with the following content:
   ```bash
   GEMINI_API_KEY=your_API_Key
   ```

## 🚀 Run with Docker (recommended)

1. Clone and create .env file, as explained in 'Configuration' section.
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

## 💻 Local dev (without Docker)

Needs a running PostgreSQL. Point `DATABASE_URL` at it (e.g.
`postgresql+psycopg://chatbot:chatbot@localhost:5432/chatbot`).

1. Clone and create .env file, as explained in 'Configuration' section.
2. Run:
  ```bash
  python3 -m venv env && source env/bin/activate
  pip install -r requirements.txt
  uvicorn main:app --reload          # API on :8000
  streamlit run app.py               # UI on :8501  (API_URL=http://127.0.0.1:8000)
  ```

## 🎯 Results
The chatbot is working correctly, responding politely to a greeting or a purchase order, as shwon in figs 1 and 2.
![alt text](<img/c1.png>)
Fig. 1.

![alt text](<img/c2.png>)
Fig. 2.

After saving a purchase order, it is possible to verify the convesational memory, as shown in Fig. 3.

![alt text](<img/c3.png>)
Fig. 3.

## 🔎 Unexpected behaviour

If the agent responses with "Lo siento ..." or "Intentalo ...", as shown in Fig. 4, it could be an LLM availability problem, a token ran out problem, or may be the agent did not understand the question.
![alt text](<img/c4.png>)
Fig. 4.

In Fig. 5 shows the console result of a token ran out problem.
![alt text](<img/c5.png>)
Fig. 5.

## 🗺️ Further work

This project can be complemented with:
- **RAG** over product descriptions, policies and FAQ.
- Authentication and rate limiting.
