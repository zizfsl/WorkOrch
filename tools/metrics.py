# tools/metrics.py
# Moved from agent.py 

from typing import List


def compute_metrics(
    durations: List[int],
    types: List[str],
    completed_indices: List[int]
) -> str:
    """
    Compute productivity metrics from the day's task data.
    """
    total     = len(durations)
    completed = len(completed_indices)

    deep_work_hours = sum(
        durations[i]
        for i in completed_indices
        if types[i] == "deep_work"
    )

    completion_rate = completed / total if total else 0

    return f"Completion Rate: {completion_rate:.2f}, Deep Work Hours: {deep_work_hours}"