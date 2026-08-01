# News Research Agent

> A LangGraph research agent that searches the live web, reflects on whether it has enough information before writing, produces a Pydantic-validated structured report, and generates a cover image — containerized and deployed to Azure.

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)](https://www.python.org)
[![LangGraph](https://img.shields.io/badge/Agent-LangGraph-1C3C3C)](https://www.langchain.com/langgraph)
[![Groq](https://img.shields.io/badge/LLM-Groq%20Llama%203.3%2070B-F55036?logo=groq)](https://groq.com)
[![Tavily](https://img.shields.io/badge/Search-Tavily-6E56CF)](https://tavily.com)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/UI-React%20%2B%20Vite-61DAFB?logo=react)](https://react.dev)
[![Docker](https://img.shields.io/badge/Container-Docker-2496ED?logo=docker)](https://www.docker.com)
[![Azure](https://img.shields.io/badge/Cloud-Azure-0078D4?logo=microsoftazure)](https://azure.microsoft.com)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A naive "search then summarize" script can't tell a thin result set from a solid one — it just writes whatever it finds. This agent adds a genuine decision point: after searching, an LLM call judges whether the results are actually sufficient, and loops back to search again (capped, so it can't run away) if they aren't. That reflection step, plus forcing the final answer into a validated schema instead of free text, is what separates an "agent" from a script that calls an API twice.

| Pattern | Implementation |
|---|---|
| Tool calling | LLM requests a Tavily search; the graph executes it and returns results — the model never runs code itself |
| Reflection loop | A second LLM call judges sufficiency (`SUFFICIENT` / `MORE`) and conditionally routes back to search, capped at `MAX_SEARCHES` |
| Structured output | `llm.with_structured_output(ResearchReport)` — a Pydantic model, not a parsed paragraph |
| Multimodal generation | Report's `image_prompt` field feeds a separate image-generation call, wired in as its own graph node |
| Provider-agnostic design | LLM calls isolated behind a single `ChatGroq` instance — swappable without touching graph logic |

---

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

---

## Repo layout

Built in incremental phases, kept as separate files to see each concept in isolation rather than one finished script:

- `main.py` — Phase 1: a single Groq LLM call
- `phase2_tool_call.py` — Phase 2: manual tool calling (LLM decides, we execute, LLM interprets)
- `phase3_langgraph.py` — Phase 3: LangGraph automates the tool-call loop
- `phase4_state_routing.py` — Phase 4: custom state + conditional "enough research?" routing
- `phase5_structured_output.py` — Phase 5: Pydantic-validated structured output
- `phase6_image_generation.py` — Phase 6: adds image generation; **this is what `api.py` actually imports and runs**
- `api.py` — Phase 7: FastAPI wrapper around the graph
- `frontend/` — Phase 8: React UI
- `Dockerfile` — Phase 9: containerization

---

## Running locally

```bash
# Backend
uv sync
cp .env.example .env   # fill in GROQ_API_KEY and TAVILY_API_KEY
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

---

## Deployment

Deployed as: **Azure Container Apps** (backend, via Azure Container Registry) + **Azure Blob Storage** (persistent image storage, falls back to local disk if unconfigured) + **Azure Static Web Apps** (frontend, static Vite build). Secrets are stored as Container App secrets, never baked into the image.

> Cloud resources were torn down after the demo session to control cost (student subscription) — the app is fully reproducible from this repo. Redeploy with: `az group create` → `az acr create` → `az containerapp env create` → `az containerapp create` → `az storage account create` → `az staticwebapp create`, then build/push the image and deploy the frontend build.

---

## Limitations

- **Free-tier image generation** — Pollinations.ai has no quality/uptime guarantees; text rendered inside images is unreliable, so prompts are constrained to pure visual scenes.
- **No persistent chat/session history** — each request is stateless; no conversation memory across queries.
- **Fixed search cap** — `MAX_SEARCHES = 3` is a static safety limit, not an adaptive budget.
- **No automated tests** — built as a learning project; correctness was verified manually at each phase.

## Roadmap

1. **Monitoring** — Azure Monitor / Application Insights instead of manual log-tailing.
2. **Key Vault** — move secrets from Container App secrets to centrally managed, rotatable Key Vault references.
3. **Provider swap** — add Microsoft Foundry as an alternate LLM backend, proving the graph logic is provider-agnostic.
4. **Automated tests** — unit tests per graph node, integration test for the full `search → analyze → summarize → generate_image` path.

---

## Project Stats

- **6** LangGraph nodes (`search`, `analyze`, `summarize`, `generate_image`, plus routing)
- **1** conditional edge (reflection-loop routing)
- **2** external APIs (Tavily search, Pollinations image generation)
- **1** LLM (`llama-3.3-70b-versatile` via Groq), swappable via a single wrapper
- **3** deployed Azure services (Container Apps, Blob Storage, Static Web Apps)

## License

[MIT](LICENSE)

---

*Built by [Kaustubha Eluri](https://github.com/Kaustubha-09).*
