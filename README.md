# Multi-Agent Productivity Tracker

A conversational multi-agent system built using the [Google ADK](https://github.com/google/google-agent-sdk) to help you schedule, optimize, and reflect on your daily tasks. It leverages **Gemini 2.5 Flash** to automatically manage your time and prioritize deep work.

## 🚀 Features

The system relies on a central Orchestrator Agent that routes requests intelligently between specialized sub-agents:

*   **📅 Planner Agent**: Takes your tasks, priorities, and durations, and generates a structured schedule for the day.
*   **⚙️ Optimizer Agent**: Recalculates and replans your schedule dynamically when tasks are completed or drop off.
*   **📊 Reflection Agent**: Computes productivity metrics (like completion rate and deep work hours) and persists this historical data to `memory.json`.

## 🛠️ Architecture

*   **`my_agent/agent.py`**: The core application housing the tool functions and agent definitions.
*   **Tools**:
    *   `schedule_tasks`: Organizes items by priority and schedules them into blocks.
    *   `compute_metrics`: Calculates productivity metrics and deep work time.
    *   `save_day`: Records history safely into local JSON storage.

## 💻 Setup & Installation

1.  **Clone the repository.**
2.  **Activate the Virtual Environment** (for Windows):
    ```powershell
    .\.venv\Scripts\activate
    ```
3.  **Environment Variables**:
    Make sure you have your API keys exported or stored in the `.env` file inside the `my_agent` directory:
    ```env
    GEMINI_API_KEY=your_api_key_here
    ```
4.  **Run the Agent**: You can run the root orchestrator agent (`orchestrator_agent`) using your preferred ADK runner or Python scripts.

## 💬 Example Prompts to Test

You can test the system by sending natural language prompts to the orchestrator agent. Here are some examples to try out for each of the sub-agents:

### 1. Planning (Triggering the Planner Agent)
*   *"I have 3 tasks today: Coding (priority 10, 3 hours, deep_work), Email (priority 5, 1 hour, shallow), and Meetings (priority 8, 2 hours, shallow). Please map out my day."*
*   *"Plan my day. I need to write documentation for 2 hours (priority 7, shallow), fix bugs for 4 hours (priority 9, deep_work), and review PRs for 1 hour (priority 6, shallow)."*
*   *"Create a schedule for me: 3 hours of focused coding, 1 hour taking a design meeting, and 2 hours catching up on team messages."*

### 2. Optimization/Replanning (Triggering the Optimizer Agent)
*   *"I finished my 1 hour of emails early. Adjust my schedule for the rest of the day."*
*   *"The 2-hour meeting got canceled! Can you replan my remaining tasks?"*
*   *"I just completed the bug-fixing task. What should I tackle next?"*

### 3. Reflection & Storage (Triggering the Reflection Agent)
*   *"How was my productivity today? Save my metrics."*
*   *"I completed my coding and email tasks, but didn't get to the meeting. Calculate my deep work hours and completion rate, and record it."*
*   *"Analyze my day's productivity. My tasks were 3 hours of deep work and 2 hours of shallow work. I finished the deep work. Please save this to memory."*

### 4. End-to-End Chat Test
Try pasting these prompts consecutively in the exact same chat session to see the agents work as a cohesive system:
1.  **Start:** *"I have an important feature to build (4h deep work, priority 10), code review (1h shallow, priority 7), and an admin meeting (1h shallow, priority 5). Plan my schedule."*
2.  **Update:** *"I wrapped up the code review and the admin meeting. Please replan the remaining time."*
3.  **Finish:** *"I'm done for the day. Compute my final productivity metrics and store them in memory."*
