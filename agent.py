# All tool functions moved to tools/ folder
# This file now only contains agent definitions

from google.adk.agents.llm_agent import Agent

# ── Tool imports ───────────────────────────────────────────────
from tools.scheduler         import schedule_tasks
from tools.metrics           import compute_metrics
from tools.memory_store      import save_day
from tools.overload_detector import detect_overload_and_warn
from tools.history_coach     import load_history_and_suggest_improvements

# =====================================================
# 🤖 AGENTS
# =====================================================

# Planner Agent
planner_agent = Agent(
    model="gemini-2.5-flash",
    name="planner_agent",
    description="Creates structured deep work schedules.",
    instruction="""
You are a planning agent.

Goal:
- Plan the user's day using schedule_tasks

Steps:
1. Extract task_names, priorities, durations, types
2. Call schedule_tasks

Rules:
- Always use the tool
- Do not manually create schedule
""",
    tools=[schedule_tasks],
)

# Optimizer Agent
optimizer_agent = Agent(
    model="gemini-2.5-flash",
    name="optimizer_agent",
    description="Replans schedules after updates.",
    instruction="""
You are an optimization agent.

Goal:
- Replan tasks when some are completed

Steps:
1. Remove completed tasks
2. Call schedule_tasks

Rules:
- Always use the tool
""",
    tools=[schedule_tasks],
)

# Reflection Agent
reflection_agent = Agent(
    model="gemini-2.5-flash",
    name="reflection_agent",
    description="Analyzes productivity and stores results.",
    instruction="""
You are a reflection agent.

Goal:
- Analyze productivity
- Save results

Steps:
1. Call compute_metrics
2. Call save_day

Rules:
- Always use tools
""",
    tools=[compute_metrics, save_day],
)

# Overload Detector Agent
overload_agent = Agent(
    model="gemini-2.5-flash",
    name="overload_agent",
    description="Warns the user if their task list exceeds available hours and suggests deferrals.",
    instruction="""
You are an overload detection agent.

Goal:
- Check if the user's tasks exceed their available working hours
- Warn them BEFORE scheduling begins
- Suggest which tasks to defer (lowest priority first)

Steps:
1. Extract tasks as a list of dicts with: name, duration_hours, priority
2. Extract available_hours (default to 7.5 if not mentioned)
3. Call detect_overload_and_warn
4. If is_overloaded is True → present the warning and deferrals clearly
5. If is_overloaded is False → confirm the day is feasible

Rules:
- Always call the tool, never guess yourself
- Be clear and friendly in your warning
- Show exactly which tasks to defer and why
""",
    tools=[detect_overload_and_warn],
)

# History Coach Agent
history_agent = Agent(
    model="gemini-2.5-flash",
    name="history_agent",
    description="Reads past productivity data and gives personalised weekly insights.",
    instruction="""
You are a history and coaching agent.

Goal:
- Read the user's past productivity history from memory.json
- Identify patterns in their completion rate and deep work hours
- Give personalised, actionable suggestions

Steps:
1. Call load_history_and_suggest_improvements
2. Present the results clearly:
   - Average completion rate and deep work hours
   - Best and worst days
   - Patterns detected
   - Specific suggestions
   - Current streak

Rules:
- Always call the tool first, never guess from memory
- Be encouraging, not critical
- Make suggestions specific and actionable
- If status is no_history, tell the user to complete their first day
""",
    tools=[load_history_and_suggest_improvements],
)

# =====================================================
# 🧠 ORCHESTRATOR (ROUTER)
# =====================================================

root_agent = Agent(
    model="gemini-2.5-flash",
    name="orchestrator_agent",
    description="Routes user requests to the correct agent.",
    instruction="""
You are an orchestrator agent.

Your job is to decide which agent to use:

- If user wants to plan → FIRST call overload_agent to check feasibility,
  THEN call planner_agent to create the schedule
- If user has too many tasks / asks if day is realistic → call overload_agent
- If user completed tasks / wants replan → call optimizer_agent
- If user wants analysis or productivity review → call reflection_agent
- If user asks about their history, patterns, weekly review,
  or wants coaching → call history_agent

IMPORTANT:
- Do NOT answer yourself
- Always delegate to the correct agent
- Always run overload_agent BEFORE planner_agent when new tasks are given
""",
    sub_agents=[
        planner_agent,
        optimizer_agent,
        reflection_agent,
        overload_agent,
        history_agent,
    ],
)