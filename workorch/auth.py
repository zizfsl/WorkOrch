import os
import requests
from google_auth_oauthlib.flow import InstalledAppFlow, Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import json

# Scopes enable reading user profile, email address, calendar, and Gmail
SCOPES = [
    'openid', 
    'https://www.googleapis.com/auth/userinfo.profile', 
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/gmail.readonly'
]

BASE_DIR = os.path.dirname(__file__)
CREDS_PATH = os.path.join(BASE_DIR, 'credentials.json')
# Use /tmp for token storage in Cloud Run (which is writable)
TOKEN_PATH = "/tmp/token.json" if os.environ.get("K_SERVICE") else os.path.join(BASE_DIR, 'token.json')


def get_credentials():
    """
    Load saved credentials from token.json.
    Returns the credentials object or None.
    """
    creds = None

    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'r') as token_file:
            creds_data = json.load(token_file)
            creds = Credentials.from_authorized_user_info(creds_data, SCOPES)

    # If scopes changed, force a re-login
    if creds and not creds.has_scopes(SCOPES):
        creds = None
        if os.path.exists(TOKEN_PATH):
            os.remove(TOKEN_PATH)

    # Refresh if expired
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            with open(TOKEN_PATH, 'w') as token_file:
                token_file.write(creds.to_json())
        except Exception:
            creds = None
            if os.path.exists(TOKEN_PATH):
                os.remove(TOKEN_PATH)

    return creds


# Module-level storage for the active flow (preserves state across requests)
_active_flow = None


def get_flow(redirect_uri: str):
    """Helper to create the OAuth flow from file or environment variable."""
    config_json = os.environ.get("GOOGLE_CLIENT_CONFIG")
    if config_json:
        return Flow.from_client_config(json.loads(config_json), scopes=SCOPES, redirect_uri=redirect_uri)
    return Flow.from_client_secrets_file(CREDS_PATH, scopes=SCOPES, redirect_uri=redirect_uri)


def get_web_auth_url(redirect_uri: str) -> str:
    """
    Generate the Google OAuth authorization URL for browser redirect.
    Stores the flow object so it can be reused during token exchange.
    """
    global _active_flow
    _active_flow = get_flow(redirect_uri)
    # Disable PKCE (code_verifier) to avoid 'Missing code verifier' errors
    _active_flow.code_verifier = None
    auth_url, _ = _active_flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    return auth_url


def exchange_code_for_credentials(code: str, redirect_uri: str):
    """
    Exchange the authorization code from Google callback for credentials.
    Reuses the stored flow object.
    """
    global _active_flow
    if _active_flow is None:
        _active_flow = get_flow(redirect_uri)
        _active_flow.code_verifier = None

    _active_flow.fetch_token(code=code)
    creds = _active_flow.credentials

    # Save token
    with open(TOKEN_PATH, 'w') as token_file:
        token_file.write(creds.to_json())

    _active_flow = None  # Clear after use
    return creds


def get_user_info(creds) -> dict:
    """
    Fetch user profile info from Google using credentials.
    """
    user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
    headers = {"Authorization": f"Bearer {creds.token}"}
    
    response = requests.get(user_info_url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return {
            "name": data.get("name", "Unknown"),
            "email": data.get("email", ""),
            "picture": data.get("picture", "")
        }
    return {"name": "Unknown", "email": "", "picture": ""}


def authenticate_with_google():
    """
    Legacy: Authenticate via desktop popup flow.
    Used by agent tools when running outside the web UI.
    """
    creds = get_credentials()
    
    if not creds or not creds.valid:
        if not os.path.exists(CREDS_PATH):
            return {"error": "credentials.json not found in the project directory."}
        flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'w') as token_file:
            token_file.write(creds.to_json())
    
    return get_user_info(creds)


def clear_token():
    """Remove the saved token to force re-authentication."""
    if os.path.exists(TOKEN_PATH):
        os.remove(TOKEN_PATH)


if __name__ == "__main__":
    print(authenticate_with_google())
