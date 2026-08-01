from typing import TypedDict
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, START, END

load_dotenv()

search_tool = TavilySearch(max_results=3)
llm = ChatGroq(model="llama-3.3-70b-versatile")

MAX_SEARCHES = 3


# --- Our own state schema, not just a message list ---
class ResearchState(TypedDict):
    query: str
    search_results: list[str]
    num_searches: int
    verdict: str  # "SUFFICIENT" or "MORE" — set by the analyze node
    summary: str


# --- Node: run a search and accumulate the raw results into state ---
def search_node(state: ResearchState) -> dict:
    result = search_tool.invoke({"query": state["query"]})
    return {
        "search_results": state["search_results"] + [str(result)],
        "num_searches": state["num_searches"] + 1,
    }


# --- Node: ask the LLM to judge whether we have enough to write a good summary ---
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


# --- Conditional edge: loop back to search, or move on to summarize ---
def route_after_analysis(state: ResearchState) -> str:
    if state["verdict"] == "SUFFICIENT" or state["num_searches"] >= MAX_SEARCHES:
        return "summarize"
    return "search"


# --- Node: write the final summary from everything gathered ---
def summarize_node(state: ResearchState) -> dict:
    combined = "\n\n---\n\n".join(state["search_results"])
    prompt = (
        f"Write a concise, well-sourced news summary about: {state['query']}\n\n"
        f"Use only these search results as your source material:\n{combined}"
    )
    response = llm.invoke(prompt)
    return {"summary": response.content}


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
        "summary": "",
    }
    result = app.invoke(initial_state)

    print(f"--- Ran {result['num_searches']} search round(s) ---")
    print("\n--- Final summary ---")
    print(result["summary"])
