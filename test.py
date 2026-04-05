import os
import asyncio
from dotenv import load_dotenv
from agent import root_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Load environment variables from .env
load_dotenv()

print("🤖 Sending request to the Orchestrator Agent...")

APP_NAME = "productivity_tracker"
USER_ID = "test_user"
SESSION_ID = "test_session"

# Explicitly create the session first
session_service = InMemorySessionService()
asyncio.run(session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID))

# Set up the Runner with an in-memory session
runner = Runner(
    app_name=APP_NAME,
    agent=root_agent,
    session_service=session_service
)

# Trigger the Reflection Agent via the Orchestrator
prompt = "I finished 2 hours of deep work and 1 hour of shallow work. Calculate my metrics and save my day's summary."
content = types.Content(role="user", parts=[types.Part(text=prompt)])

print("\n✅ Agent Response:")
for event in runner.run(new_message=content, user_id=USER_ID, session_id=SESSION_ID):
    if event.is_final_response():
        print(event.content.parts[0].text)