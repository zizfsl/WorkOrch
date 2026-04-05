import json
import os
from datetime import date

# =====================================================
# 📂 PATH HELPERS
# =====================================================

WORKORCH_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "workorch")
PROFILES_FILE = os.path.join(WORKORCH_DIR, "user_profiles.json")
LAST_USER_FILE = os.path.join(WORKORCH_DIR, "last_user.json")
MEMORY_FILE = os.path.join(WORKORCH_DIR, "memory.json")


def _load_json(path: str, default=None):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return default if default is not None else {}


def _save_json(path: str, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# =====================================================
# 👤 USER PROFILE TOOLS
# =====================================================

def create_or_update_profile(
    user_name: str,
    role: str = "",
    preferred_work_start: int = 9,
    preferred_work_end: int = 17,
    work_style: str = "deep_work",
    goals: str = ""
) -> str:
    """
    Create a new user profile or update an existing one.
    Also sets this user as the last active user so they are auto-remembered.
    Pass goals as a comma-separated string like 'finish report, read papers'.
    """

    profiles = _load_json(PROFILES_FILE, {})
    key = user_name.strip().lower()
    today = str(date.today())

    if key in profiles:
        # Update existing profile
        profile = profiles[key]
        profile["total_sessions"] = profile.get("total_sessions", 0) + 1
        profile["last_active"] = today
        if role:
            profile["role"] = role
        if goals:
            profile["goals"] = [g.strip() for g in goals.split(",")]
        if preferred_work_start:
            profile["preferred_work_start"] = preferred_work_start
        if preferred_work_end:
            profile["preferred_work_end"] = preferred_work_end
        if work_style:
            profile["work_style"] = work_style
    else:
        # Create new profile
        profile = {
            "name": user_name.strip(),
            "role": role,
            "preferred_work_start": preferred_work_start,
            "preferred_work_end": preferred_work_end,
            "work_style": work_style,
            "goals": [g.strip() for g in goals.split(",")] if goals else [],
            "total_sessions": 1,
            "avg_completion_rate": 0.0,
            "total_deep_work_hours": 0,
            "last_active": today,
            "history": []
        }

    profiles[key] = profile
    _save_json(PROFILES_FILE, profiles)

    # Remember this user as the last active user
    _save_json(LAST_USER_FILE, {"last_user": key})

    return f"Profile for '{user_name}' saved. Sessions: {profile['total_sessions']}, Last active: {today}"


def get_profile(user_name: str = "") -> str:
    """
    Retrieve a user's profile. If user_name is empty, retrieves the last active user's profile.
    Returns the profile as a formatted summary, or a message if no profile is found.
    """

    profiles = _load_json(PROFILES_FILE, {})

    if not user_name:
        last = _load_json(LAST_USER_FILE, {})
        user_name = last.get("last_user", "")

    if not user_name:
        return "NO_PROFILE_FOUND"

    key = user_name.strip().lower()
    profile = profiles.get(key)

    if not profile:
        return "NO_PROFILE_FOUND"

    goals_str = ", ".join(profile.get("goals", [])) if profile.get("goals") else "None set"
    history_count = len(profile.get("history", []))

    return (
        f"👤 Name: {profile['name']}\n"
        f"💼 Role: {profile.get('role', 'Not set')}\n"
        f"🕐 Work Hours: {profile.get('preferred_work_start', 9)}:00 - {profile.get('preferred_work_end', 17)}:00\n"
        f"🧠 Work Style: {profile.get('work_style', 'deep_work')}\n"
        f"🎯 Goals: {goals_str}\n"
        f"📊 Sessions: {profile.get('total_sessions', 0)}\n"
        f"✅ Avg Completion Rate: {profile.get('avg_completion_rate', 0):.2f}\n"
        f"⏱️ Total Deep Work Hours: {profile.get('total_deep_work_hours', 0)}\n"
        f"📅 Last Active: {profile.get('last_active', 'Unknown')}\n"
        f"📝 Past Summaries: {history_count} entries"
    )


def get_user_history(user_name: str = "") -> str:
    """
    Retrieve a user's past day summaries from their profile.
    If user_name is empty, retrieves history for the last active user.
    """

    profiles = _load_json(PROFILES_FILE, {})

    if not user_name:
        last = _load_json(LAST_USER_FILE, {})
        user_name = last.get("last_user", "")

    if not user_name:
        return "No user found. Please provide a user name."

    key = user_name.strip().lower()
    profile = profiles.get(key)

    if not profile:
        return f"No profile found for '{user_name}'."

    history = profile.get("history", [])

    if not history:
        return f"No past summaries found for {profile['name']}. Start planning your day to build history!"

    formatted = [f"📅 Session {i+1}: {entry}" for i, entry in enumerate(history)]
    return f"History for {profile['name']}:\n" + "\n".join(formatted)


def update_profile_stats(
    user_name: str = "",
    completion_rate: float = 0.0,
    deep_work_hours: int = 0,
    day_summary: str = ""
) -> str:
    """
    Update a user's productivity stats in their profile after a work session.
    Updates the running average completion rate, accumulates deep work hours,
    and appends the day summary to their history.
    If user_name is empty, updates the last active user.
    """

    profiles = _load_json(PROFILES_FILE, {})

    if not user_name:
        last = _load_json(LAST_USER_FILE, {})
        user_name = last.get("last_user", "")

    if not user_name:
        return "No user found. Please provide a user name."

    key = user_name.strip().lower()
    profile = profiles.get(key)

    if not profile:
        return f"No profile found for '{user_name}'."

    # Update running average completion rate
    sessions = profile.get("total_sessions", 1)
    old_avg = profile.get("avg_completion_rate", 0.0)
    profile["avg_completion_rate"] = round(((old_avg * (sessions - 1)) + completion_rate) / sessions, 2)

    # Accumulate deep work hours
    profile["total_deep_work_hours"] = profile.get("total_deep_work_hours", 0) + deep_work_hours

    # Append day summary to per-user history
    if day_summary:
        if "history" not in profile:
            profile["history"] = []
        profile["history"].append(f"[{date.today()}] {day_summary}")

    profile["last_active"] = str(date.today())
    profiles[key] = profile
    _save_json(PROFILES_FILE, profiles)

    return (
        f"Stats updated for {profile['name']}! "
        f"Avg Completion: {profile['avg_completion_rate']:.2f}, "
        f"Total Deep Work: {profile['total_deep_work_hours']}h"
    )
