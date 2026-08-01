# News Research Agent

An AI agent that researches a topic across the live web, reflects on whether it has enough information, writes a structured, sourced report, and generates a cover image — built to learn agentic AI development end-to-end, then deployed to Azure.

## What it does

Give it a topic (e.g. "latest developments in AI coding agents"), and it will:

1. Search the web (Tavily)
2. Judge whether the results are sufficient to write a good report — if not, search again (up to 3 rounds)
3. Write a structured report: headline, key developments, sources (validated with Pydantic)
4. Generate a cover image for the report
5. Return it all through a FastAPI endpoint, rendered by a React frontend

## Architecture

```
React (frontend)
      ↓
FastAPI (api.py)
      ↓
LangGraph state machine
      │
      ├── search ──────► Tavily web search
      ├── analyze ─────► Groq LLM (llama-3.3-70b) — "enough info yet?"
      │     └── loops back to search if not, up to MAX_SEARCHES
      ├── summarize ───► Groq LLM, forced into a Pydantic schema
      └── generate_image ► Pollinations.ai (free image generation)
```

## Stack

- **Agent orchestration**: LangGraph (state, conditional routing/reflection loop)
- **LLM**: Groq (`llama-3.3-70b-versatile`) via `langchain-groq`
- **Search**: Tavily
- **Structured output**: Pydantic, via `with_structured_output`
- **Image generation**: Pollinations.ai (free, no API key)
- **Backend**: FastAPI
- **Frontend**: React (Vite)
- **Deployment**: Docker → Azure Container Registry → Azure Container Apps

## Repo layout

This was built in incremental phases, kept as separate files to see each concept in isolation:

- `main.py` — Phase 1: a single Groq LLM call
- `phase2_tool_call.py` — Phase 2: manual tool calling (LLM decides, we execute, LLM interprets)
- `phase3_langgraph.py` — Phase 3: LangGraph automates the tool-call loop
- `phase4_state_routing.py` — Phase 4: custom state + conditional "enough research?" routing
- `phase5_structured_output.py` — Phase 5: Pydantic-validated structured output
- `phase6_image_generation.py` — Phase 6: adds image generation; **this is what `api.py` actually imports and runs**
- `api.py` — Phase 7: FastAPI wrapper around the graph
- `frontend/` — Phase 8: React UI
- `Dockerfile` — Phase 9: containerization
- Phase 10: deployed to Azure Container Apps (see below)

## Running locally

```bash
# Backend
uv sync
cp .env.example .env   # then fill in GROQ_API_KEY and TAVILY_API_KEY
uv run uvicorn api:api --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173`.

## Running with Docker

```bash
docker build -t news-research-agent .
docker run -d -p 8000:8000 --env-file .env -v "$(pwd)/outputs:/app/outputs" news-research-agent
```

## Deployment

**Backend**: Azure Container Apps, backed by Azure Container Registry. Secrets (API keys, storage connection string) are stored as Container App secrets, not baked into the image.

**Frontend**: Azure Static Web Apps, deployed from the production Vite build (`npm run build` → `dist/`).

**Live URLs**:
- Frontend: https://lively-smoke-0e85a860f.7.azurestaticapps.net
- Backend: https://news-research-agent.agreeableriver-806102e7.eastus.azurecontainerapps.io

Generated images are uploaded to Azure Blob Storage (persistent, shared across replicas) whenever `AZURE_STORAGE_CONNECTION_STRING` is set; otherwise the app falls back to writing to a local `outputs/` folder for local development without needing an Azure Storage account.
