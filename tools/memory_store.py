# tools/memory_store.py
# Moved from agent.py 

import json
import os


def save_day(summary: str) -> str:
    """
    Appends today's productivity summary to memory.json.
    Creates the file if it doesn't exist yet.
    """
    file_path = "memory.json"

    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            history = json.load(f)
    else:
        history = []

    history.append(summary)

    with open(file_path, "w") as f:
        json.dump(history, f, indent=2)

    return "Saved successfully"