import os
import uuid
import urllib.parse
from typing import TypedDict, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import requests
from azure.storage.blob import BlobServiceClient, ContentSettings
from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, START, END

load_dotenv()

search_tool = TavilySearch(max_results=3)
llm = ChatGroq(model="llama-3.3-70b-versatile")

MAX_SEARCHES = 3
OUTPUT_DIR = "outputs"
BLOB_CONTAINER_NAME = "infographics"

# If this is set (e.g. in the deployed container), images go to Azure Blob
# Storage — persistent, shared across replicas. If unset (local dev), we
# fall back to writing to the local outputs/ folder, same as before.
AZURE_STORAGE_CONNECTION_STRING = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")


class ResearchReport(BaseModel):
    headline: str = Field(description="A short, punchy news-style headline")
    key_developments: list[str] = Field(
        description="3-6 bullet points, each one concrete development or fact"
    )
    sources: list[str] = Field(description="URLs or publication names actually used")
    image_prompt: str = Field(
        description=(
            "A short prompt describing a purely visual, atmospheric cover image "
            "for this report — a scene, mood, or symbolic imagery related to the "
            "topic. Do NOT ask for any text, words, labels, charts, or numbers "
            "to appear in the image — image models render text as garbled "
            "gibberish, so describe imagery only."
        )
    )


class ResearchState(TypedDict):
    query: str
    search_results: list[str]
    num_searches: int
    verdict: str
    report: Optional[ResearchReport]
    image_url: Optional[str]


def search_node(state: ResearchState) -> dict:
    result = search_tool.invoke({"query": state["query"]})
    return {
        "search_results": state["search_results"] + [str(result)],
        "num_searches": state["num_searches"] + 1,
    }


def analyze_node(state: ResearchState) -> dict:
    combined = "\n\n---\n\n".join(state["search_results"])
    prompt = (
        f"Topic: {state['query']}\n\n"
        f"Search results so far:\n{combined}\n\n"
        "Do these results give enough concrete, specific information to write a "
        "solid news summary? Reply with exactly one word first — SUFFICIENT or MORE — "
        "then a short reason."
    )
    response = llm.invoke(prompt)
    verdict = "SUFFICIENT" if response.content.strip().upper().startswith("SUFFICIENT") else "MORE"
    print(f"[analyze] round {state['num_searches']} -> verdict: {verdict}")
    return {"verdict": verdict}


def route_after_analysis(state: ResearchState) -> str:
    if state["verdict"] == "SUFFICIENT" or state["num_searches"] >= MAX_SEARCHES:
        return "summarize"
    return "search"


def summarize_node(state: ResearchState) -> dict:
    combined = "\n\n---\n\n".join(state["search_results"])
    prompt = (
        f"Write a research report about: {state['query']}\n\n"
        f"Use only these search results as your source material:\n{combined}"
    )
    structured_llm = llm.with_structured_output(ResearchReport)
    report = structured_llm.invoke(prompt)
    return {"report": report}


# --- New node: turn report.image_prompt into an actual image file ---
def generate_image_node(state: ResearchState) -> dict:
    prompt = state["report"].image_prompt

    # Pollinations serves an image directly from a GET request — the prompt
    # goes in the URL path itself, so it must be URL-encoded.
    encoded_prompt = urllib.parse.quote(prompt)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        "?width=1024&height=1024&nologo=true&model=flux"
    )

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    filename = f"infographic_{uuid.uuid4().hex[:8]}.png"

    if AZURE_STORAGE_CONNECTION_STRING:
        blob_service = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        blob_client = blob_service.get_blob_client(container=BLOB_CONTAINER_NAME, blob=filename)
        blob_client.upload_blob(
            response.content,
            overwrite=True,
            content_settings=ContentSettings(content_type="image/png"),
        )
        image_url = blob_client.url  # a real, publicly-fetchable https:// URL
    else:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        image_path = os.path.join(OUTPUT_DIR, filename)
        with open(image_path, "wb") as f:
            f.write(response.content)
        image_url = f"/outputs/{filename}"  # relative — api.py serves this via StaticFiles

    return {"image_url": image_url}


graph = StateGraph(ResearchState)
graph.add_node("search", search_node)
graph.add_node("analyze", analyze_node)
graph.add_node("summarize", summarize_node)
graph.add_node("generate_image", generate_image_node)

graph.add_edge(START, "search")
graph.add_edge("search", "analyze")
graph.add_conditional_edges("analyze", route_after_analysis)
graph.add_edge("summarize", "generate_image")
graph.add_edge("generate_image", END)

app = graph.compile()


if __name__ == "__main__":
    import sys

    query = " ".join(sys.argv[1:]) or "latest developments in AI coding agents this week"

    initial_state: ResearchState = {
        "query": query,
        "search_results": [],
        "num_searches": 0,
        "verdict": "",
        "report": None,
        "image_url": None,
    }
    result = app.invoke(initial_state)

    report = result["report"]
    print(f"\n--- Ran {result['num_searches']} search round(s) ---")
    print(f"\nHeadline: {report.headline}")
    print(f"Image prompt used: {report.image_prompt}")
    print(f"\nImage: {result['image_url']}")
