from typing import TypedDict, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, START, END

load_dotenv()

search_tool = TavilySearch(max_results=3)
llm = ChatGroq(model="llama-3.3-70b-versatile")

MAX_SEARCHES = 3


# --- The schema we force the final answer into, instead of loose text ---
class ResearchReport(BaseModel):
    headline: str = Field(description="A short, punchy news-style headline")
    key_developments: list[str] = Field(
        description="3-6 bullet points, each one concrete development or fact"
    )
    sources: list[str] = Field(description="URLs or publication names actually used")
    image_prompt: str = Field(
        description="A short prompt describing an infographic/cover image for this report"
    )


class ResearchState(TypedDict):
    query: str
    search_results: list[str]
    num_searches: int
    verdict: str
    report: Optional[ResearchReport]


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


# --- This is the only node that changes meaningfully in Phase 5 ---
def summarize_node(state: ResearchState) -> dict:
    combined = "\n\n---\n\n".join(state["search_results"])
    prompt = (
        f"Write a research report about: {state['query']}\n\n"
        f"Use only these search results as your source material:\n{combined}"
    )

    # with_structured_output makes the LLM call return a validated
    # ResearchReport instance instead of a free-text string. Under the hood
    # LangChain turns the Pydantic schema into a tool/JSON-schema definition
    # and forces the model's response to conform to it.
    structured_llm = llm.with_structured_output(ResearchReport)
    report = structured_llm.invoke(prompt)
    return {"report": report}


graph = StateGraph(ResearchState)
graph.add_node("search", search_node)
graph.add_node("analyze", analyze_node)
graph.add_node("summarize", summarize_node)

graph.add_edge(START, "search")
graph.add_edge("search", "analyze")
graph.add_conditional_edges("analyze", route_after_analysis)
graph.add_edge("summarize", END)

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
    }
    result = app.invoke(initial_state)

    print(f"\n--- Ran {result['num_searches']} search round(s) ---")
    report = result["report"]

    print("\n--- Structured report ---")
    print(f"Headline: {report.headline}\n")
    print("Key developments:")
    for point in report.key_developments:
        print(f"  - {point}")
    print("\nSources:")
    for src in report.sources:
        print(f"  - {src}")
    print(f"\nImage prompt: {report.image_prompt}")

    # This is the payoff: report.model_dump() is a plain dict/JSON,
    # exactly what you'd return from a FastAPI endpoint in Phase 7.
    print("\n--- As JSON (what an API would return) ---")
    print(report.model_dump_json(indent=2))
