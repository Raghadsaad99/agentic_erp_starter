# services/llm.py
import os
from langchain_openai import ChatOpenAI

# Read the API key from environment variable for security
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError(
        "Missing OpenAI API key. Please set OPENAI_API_KEY in your environment."
    )

# Single shared LLM instance
llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
    temperature=float(os.getenv("OPENAI_TEMPERATURE", "0")),
    openai_api_key=OPENAI_API_KEY
)
