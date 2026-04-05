# tools/scheduler.py
# Moved from agent.py 

from typing import List


def schedule_tasks(
    task_names: List[str],
    priorities: List[int],
    durations: List[int],
    types: List[str]
) -> List[str]:
    """
    Create a structured schedule by sorting tasks by priority
    and assigning sequential time blocks starting at 9:00 AM.
    """
    tasks = list(zip(task_names, priorities, durations, types))
    tasks.sort(key=lambda x: x[1], reverse=True)

    current_hour = 9
    schedule = []

    for name, priority, duration, ttype in tasks:
        block = f"{name} ({ttype}) → {current_hour}:00 to {current_hour + duration}:00"
        schedule.append(block)
        current_hour += duration

    return schedule