from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode

load_dotenv()

search_tool = TavilySearch(max_results=3)
llm = ChatGroq(model="llama-3.3-70b-versatile")
llm_with_tools = llm.bind_tools([search_tool])


# --- Node 1: ask the model to think / decide whether to call a tool ---
def call_model(state: MessagesState):
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}  # LangGraph appends this to state["messages"]


# --- Node 2: actually run any tool the model requested ---
# ToolNode is a prebuilt node that reads the last message's tool_calls,
# executes them, and returns ToolMessages — this is exactly what we
# hand-wrote in phase2_tool_call.py, now reusable.
tool_node = ToolNode([search_tool])


# --- Conditional edge: after the model responds, do we need to run a tool,
#     or are we done? ---
def should_continue(state: MessagesState):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END


# --- Build the graph ---
graph = StateGraph(MessagesState)
graph.add_node("agent", call_model)
graph.add_node("tools", tool_node)

graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", should_continue)
graph.add_edge("tools", "agent")  # after tools run, go back to the model

app = graph.compile()


if __name__ == "__main__":
    question = "What are the latest developments in AI coding agents this week?"
    result = app.invoke({"messages": [("human", question)]})

    print("--- Full message trace ---")
    for m in result["messages"]:
        print(f"[{m.type}] {m.content[:200]}")

    print("\n--- Final answer ---")
    print(result["messages"][-1].content)
