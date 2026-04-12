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
print(f"DEBUG: GOOGLE_APPLICATION_CREDENTIALS = {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')}")

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from auth import (
    get_credentials, get_web_auth_url, exchange_code_for_credentials,
    get_user_info, clear_token, save_credentials
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
BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000").rstrip("/")
REDIRECT_URI = f"{BASE_URL}/auth/callback"

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
    auth_url, code_verifier = get_web_auth_url(REDIRECT_URI)
    response = RedirectResponse(url=auth_url)
    if code_verifier:
        response.set_cookie(key="cv", value=code_verifier, httponly=True)
    return response


@app.get("/auth/callback")
async def auth_callback(request: Request, code: str = None, state: str = None, error: str = None):
    """Handle Google OAuth callback."""
    if error:
        return HTMLResponse(f"<h1>Auth Error</h1><p>{error}</p>", status_code=400)
    if not code:
        return HTMLResponse("<h1>No code received</h1>", status_code=400)

    try:
        # Re-create the flow using the state from Google's callback URL
        code_verifier = request.cookies.get("cv")
        creds = exchange_code_for_credentials(code, REDIRECT_URI, state=state, code_verifier=code_verifier)
    except Exception as e:
        print(f"[ERROR] TOKEN EXCHANGE ERROR: {e}")
        return HTMLResponse(f"<h1>Login Error</h1><p>{e}</p>", status_code=500)

    try:
        user_info = get_user_info(creds)
    except Exception as e:
        print(f"[ERROR] USER INFO ERROR: {e}")
        user_info = {}

    # Auto-create/update WorkOrch profile (non-fatal if DB is down)
    if user_info.get("name"):
        try:
            create_or_update_profile(user_name=user_info["name"])
        except Exception as e:
            print(f"[ERROR] PROFILE CREATION ERROR (non-fatal): {e}")

    # Set up session
    session_id = str(uuid.uuid4())
    save_credentials(session_id, creds)
    
    response = RedirectResponse(url="/")
    response.set_cookie(key="session_id", value=session_id, httponly=True)
    return response


@app.get("/auth/logout")
async def auth_logout(request: Request):
    """Clear token and redirect to login."""
    session_id = request.cookies.get("session_id")
    clear_token(session_id)
    response = RedirectResponse(url="/")
    if session_id:
        response.delete_cookie(key="session_id")
    return response


# =====================================================
# API Routes
# =====================================================

@app.get("/api/user")
async def api_user(request: Request):
    """Return the current authenticated user's info."""
    session_id = request.cookies.get("session_id")
    creds = get_credentials(session_id)
    if not creds or not creds.valid:
        return JSONResponse({"authenticated": False}, status_code=401)

    user_info = get_user_info(creds)
    return JSONResponse({"authenticated": True, **user_info})


@app.post("/api/chat")
async def api_chat(request: Request):
    """Send a message to the ADK agent and return the response."""
    session_id = request.cookies.get("session_id")
    creds = get_credentials(session_id)
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
async def index(request: Request):
    """Serve main page or landing page."""
    session_id = request.cookies.get("session_id")
    creds = get_credentials(session_id)
    if not creds or not creds.valid:
        html_path = os.path.join(STATIC_DIR, "landing.html")
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())

    # Serve the HTML file
    html_path = os.path.join(STATIC_DIR, "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


# =====================================================
# Run
# =====================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
