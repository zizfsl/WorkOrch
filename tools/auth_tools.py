from tools.profile_tools import create_or_update_profile

def login_with_google() -> str:
    """
    Log the user in using Google Auth.
    This opens a browser window. Once successful, it creates or updates
    the user's profile with their real name from Google.
    """
    try:
        from workorch.auth import authenticate_with_google
    except ModuleNotFoundError:
        from auth import authenticate_with_google  # type: ignore
        
    result = authenticate_with_google()
    
    if "error" in result:
        return f"Login failed: {result['error']}"
        
    name = result.get("name")
    
    # Update profile in WorkOrch leveraging existing capabilities
    create_or_update_profile(user_name=name)
    
    return f"Successfully logged in with Google! Welcome, {name}."
