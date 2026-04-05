import os
import sys
import asyncio
import uuid
from dotenv import load_dotenv

# Resolve this file's directory (absolute)
_THIS_DIR = os.path.abspath(os.path.dirname(__file__))

# Ensure workorch is importable
sys.path.insert(0, _THIS_DIR)

# Load .env from the workorch directory BEFORE any ADK/agent imports
load_dotenv(os.path.join(_THIS_DIR, '.env'), override=True)

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from auth import (
    get_credentials, get_web_auth_url, exchange_code_for_credentials,
    get_user_info, clear_token
)
from agent import root_agent, create_or_update_profile

# ADK imports
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# =====================================================
# FastAPI App
# =====================================================

app = FastAPI(title="WorkOrch")

STATIC_DIR = os.path.join(_THIS_DIR, "static")
REDIRECT_URI = "http://localhost:8000/auth/callback"

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ADK Runner setup
session_service = InMemorySessionService()
runner = Runner(
    agent=root_agent,
    app_name="workorch",
    session_service=session_service,
)

# In-memory mapping of user to session id
user_sessions = {}


async def get_or_create_session(user_id: str):
    """Get or create a session for the user."""
    if user_id not in user_sessions:
        session_id = str(uuid.uuid4())
        session = await session_service.create_session(
            app_name="workorch",
            user_id=user_id,
            session_id=session_id,
        )
        user_sessions[user_id] = session_id
    return user_sessions[user_id]


# =====================================================
# Auth Routes
# =====================================================

@app.get("/auth/login")
async def auth_login():
    """Redirect user to Google sign-in."""
    auth_url = get_web_auth_url(REDIRECT_URI)
    return RedirectResponse(url=auth_url)


@app.get("/auth/callback")
async def auth_callback(code: str = None, error: str = None):
    """Handle Google OAuth callback."""
    if error:
        return HTMLResponse(f"<h1>Auth Error</h1><p>{error}</p>", status_code=400)
    if not code:
        return HTMLResponse("<h1>No code received</h1>", status_code=400)

    creds = exchange_code_for_credentials(code, REDIRECT_URI)
    user_info = get_user_info(creds)

    # Auto-create/update WorkOrch profile
    if user_info.get("name"):
        create_or_update_profile(user_name=user_info["name"])

    return RedirectResponse(url="/")


@app.get("/auth/logout")
async def auth_logout():
    """Clear token and redirect to login."""
    clear_token()
    return RedirectResponse(url="/auth/login")


# =====================================================
# API Routes
# =====================================================

@app.get("/api/user")
async def api_user():
    """Return the current authenticated user's info."""
    creds = get_credentials()
    if not creds or not creds.valid:
        return JSONResponse({"authenticated": False}, status_code=401)

    user_info = get_user_info(creds)
    return JSONResponse({"authenticated": True, **user_info})


@app.post("/api/chat")
async def api_chat(request: Request):
    """Send a message to the ADK agent and return the response."""
    creds = get_credentials()
    if not creds or not creds.valid:
        return JSONResponse({"error": "Not authenticated"}, status_code=401)

    body = await request.json()
    message = body.get("message", "").strip()
    if not message:
        return JSONResponse({"error": "Empty message"}, status_code=400)

    user_info = get_user_info(creds)
    user_id = user_info.get("email", "default_user")
    session_id = await get_or_create_session(user_id)

    # Build the user message
    content = types.Content(
        role="user",
        parts=[types.Part(text=message)]
    )

    # Run the agent
    response_text = ""
    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content,
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        # Only collect final agent responses (not tool calls)
                        if event.author != "orchestrator_agent" or not any(
                            p.function_call for p in event.content.parts
                        ):
                            response_text = part.text
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

    return JSONResponse({"response": response_text})


# =====================================================
# Main Page
# =====================================================

@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve main page or redirect to login."""
    creds = get_credentials()
    if not creds or not creds.valid:
        return RedirectResponse(url="/auth/login")

    # Serve the HTML file
    html_path = os.path.join(STATIC_DIR, "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


# =====================================================
# Run
# =====================================================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
