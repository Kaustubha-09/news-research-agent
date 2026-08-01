from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()  # reads GROQ_API_KEY from .env into the environment

llm = ChatGroq(model="llama-3.3-70b-versatile")

response = llm.invoke("Hello! In one sentence, what can you help me with?")

print(response.content)
