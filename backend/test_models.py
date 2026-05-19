"""Test which Groq models are available for tool calling."""
import os
from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

models_to_test = [
    "gemma2-9b-it",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]

for model_name in models_to_test:
    try:
        llm = ChatGroq(model=model_name, api_key=os.getenv("GROQ_API_KEY"))
        response = llm.invoke([HumanMessage(content="Say hello in one word.")])
        print(f"[OK] {model_name}: {response.content[:50]}")
    except Exception as e:
        print(f"[FAIL] {model_name}: {str(e)[:100]}")

print("\nDone.")
