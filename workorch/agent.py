import sys
import os

_parent_dir = os.path.dirname(os.path.dirname(__file__))
if _parent_dir not in sys.path:
    sys.path.append(_parent_dir)

from google.adk.agents.llm_agent import Agent

try:
    from google_tools import get_upcoming_events, get_unread_emails
except ModuleNotFoundError:
    from workorch.google_tools import get_upcoming_events, get_unread_emails

# ── Tool imports ───────────────────────────────────────────────
from tools.scheduler         import schedule_tasks
from tools.metrics           import compute_metrics
from tools.memory_store      import save_day_to_db, save_day
from tools.overload_detector import detect_overload_and_warn
from tools.history_coach     import load_history_and_suggest_improvements
from tools.profile_tools     import create_or_update_profile, get_profile, get_user_history, update_profile_stats
from tools.auth_tools        import login_with_google


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
    description="Analyzes productivity, stores results in AlloyDB, and updates user profile stats.",
    instruction="""
You are a reflection agent.

Goal:
- Analyze productivity
- Save results to AlloyDB
- Update the user's profile stats

Steps:
1. Call compute_metrics to get completion rate and deep work hours
2. Call save_day_to_db with completion_rate and deep_work_hours to persist the summary to AlloyDB
3. Call update_profile_stats to update the user's profile with the new metrics
   - Extract the completion_rate (as a float like 0.75) and deep_work_hours (as an integer) from the compute_metrics result
   - Pass the full summary as day_summary
   - Leave user_name empty to auto-use the last active user

Rules:
- Always use all three tools in order
""",
    tools=[compute_metrics, save_day_to_db, update_profile_stats],
)

# Profile Agent
profile_agent = Agent(
    model="gemini-2.5-flash",
    name="profile_agent",
    description="Manages user profiles — creates, updates, retrieves profiles.",
    instruction="""
You are a profile management agent for WorkOrch.

Goal:
- Help users create or update their profile
- Log users in securely using Google Auth if requested
- Retrieve profile information when asked

Available tools:
- login_with_google: Trigger a browser popup to sign the user in with Google and automatically create their profile.
- create_or_update_profile: Create a new profile manually or update an existing one
- get_profile: Retrieve a user's profile (leave user_name empty to get the last active user)
- update_profile_stats: Update productivity stats after a session

Behavior:
- If user wants to set up their profile, suggest they can log in via Google for a frictionless experience, or do it manually.
- If user wants to log in with Google, exclusively use login_with_google.
- If user does it manually, ask for: name, role, preferred work hours, work style, and goals.
- If user asks "who am I" or "my profile", call get_profile with empty user_name.

Rules:
- Always use the tools, never fabricate profile data
- Be conversational and friendly when collecting info
""",
    tools=[login_with_google, create_or_update_profile, get_profile, update_profile_stats],
)

# Greeting Agent
greeting_agent = Agent(
    model="gemini-2.5-flash",
    name="greeting_agent",
    description="Greets users and provides a personalized overview of available capabilities.",
    instruction="""
You are a friendly greeting agent for WorkOrch — a smart work orchestration system.

Goal:
- Check if there's a returning user by calling get_profile with an empty user_name
- Greet the user warmly and personally

Behavior based on get_profile result:

IF the result contains "NO_PROFILE_FOUND":
- Welcome them as a new user
- Say: "Welcome to WorkOrch! I'd love to get to know you. You can set up your profile by telling me your name and role."
- Then explain the capabilities listed below

IF the result contains a real profile:
- Greet them BY NAME (e.g., "Welcome back, Alice! 👋")
- Mention their last session stats (completion rate, deep work hours) if available
- Encourage them to continue where they left off

Always explain these capabilities:
1. 📅 **Plan Your Day** — Create structured deep work schedules
2. 🔄 **Optimize & Replan** — Update your schedule on the fly
3. 📊 **Reflect & Analyze** — Get productivity metrics and save summaries
4. 👤 **Your Profile** — View and update your personal profile and history

Rules:
- ALWAYS call get_profile first (with empty user_name) before greeting
- Keep it friendly and concise
- Encourage the user to try a feature
""",
    tools=[get_profile],
)

# Assistant Agent
assistant_agent = Agent(
    model="gemini-2.5-flash",
    name="assistant_agent",
    description="Manages the user's schedule (Calendar) and communications (Gmail).",
    instruction="""
You are an assistant for WorkOrch.

Goal:
- Read the user's upcoming Google Calendar events.
- Read the user's unread emails in Gmail.

Available tools:
- get_upcoming_events: Fetches the user's upcoming calendar events.
- get_unread_emails: Fetches the user's latest unread emails.

Behavior:
- When asked about schedule, meetings, or calendar, use get_upcoming_events.
- When asked about emails, unread messages, or inbox, use get_unread_emails.
""",
    tools=[get_upcoming_events, get_unread_emails],
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
1. Call get_user_history to examine the raw history if needed
2. Call load_history_and_suggest_improvements
3. Present the results clearly:
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
    tools=[load_history_and_suggest_improvements, get_user_history],
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

- If user says hello, hi, hey, greetings, good morning, or any greeting → call greeting_agent
- If user wants to plan → FIRST call overload_agent to check feasibility, THEN call planner_agent to create the schedule
- If user has too many tasks / asks if day is realistic → call overload_agent
- If user completed tasks / wants to replan → call optimizer_agent
- If user wants productivity analysis or reflection → call reflection_agent
- If user wants to set up, view, or update their profile → call profile_agent
- If user asks "who am I" or "my profile" → call profile_agent
- If user asks about their calendar, events, schedule, emails, or inbox → call assistant_agent
- If user asks about their history, past sessions, patterns, weekly review, or wants coaching → call history_agent

IMPORTANT:
- Do NOT answer yourself
- Always delegate to the correct agent
- Always run overload_agent BEFORE planner_agent when new tasks are given
""",
    sub_agents=[
        greeting_agent, 
        profile_agent, 
        overload_agent, 
        planner_agent, 
        optimizer_agent, 
        reflection_agent, 
        assistant_agent, 
        history_agent
    ],
)