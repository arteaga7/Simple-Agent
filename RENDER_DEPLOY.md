# Deploying to Render

This app deploys as **two Render web services** (the FastAPI API and the
Streamlit UI) plus a **Postgres** database. A [`render.yaml`](render.yaml)
Blueprint wires them together.

## Prerequisites
- Code pushed to GitHub (`arteaga7/Simple-Agent`).
- A Gemini API key.
- A Render Postgres instance (you already have one). Copy its **Internal
  Database URL** from the Render dashboard → your DB → *Connections*.

## Deploy with the Blueprint (recommended)
1. Push the latest commit (including `render.yaml`) to GitHub.
2. Render dashboard → **New** → **Blueprint** → pick this repo.
3. Render reads `render.yaml` and creates **simple-agent-api** and
   **simple-agent-ui**. It prompts for the `sync: false` secrets — enter:
   - `GEMINI_API_KEY` → your Gemini key
   - `DATABASE_URL` → your Postgres **Internal Database URL**
4. Click **Apply**. The API builds first; the UI's `API_URL` is auto-wired to
   the API's hostname.
5. Open the **simple-agent-ui** URL when both go live.

## Notes
- **Ports**: Render injects `$PORT`; both services bind to it via their
  `dockerCommand` (the local `docker-compose` setup is unchanged).
- **Auto-seeding**: the API seeds the catalog on startup, so a fresh database
  populates itself.
- **Free plan** spins services down after ~15 min idle; the first request then
  cold-starts (~30–60s). Upgrade either service to **Starter** to keep it warm.
- **If the UI can't reach the API**: set the UI service's `API_URL` env var
  manually to the API's full URL, e.g. `https://simple-agent-api.onrender.com`.
- **Use a Render-managed DB instead** of your existing one: uncomment the
  `databases:` block in `render.yaml` and switch `DATABASE_URL` to the
  `fromDatabase` form (commented in the file).

## Security
- `.env` is gitignored and excluded via `.dockerignore`, so secrets are never
  baked into the image or committed. On Render, all secrets come from the
  dashboard env vars.
