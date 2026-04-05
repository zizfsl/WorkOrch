# tools/overload_detector.py
# Tool 1: detect_overload_and_warn
# Solves Issue #1 — prevents agent from scheduling impossible days

def detect_overload_and_warn(tasks: list, available_hours: float = 7.5) -> dict:
    """
    Checks if total task hours exceed available working hours.
    If overloaded, recommends which tasks to defer (lowest priority first).
    """

    total_hours = sum(task.get("duration_hours", 0) for task in tasks)
    overflow = total_hours - available_hours

    if overflow <= 0:
        return {
            "is_overloaded": False,
            "total_task_hours": total_hours,
            "available_hours": available_hours,
            "message": "Your task load fits within the day. Good to schedule!"
        }

    # Sort by priority — lowest priority gets deferred first
    sorted_tasks = sorted(tasks, key=lambda t: t.get("priority", 5))

    recommended_deferrals = []
    hours_freed = 0.0

    for task in sorted_tasks:
        if hours_freed >= overflow:
            break
        recommended_deferrals.append({
            "task": task.get("name", "Unnamed task"),
            "duration_hours": task.get("duration_hours", 0),
            "priority": task.get("priority", 5),
            "reason": f"Priority {task.get('priority', 5)} — lowest urgency, safe to defer"
        })
        hours_freed += task.get("duration_hours", 0)

    return {
        "is_overloaded": True,
        "total_task_hours": total_hours,
        "available_hours": available_hours,
        "overflow_hours": round(overflow, 1),
        "recommended_deferrals": recommended_deferrals,
        "warning_message": (
            f"You have {round(overflow, 1)} extra hours of work planned. "
            f"Consider deferring {len(recommended_deferrals)} task(s) to stay realistic."
        )
    }