from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from phase6_image_generation import app as research_graph, OUTPUT_DIR

api = FastAPI(title="News Research Agent")

# The React dev server runs on a different port (5173), which browsers treat
# as a different "origin" — without this, the browser blocks the fetch call
# even though curl works fine (curl doesn't enforce CORS, only browsers do).
api.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Makes files in outputs/ downloadable at http://localhost:8000/outputs/<filename>
api.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")


# --- What the client sends us ---
class ResearchRequest(BaseModel):
    query: str


# --- What we send back — deliberately explicit, not just "whatever the graph returns" ---
class ResearchResponse(BaseModel):
    headline: str
    key_developments: list[str]
    sources: list[str]
    image_url: str
    num_searches: int


@api.post("/research", response_model=ResearchResponse)
def run_research(request: ResearchRequest):
    initial_state = {
        "query": request.query,
        "search_results": [],
        "num_searches": 0,
        "verdict": "",
        "report": None,
        "image_path": None,
    }

    # This is the same .invoke() call from our CLI scripts — the graph
    # doesn't know or care whether it's called from a terminal or an API.
    result = research_graph.invoke(initial_state)
    report = result["report"]

    # image_path looks like "outputs/infographic_ab12cd34.png" — we only
    # want the filename, since StaticFiles serves from that directory root.
    filename = result["image_path"].split("/")[-1]

    return ResearchResponse(
        headline=report.headline,
        key_developments=report.key_developments,
        sources=report.sources,
        image_url=f"/outputs/{filename}",
        num_searches=result["num_searches"],
    )


@api.get("/health")
def health_check():
    return {"status": "ok"}
