# tools/memory_store.py
# Moved from agent.py 

import json
import os
import psycopg2


def save_day(summary: str) -> str:
    """
    Appends today's productivity summary to memory.json.
    Creates the file if it doesn't exist yet.
    """
    WORKORCH_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "workorch")
    file_path = os.path.join(WORKORCH_DIR, "memory.json")

    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            history = json.load(f)
    else:
        history = []

    history.append(summary)

    with open(file_path, "w") as f:
        json.dump(history, f, indent=2)

    return "Saved successfully"


def save_day_to_db(completion_rate: float, deep_work_hours: float, user_name: str = "") -> str:
    """
    Save results to AlloyDB.
    """

    summary = f"Completion Rate: {completion_rate:.2f}, Deep Work Hours: {deep_work_hours}"

    try:
        conn = psycopg2.connect(
            host=os.environ.get("ALLOYDB_HOST"),
            user=os.environ.get("ALLOYDB_USER"),
            password=os.environ.get("ALLOYDB_PASSWORD"),
            dbname=os.environ.get("ALLOYDB_DB_NAME")
        )
        cursor = conn.cursor()

        # Fetch the most recent user if one isn't provided
        if not user_name:
            cursor.execute("SELECT name FROM user_profiles ORDER BY last_active DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                user_name = row[0]
            else:
                user_name = "default_user"

        cursor.execute(
            "INSERT INTO productivity_history (user_name, summary) VALUES (%s, %s)",
            (user_name, summary)
        )

        conn.commit()
        cursor.close()
        conn.close()
        return "Saved successfully to AlloyDB"
    except Exception as e:
        return f"Failed to save to AlloyDB: {str(e)}"