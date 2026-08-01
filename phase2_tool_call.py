from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch
from langchain_core.messages import HumanMessage, ToolMessage

load_dotenv()

# 1. Define the tool the LLM is allowed to use
search_tool = TavilySearch(max_results=3)

# 2. Bind it to the model — this tells the LLM "you may request this tool"
llm = ChatGroq(model="llama-3.3-70b-versatile")
llm_with_tools = llm.bind_tools([search_tool])

question = "What are the latest developments in AI coding agents this week?"

# 3. First call: the LLM sees the question and the available tool,
#    and decides whether it needs to call the tool to answer well.
messages = [HumanMessage(question)]
ai_response = llm_with_tools.invoke(messages)
messages.append(ai_response)

print("--- Did the model request a tool call? ---")
print(ai_response.tool_calls)

# 4. If it asked for a tool call, WE execute it (the LLM never runs code itself)
#    and hand the result back as a ToolMessage.
for tool_call in ai_response.tool_calls:
    result = search_tool.invoke(tool_call["args"])
    messages.append(
        ToolMessage(content=str(result), tool_call_id=tool_call["id"])
    )

# 5. Second call: now the LLM has the search results in its context
#    and can write a real, grounded answer.
final_response = llm_with_tools.invoke(messages)

print("\n--- Final answer ---")
print(final_response.content)
