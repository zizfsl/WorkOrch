# tools/history_coach.py
# Tool 2: load_history_and_suggest_improvements
# Solves Issue #2 — reads memory.json and gives personalised suggestions
# Closes the loop: save_day (writes) and this tool (reads + learns)

import json
import os
from datetime import datetime

def load_history_and_suggest_improvements(
    memory_file: str = "memory.json",
    days_to_analyze: int = 7
) -> dict:
    """
    Reads past productivity data from memory.json and returns
    personalised suggestions based on the user's actual patterns.

    This transforms the system from a one-shot scheduler into
    a learning productivity coach.
    """

    # Guard: file doesn't exist yet 
    if not os.path.exists(memory_file):
        return {
            "status": "no_history",
            "message": (
                "No productivity history found yet. "
                "Complete your first day and save it using the reflection agent. "
                "Come back tomorrow for your first insights!"
            )
        }

    # Load the file
    with open(memory_file, "r") as f:
        try:
            raw_data = json.load(f)
        except json.JSONDecodeError:
            return {
                "status": "error",
                "message": "memory.json could not be read. It may be corrupted."
            }

    # Handle old plain-string format (e.g. ["Completion Rate: 0.33, Deep Work Hours: 2"])
    # Parse strings into structured dicts so we can do maths on them
    days = []
    for i, entry in enumerate(raw_data[-days_to_analyze:]):
        if isinstance(entry, dict):
            days.append(entry)
        elif isinstance(entry, str):
            # Parse "Completion Rate: 0.33, Deep Work Hours: 2"
            parsed = _parse_legacy_string(entry, index=i)
            if parsed:
                days.append(parsed)

    if not days:
        return {
            "status": "empty",
            "message": "No valid productivity records found in memory.json."
        }

    # Core calculations 
    avg_completion  = sum(d["completion_rate"]  for d in days) / len(days)
    avg_deep_work   = sum(d["deep_work_hours"]  for d in days) / len(days)

    best_day  = max(days, key=lambda d: d["completion_rate"])
    worst_day = min(days, key=lambda d: d["completion_rate"])

    # Pattern detection
    patterns = []

    if avg_deep_work < 2.0:
        patterns.append(
            f"Your average deep work is only {avg_deep_work:.1f}h — "
            "below the recommended 2h minimum. "
            "Try protecting your morning hours."
        )

    if avg_completion < 0.5:
        patterns.append(
            "You're completing fewer than half your planned tasks. "
            "You may be over-estimating what fits in a day."
        )

    if len(days) >= 3:
        last_3_rates = [d["completion_rate"] for d in days[-3:]]
        if last_3_rates[0] > last_3_rates[1] > last_3_rates[2]:
            patterns.append(
                "Your completion rate has dropped 3 days in a row. "
                "Consider planning lighter days or taking a break."
            )

    if avg_completion >= 0.8:
        patterns.append(
            f"Excellent! You're completing {avg_completion*100:.0f}% of your tasks on average. "
            "Great consistency!"
        )

    if not patterns:
        patterns.append("Not enough variation in data yet to detect strong patterns. Keep logging!")

    # Personalised suggestions 
    suggestions = []

    if avg_completion < 0.5:
        suggestions.append("Plan a maximum of 3 tasks per day until completion rate improves.")
    elif avg_completion < 0.75:
        suggestions.append("Add 30-minute buffer slots between tasks to handle overruns.")

    if avg_deep_work < 2.0:
        suggestions.append("Block 9–11 AM as a strict no-meeting deep work window.")
        suggestions.append("Put your most important deep work task FIRST before checking email.")

    if avg_completion >= 0.8 and avg_deep_work >= 3.0:
        suggestions.append("You're performing well — consider adding a stretch goal each day.")

    if not suggestions:
        suggestions.append("Keep your current routine — it's working well!")

    # Streak: days in a row above 70% completion
    streak = 0
    for day in reversed(days):
        if day["completion_rate"] >= 0.7:
            streak += 1
        else:
            break

    # Build final output 
    return {
        "status": "success",
        "days_analyzed": len(days),
        "average_completion_rate": round(avg_completion, 2),
        "average_deep_work_hours": round(avg_deep_work, 2),
        "best_day": {
            "date": best_day.get("date", "Day " + str(days.index(best_day) + 1)),
            "completion_rate": best_day["completion_rate"]
        },
        "worst_day": {
            "date": worst_day.get("date", "Day " + str(days.index(worst_day) + 1)),
            "completion_rate": worst_day["completion_rate"]
        },
        "patterns_detected": patterns,
        "suggestions": suggestions,
        "current_streak": streak,
        "streak_message": (
            f" {streak} day streak!" if streak >= 2
            else "Complete today above 70% to start a streak!"
        )
    }


# Helper: parse old plain-string format 
def _parse_legacy_string(entry: str, index: int) -> dict:
    """
    Converts old string format:
    "Completion Rate: 0.33, Deep Work Hours: 2"
    into a proper dict the tool can process.
    """
    try:
        parts = entry.split(",")
        completion_rate = float(parts[0].split(":")[1].strip())
        deep_work_hours = float(parts[1].split(":")[1].strip())
        return {
            "date": f"Day {index + 1}",   # no real date in old format
            "completion_rate": completion_rate,
            "deep_work_hours": deep_work_hours
        }
    except Exception:
        return None