# Deployment Guide

## Architecture

```
┌─────────────────┐         ┌──────────────────┐
│   Vercel         │  HTTPS  │   Railway         │
│   (Frontend)     │────────▶│   (Backend API)   │
│   React + Vite   │  WSS    │   FastAPI + UV    │
└─────────────────┘         └──────┬───────────┘
                                   │
                              ┌────▼────┐
                              │ /data   │
                              │ Volume  │
                              └─────────┘
```

## Backend — Railway

### Environment Variables

Set these in the Railway dashboard:

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | Yes | `sk-ant-...` | Claude API key |
| `DATA_DIR` | Yes | `/data` | Persistent storage path (Railway volume mount) |
| `CORS_ORIGINS` | Yes | `https://your-app.vercel.app` | Frontend URL (comma-separated for multiple) |
| `OPENAI_API_KEY` | No | `sk-...` | For embeddings (RAG, experimental) |

`PORT` is automatically provided by Railway.

### Volume Setup

1. In Railway dashboard, add a volume to your service
2. Set mount path to `/data`
3. Set `DATA_DIR=/data` in environment variables

The app creates `uploads/` and `outputs/` subdirectories automatically.

### Configuration Files

- `railway.json` — Railpack builder, start command, health check
- `nixpacks.toml` — Poetry install configuration

### Health Check

The `/health` endpoint returns `{"status": "healthy"}` and is used by Railway for liveness checks.

---

## Frontend — Vercel

### Environment Variables

Set in the Vercel dashboard (Settings > Environment Variables):

| Variable | Value | Description |
|----------|-------|-------------|
| `VITE_API_URL` | `https://your-railway-app.up.railway.app` | Backend API URL |

### Setup

1. Import the repository in Vercel
2. Set **Root Directory** to `frontend`
3. Framework is auto-detected as Vite
4. Add the `VITE_API_URL` environment variable
5. Deploy

### Configuration

`frontend/vercel.json` handles the build command, output directory, and SPA routing rewrites.

---

## Local Development

No environment variables needed — defaults work out of the box:

```bash
# Terminal 1: Backend
poetry run uvicorn src.api.main:app --reload

# Terminal 2: Frontend
cd frontend && npm run dev
```

- Backend runs on `http://localhost:8000`
- Frontend runs on `http://localhost:5173` with Vite proxy to backend
- Data stored in `./data/uploads/` and `./data/outputs/`

### Testing with production-like config

```bash
# Backend with custom data dir and CORS
DATA_DIR=/tmp/test CORS_ORIGINS=https://example.com \
  poetry run uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# Frontend production build
cd frontend && VITE_API_URL=http://localhost:8000 npm run build
```
