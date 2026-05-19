import os
from agent import run_agent

user_message = "Met Dr. Smith today. Discussed CardioX. Sentiment was positive. Shared brochures."

try:
    print("Testing agent invocation...")
    result = run_agent(user_message=user_message)
    print("Success!")
    print(result)
except Exception as e:
    print(f"Error occurred: {str(e)}")
