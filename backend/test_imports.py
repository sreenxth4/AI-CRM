"""Quick test to verify all imports work correctly."""
try:
    from langgraph.graph import StateGraph, START, END, add_messages
    print("OK: langgraph.graph imports")
except ImportError as e:
    print(f"FAIL: langgraph.graph - {e}")

try:
    from langgraph.prebuilt import ToolNode, tools_condition
    print("OK: langgraph.prebuilt imports")
except ImportError as e:
    print(f"FAIL: langgraph.prebuilt - {e}")

try:
    from langchain_groq import ChatGroq
    print("OK: langchain_groq imports")
except ImportError as e:
    print(f"FAIL: langchain_groq - {e}")

try:
    from langchain_core.tools import tool
    print("OK: langchain_core.tools imports")
except ImportError as e:
    print(f"FAIL: langchain_core.tools - {e}")

try:
    from fastapi import FastAPI
    print("OK: fastapi imports")
except ImportError as e:
    print(f"FAIL: fastapi - {e}")

try:
    from sqlalchemy import create_engine
    print("OK: sqlalchemy imports")
except ImportError as e:
    print(f"FAIL: sqlalchemy - {e}")

print("\nAll import checks complete.")
