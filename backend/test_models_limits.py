import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from tools import all_tools

load_dotenv()

models_to_test = [
    "llama3-8b-8192",
    "mixtral-8x7b-32768",
    "llama3-70b-8192",
    "llama-3.1-8b-instant",
]

system_prompt = """You are a pharma CRM AI.
Tools:
1. log_interaction: For NEW interactions. Default to today if no date.
2. edit_interaction: Correct/update data. Requires interaction_id.
3. suggest_followup: Recommend next steps. Requires interaction_id.
4. generate_summary: Create a summary. Requires interaction_id.
5. compliance_check: Verify compliance. Requires interaction_id.

RULES:
- Extract structured data.
- Sentiment: "Positive", "Negative", or "Neutral".
- Current interaction_id: None. Use this for tools 2-5 if not specified.
- Be concise. Confirm changes."""

user_msg = HumanMessage(content="Met Dr. Smith today. Discussed CardioX. Sentiment was positive. Shared brochures.")
sys_msg = SystemMessage(content=system_prompt)

for model in models_to_test:
    print(f"\n--- Testing {model} ---")
    try:
        llm = ChatGroq(model=model, temperature=0, max_retries=0)
        llm_with_tools = llm.bind_tools(all_tools)
        response = llm_with_tools.invoke([sys_msg, user_msg])
        print(f"[SUCCESS] {model} returned: {response.content[:50]}")
        if response.tool_calls:
            print(f"  Tool called: {response.tool_calls[0]['name']}")
    except Exception as e:
        # Get just the error message without full traceback
        error_str = str(e).split('\n')[0][:150]
        print(f"[FAIL] {model}: {error_str}")
