import os
from datetime import date
import psycopg2
from psycopg2.extras import Json

# =====================================================
# 📂 DB HELPERS
# =====================================================

def get_db_connection():
    return psycopg2.connect(
        host=os.environ.get("ALLOYDB_HOST"),
        user=os.environ.get("ALLOYDB_USER"),
        password=os.environ.get("ALLOYDB_PASSWORD"),
        dbname=os.environ.get("ALLOYDB_DB_NAME")
    )


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
    name_key = user_name.strip().lower()
    today = date.today()
    goals_list = [g.strip() for g in goals.split(",")] if goals else []

    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    INSERT INTO user_profiles (
        name, role, preferred_work_start, preferred_work_end,
        work_style, goals, total_sessions, avg_completion_rate,
        total_deep_work_hours, last_active, history
    ) VALUES (%s, %s, %s, %s, %s, %s, 1, 0.0, 0, %s, %s)
    ON CONFLICT (name) DO UPDATE SET
        role = CASE WHEN EXCLUDED.role <> '' THEN EXCLUDED.role ELSE user_profiles.role END,
        preferred_work_start = EXCLUDED.preferred_work_start,
        preferred_work_end = EXCLUDED.preferred_work_end,
        work_style = EXCLUDED.work_style,
        goals = CASE WHEN EXCLUDED.goals::text <> '[]' THEN EXCLUDED.goals ELSE user_profiles.goals END,
        total_sessions = user_profiles.total_sessions + 1,
        last_active = EXCLUDED.last_active;
    """
    cursor.execute(query, (
        name_key, role, preferred_work_start, preferred_work_end,
        work_style, Json(goals_list), today, Json([])
    ))

    cursor.execute("SELECT total_sessions FROM user_profiles WHERE name = %s", (name_key,))
    total_sessions = cursor.fetchone()[0]

    conn.commit()
    cursor.close()
    conn.close()

    return f"Profile for '{user_name}' saved. Sessions: {total_sessions}, Last active: {today}"


def get_profile(user_name: str = "") -> str:
    """
    Retrieve a user's profile. If user_name is empty, retrieves the last active user's profile.
    Returns the profile as a formatted summary, or a message if no profile is found.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    if not user_name:
        cursor.execute("SELECT name FROM user_profiles ORDER BY last_active DESC LIMIT 1")
        row = cursor.fetchone()
        if not row:
            cursor.close()
            conn.close()
            return "NO_PROFILE_FOUND"
        user_name = row[0]

    key = user_name.strip().lower()
    cursor.execute(
        "SELECT name, role, preferred_work_start, preferred_work_end, work_style, goals, total_sessions, avg_completion_rate, total_deep_work_hours, last_active, history FROM user_profiles WHERE name = %s",
        (key,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        return "NO_PROFILE_FOUND"

    name, role, start, end, style, goals, sessions, avg_rate, deep_hours, last_active, history = row
    goals_str = ", ".join(goals) if goals else "None set"
    history_count = len(history) if history else 0

    return (
        f"👤 Name: {name}\n"
        f"💼 Role: {role or 'Not set'}\n"
        f"🕐 Work Hours: {start}:00 - {end}:00\n"
        f"🧠 Work Style: {style or 'deep_work'}\n"
        f"🎯 Goals: {goals_str}\n"
        f"📊 Sessions: {sessions}\n"
        f"✅ Avg Completion Rate: {avg_rate:.2f}\n"
        f"⏱️ Total Deep Work Hours: {deep_hours}\n"
        f"📅 Last Active: {last_active}\n"
        f" Past Summaries: {history_count} entries"
    )


def get_user_history(user_name: str = "") -> str:
    """
    Retrieve a user's past day summaries from their profile.
    If user_name is empty, retrieves history for the last active user.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    if not user_name:
        cursor.execute("SELECT name FROM user_profiles ORDER BY last_active DESC LIMIT 1")
        row = cursor.fetchone()
        if not row:
            cursor.close()
            conn.close()
            return "No user found. Please provide a user name."
        user_name = row[0]

    key = user_name.strip().lower()
    cursor.execute("SELECT name, history FROM user_profiles WHERE name = %s", (key,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        return f"No profile found for '{user_name}'."

    name, history = row
    if not history:
        return f"No past summaries found for {name}. Start planning your day to build history!"

    formatted = [f"📅 Session {i+1}: {entry}" for i, entry in enumerate(history)]
    return f"History for {name}:\n" + "\n".join(formatted)


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
    conn = get_db_connection()
    cursor = conn.cursor()

    if not user_name:
        cursor.execute("SELECT name FROM user_profiles ORDER BY last_active DESC LIMIT 1")
        row = cursor.fetchone()
        if not row:
            cursor.close()
            conn.close()
            return "No user found. Please provide a user name."
        user_name = row[0]

    key = user_name.strip().lower()
    cursor.execute("SELECT name, total_sessions, avg_completion_rate, total_deep_work_hours, history FROM user_profiles WHERE name = %s", (key,))
    row = cursor.fetchone()
    
    if not row:
        cursor.close()
        conn.close()
        return f"No profile found for '{user_name}'."

    name, sessions, old_avg, old_deep, history = row
    if not history:
        history = []

    sessions = sessions if sessions > 0 else 1
    new_avg = round(((old_avg * (sessions - 1)) + completion_rate) / sessions, 2)
    new_deep = old_deep + deep_work_hours
    
    if day_summary:
        history.append(f"[{date.today()}] {day_summary}")

    cursor.execute("""
        UPDATE user_profiles
        SET avg_completion_rate = %s,
            total_deep_work_hours = %s,
            history = %s,
            last_active = %s
        WHERE name = %s
    """, (new_avg, new_deep, Json(history), date.today(), key))

    conn.commit()
    cursor.close()
    conn.close()

    return (
        f"Stats updated for {name}! "
        f"Avg Completion: {new_avg:.2f}, "
        f"Total Deep Work: {new_deep}h"
    )
