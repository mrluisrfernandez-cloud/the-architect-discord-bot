import os
import json
import asyncio
from datetime import datetime, timezone, date
from zoneinfo import ZoneInfo

import discord
from discord.ext import tasks
from openai import OpenAI

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not DISCORD_TOKEN:
    raise RuntimeError("Missing DISCORD_TOKEN environment variable.")
if not OPENAI_API_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY environment variable.")

ai_client = OpenAI(api_key=OPENAI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

MEMORY_FILE = "memory.json"
TRADES_FILE = "trades.json"
GUILD_STATE_FILE = "guild_state.json"

DR_TZ = ZoneInfo("America/Santo_Domingo")

CHANNELS = {
    "mission_brief": "mission-brief",
    "daily_checkin": "daily-checkin",
    "weekly_review": "weekly-review",
    "performance_report": "performance-report",
    "system_analysis": "system-analysis",
}

DEPARTMENT_CHANNELS = {
    "system_core": "mission-brief",
    "fitness_lab": "fitness-log",
    "nutrition_lab": "nutrition-lab",
    "trading_desk": "trading-desk",
    "knowledge_vault": "reading-log",
    "builder_lab": "builder-lab",
    "cosmic_reflection": "cosmic-reflection",
    "architect_analysis": "system-analysis",
}

MORNING_BRIEF_HOUR = 8
MORNING_BRIEF_MINUTE = 0

ARCHITECT_CORE_IDENTITY = """
You are Architect.

Architect is the AI operating system built for Luis.

Your purpose is to help Luis build a disciplined, high-performance life through
clear thinking, smart execution, data tracking, strategic reflection, and steady improvement.

You support Luis across multiple departments:
1. Trading Desk
2. Fitness Lab
3. Nutrition Lab
4. Knowledge Vault
5. Builder Lab
6. Cosmic Reflection
7. Architect Analysis

You are not just a chatbot.
You are a coach, strategist, second brain, and execution partner.

Your style:
- Clear
- Practical
- Strategic
- Motivating
- Honest
- Disciplined
- Built for action, not fluff

Always help Luis move toward:
- clarity
- discipline
- execution
- consistency
- intelligent self-correction
- long-term growth
"""

TASK_DEFINITIONS = {
    "wake": {
        "id": "wake",
        "label": "Wake Up",
        "department": "system_core",
        "default_time": "05:00",
        "priority": 100,
        "required": True,
        "time_sensitive": True,
        "can_skip_if_late": False,
        "follow_up_prompt": "You still have not checked in for wake-up. Start the day and reset the tone now.",
    },
    "movement": {
        "id": "movement",
        "label": "Movement / Yoga",
        "department": "fitness_lab",
        "default_time": "06:00",
        "priority": 90,
        "required": True,
        "time_sensitive": True,
        "can_skip_if_late": True,
        "follow_up_prompt": "Movement is still missing. Get at least a short mobility or yoga block done.",
    },
    "breakfast": {
        "id": "breakfast",
        "label": "Breakfast / Fuel",
        "department": "nutrition_lab",
        "default_time": "07:00",
        "priority": 88,
        "required": True,
        "time_sensitive": True,
        "can_skip_if_late": False,
        "follow_up_prompt": "Breakfast is still missing. Fuel up and log your meal.",
    },
    "trading_brief": {
        "id": "trading_brief",
        "label": "Trading Brief",
        "department": "trading_desk",
        "default_time": "08:00",
        "priority": 92,
        "required": True,
        "time_sensitive": True,
        "can_skip_if_late": False,
        "follow_up_prompt": "Trading briefing is still missing. Align bias and prepare now.",
    },
    "premarket_check": {
        "id": "premarket_check",
        "label": "Premarket Check",
        "department": "trading_desk",
        "default_time": "09:15",
        "priority": 95,
        "required": True,
        "time_sensitive": True,
        "can_skip_if_late": False,
        "follow_up_prompt": "Premarket is still missing. Get aligned before execution.",
    },
    "lunch": {
        "id": "lunch",
        "label": "Lunch",
        "department": "nutrition_lab",
        "default_time": "12:30",
        "priority": 70,
        "required": True,
        "time_sensitive": False,
        "can_skip_if_late": False,
        "follow_up_prompt": "Lunch is still missing. Eat clean and keep energy stable.",
    },
    "trade_talk_prompt": {
        "id": "trade_talk_prompt",
        "label": "Trade Talk Scheduling",
        "department": "trading_desk",
        "default_time": "16:30",
        "priority": 80,
        "required": True,
        "time_sensitive": False,
        "can_skip_if_late": False,
        "follow_up_prompt": "You still have not set today’s trade talk. Lock in a review time.",
    },
    "recap": {
        "id": "recap",
        "label": "Market Recap",
        "department": "trading_desk",
        "default_time": "20:00",
        "priority": 75,
        "required": True,
        "time_sensitive": False,
        "can_skip_if_late": False,
        "follow_up_prompt": "Recap is still missing. Review the market before the day closes.",
    },
    "reflection": {
        "id": "reflection",
        "label": "Reflection",
        "department": "cosmic_reflection",
        "default_time": "22:00",
        "priority": 60,
        "required": True,
        "time_sensitive": False,
        "can_skip_if_late": True,
        "follow_up_prompt": "Reflection is still missing. Close the day with intention.",
    },
}

SCHEDULE = {task["default_time"]: task_id for task_id, task in TASK_DEFINITIONS.items()}

last_triggered = {}
operating_day_state = {
    "date": "",
    "tasks": {},
    "meta": {
        "day_started_at": "",
        "last_updated": "",
    }
}

WEEKLY_WORKOUT_LIBRARY = {
    "monday": {
        "title": "Full Body Strength + Chest/Core",
        "focus": "strength, chest, lower body, pull, core",
        "gym": [
            "Barbell or DB Bench Press - 4x6-8",
            "Incline Press or Push-Ups - 3x12",
            "Goblet Squats or Front Squats - 4x10",
            "Pull-Ups or TRX Rows - 3x10",
            "Plank to Push-Up + Weighted Sit-Ups - 3x15",
        ],
        "home": [
            "Weighted or Tempo Push-Ups - 4x8-12",
            "Incline Push-Ups or Feet Elevated Push-Ups - 3x12",
            "Goblet Squats or Bodyweight Tempo Squats - 4x10-15",
            "TRX Rows or Doorframe Rows - 3x10-12",
            "Plank to Push-Up + Sit-Ups - 3x15",
        ],
    },
    "tuesday": {
        "title": "Core + HIIT Conditioning",
        "focus": "conditioning, abs, mobility",
        "gym": [
            "Jump Rope HIIT - 5 rounds x 45 sec",
            "Hollow Holds or V-Ups - 3x30 sec",
            "Hanging Leg Raises - 3x15",
            "Flutter Kicks - 4x20 sec",
            "Pigeon Stretch + Hip Mobility - 10 min",
        ],
        "home": [
            "Jump Rope HIIT or Fast Step-Ups - 5 rounds x 45 sec",
            "Hollow Holds or V-Ups - 3x30 sec",
            "Lying Leg Raises - 3x15",
            "Flutter Kicks - 4x20 sec",
            "Pigeon Stretch + Hip Mobility - 10 min",
        ],
    },
    "wednesday": {
        "title": "Lower Body + Posterior Chain",
        "focus": "glutes, hamstrings, lower body, core stability",
        "gym": [
            "Romanian Deadlifts or Trap Bar - 4x10",
            "Walking Lunges - 3x20 steps",
            "Hip Thrusts or Bridges - 4x8",
            "Hamstring Curls or Nordic Curls - 3x12",
            "Bird Dogs or Weighted Plank - 3x1 min",
        ],
        "home": [
            "DB RDL or Backpack RDL - 4x10-12",
            "Walking Lunges or Reverse Lunges - 3x20 steps",
            "Glute Bridges or Single-Leg Bridges - 4x10",
            "Nordic Negatives or Banded Ham Curls - 3x12",
            "Bird Dogs or Plank - 3x1 min",
        ],
    },
    "thursday": {
        "title": "Upper Body + Arms & Core",
        "focus": "shoulders, arms, trunk",
        "gym": [
            "Overhead Press or Arnold Press - 4x10",
            "EZ Bar Curl + DB Hammer Curl - 3x12 each",
            "Triceps Rope or Skull Crushers - 3x15",
            "Incline Sit-Ups or Cable Crunch - 3x20",
            "Side Plank Reach - 3x30 sec/side",
        ],
        "home": [
            "Pike Push-Ups or DB Overhead Press - 4x10",
            "DB Curl + Hammer Curl - 3x12 each",
            "Bench Dips or Overhead Triceps Extension - 3x15",
            "Sit-Ups or Crunch Variations - 3x20",
            "Side Plank Reach - 3x30 sec/side",
        ],
    },
    "friday": {
        "title": "Calisthenics + Athletic Conditioning",
        "focus": "bodyweight performance, explosive conditioning",
        "gym": [
            "Push-Ups - 4x20 (mix: wide/diamond/feet up)",
            "Box Jumps or Sled Push - 3x10",
            "Pull-Ups or Jumping Pull-Ups - 3x10",
            "Kettlebell Swings or Sled Drag - 4x30 sec",
            "Core Circuit: V-Ups + Russian Twists - 3 rounds",
        ],
        "home": [
            "Push-Ups - 4x20 (mix: wide/diamond/feet up)",
            "Jump Squats or Broad Jumps - 3x10",
            "Pull-Ups, Band Pulldowns, or Inverted Rows - 3x10",
            "Kettlebell Swings or Fast Bodyweight Circuits - 4x30 sec",
            "Core Circuit: V-Ups + Russian Twists - 3 rounds",
        ],
    },
    "saturday": {
        "title": "Recovery + Mobility",
        "focus": "recovery, mobility, tissue quality",
        "gym": [
            "Yoga Flow - 20-30 min",
            "Foam Roll: Glutes, Lats, Hamstrings - 10 min",
            "Breathing Core Work (Deadbugs, TVA Activation)",
            "Stretch: Hip Flexor, Thoracic Spine - 3x30 sec each",
        ],
        "home": [
            "Yoga Flow - 20-30 min",
            "Foam Roll or Mobility Ball Work - 10 min",
            "Breathing Core Work (Deadbugs, TVA Activation)",
            "Stretch: Hip Flexor, Thoracic Spine - 3x30 sec each",
        ],
    },
    "sunday": {
        "title": "Light Cardio + Optional Abs",
        "focus": "recovery cardio, light core",
        "gym": [
            "Swimming Laps 10-15 min OR Bike Ride 30-45 min OR Incline Walk 30 min",
            "Optional Core: Leg Raises, Flutter Kicks, Planks - 3 sets each",
            "Stretch + Chill Mode",
        ],
        "home": [
            "Bike Ride 30-45 min OR Incline Walk 30 min OR Outdoor Walk",
            "Optional Core: Leg Raises, Flutter Kicks, Planks - 3 sets each",
            "Stretch + Chill Mode",
        ],
    },
}

def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


def dr_now():
    return datetime.now(DR_TZ)


def today_dr():
    return dr_now().date().isoformat()


def load_json_file(path: str, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json_file(path: str, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_memory():
    return load_json_file(MEMORY_FILE, {})


def save_memory(data):
    save_json_file(MEMORY_FILE, data)


def get_trades():
    return load_json_file(TRADES_FILE, {})


def save_trades(data):
    save_json_file(TRADES_FILE, data)


def get_guild_state():
    return load_json_file(GUILD_STATE_FILE, {})


def save_guild_state(data):
    save_json_file(GUILD_STATE_FILE, data)


def safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def safe_int(value, default=0):
    try:
        return int(float(value))
    except Exception:
        return default


def get_user_key(message: discord.Message) -> str:
    return str(message.author.id)


def ensure_guild_state(guild_id: str):
    guild_state = get_guild_state()
    current = guild_state.get(guild_id, {
        "primary_user_id": "",
        "last_morning_brief_date": "",
    })
    current.setdefault("primary_user_id", "")
    current.setdefault("last_morning_brief_date", "")
    guild_state[guild_id] = current
    save_guild_state(guild_state)
    return guild_state, current


def register_guild_user(guild_id: str, user_id: str):
    guild_state, current = ensure_guild_state(guild_id)
    current["primary_user_id"] = user_id
    guild_state[guild_id] = current
    save_guild_state(guild_state)


def set_last_morning_brief_date(guild_id: str, date_text: str):
    guild_state, current = ensure_guild_state(guild_id)
    current["last_morning_brief_date"] = date_text
    guild_state[guild_id] = current
    save_guild_state(guild_state)


def get_or_create_user_memory(user_id: str):
    memory = get_memory()
    user = memory.get(user_id, {
        "weights": [],
        "goals": [],
        "notes": [],
        "ideas": [],
        "habits": [],
        "checkins": [],
        "pnl_logs": [],
        "wins": [],
        "mistakes": [],
        "sleep_logs": [],
        "mood_logs": [],
        "focus_logs": [],
        "workouts": [],
        "activity_logs": [],
        "body_baseline": {},
        "body_goal": {},
        "body_change": {},
        "activity_baseline": {},
        "profile": {},
        "transformation_goal": {},
        "fitness_profile": {},
        "adjustment_engine": {
            "last_analysis": {},
            "last_updated": "",
        },
        "user_workout_engine": {
            "workout_phase": "",
            "phase_duration_weeks": 0,
            "equipment": [],
        },
        "context": {
            "week_mode": "",
            "week_focus": [],
            "training_mode": "",
            "nutrition_mode": "",
            "daily_goals": [],
            "watchlist": [],
        },
    })

    for key in [
        "weights", "goals", "notes", "ideas", "habits", "checkins",
        "pnl_logs", "wins", "mistakes", "sleep_logs", "mood_logs",
        "focus_logs", "workouts", "activity_logs"
    ]:
        user.setdefault(key, [])

    for key in [
        "body_baseline", "body_goal", "body_change", "activity_baseline",
        "profile", "transformation_goal", "fitness_profile"
    ]:
        user.setdefault(key, {})

    user.setdefault("adjustment_engine", {"last_analysis": {}, "last_updated": ""})
    user.setdefault("user_workout_engine", {"workout_phase": "", "phase_duration_weeks": 0, "equipment": []})
    user.setdefault("context", {
        "week_mode": "",
        "week_focus": [],
        "training_mode": "",
        "nutrition_mode": "",
        "daily_goals": [],
        "watchlist": [],
    })

    uwe = user["user_workout_engine"]
    uwe.setdefault("workout_phase", "")
    uwe.setdefault("phase_duration_weeks", 0)
    uwe.setdefault("equipment", [])

    ctx = user["context"]
    ctx.setdefault("week_mode", "")
    ctx.setdefault("week_focus", [])
    ctx.setdefault("training_mode", "")
    ctx.setdefault("nutrition_mode", "")
    ctx.setdefault("daily_goals", [])
    ctx.setdefault("watchlist", [])

    memory[user_id] = user
    save_memory(memory)
    return memory, user


def append_memory_item(user_id: str, key: str, payload: dict):
    memory, user = get_or_create_user_memory(user_id)
    user[key].append(payload)
    memory[user_id] = user
    save_memory(memory)


def find_text_channel_by_name(guild: discord.Guild, channel_name: str):
    for channel in guild.text_channels:
        if channel.name == channel_name:
            return channel
    return None


def get_system_channel(guild: discord.Guild, key: str):
    channel_name = CHANNELS.get(key, "")
    if not channel_name:
        return None
    return find_text_channel_by_name(guild, channel_name)


def get_department_channel(guild: discord.Guild, department: str):
    channel_name = DEPARTMENT_CHANNELS.get(department)
    if not channel_name:
        return None
    for channel in guild.text_channels:
        if channel.name == channel_name:
            return channel
    return None


async def send_to_department(guild: discord.Guild | None, department: str, message: str):
    if guild is None:
        return
    channel = get_department_channel(guild, department)
    if channel:
        await channel.send(message)


async def route_department_report(guild: discord.Guild | None, department: str, message: str):
    await send_to_department(guild, department, message)
    if department != "architect_analysis":
        await send_to_department(guild, "architect_analysis", message)


def extract_prompt(content: str) -> str:
    return content.replace("!architect", "", 1).strip()


def split_command_and_body(prompt: str):
    if not prompt:
        return "", ""
    parts = prompt.split(" ", 1)
    return parts[0].strip().lower(), parts[1].strip() if len(parts) > 1 else ""


def get_department_prompt(channel_name: str) -> str:
    name = (channel_name or "").lower()

    if "trading" in name:
        return "You are inside Trading Desk. Be sharp, practical, structured, and focused on execution, discipline, and risk."
    if "fitness" in name:
        return "You are inside Fitness Lab. Be practical, motivating, and realistic about workouts, recovery, and consistency."
    if "nutrition" in name:
        return "You are inside Nutrition Lab. Keep advice simple, useful, and sustainable."
    if "reading" in name or "knowledge" in name:
        return "You are inside Knowledge Vault. Help organize notes, ideas, and useful insight."
    if "builder" in name:
        return "You are inside Builder Lab. Focus on execution, systems, and next steps."
    if "cosmic" in name or "reflection" in name:
        return "You are inside Cosmic Reflection. Be reflective, calm, grounded, and practical."
    if "analysis" in name or "performance" in name:
        return "You are inside Architect Analysis. Focus on patterns, accountability, discipline, and lesson extraction."

    return "You are Architect. Be strategic, practical, clear, and helpful."


def get_channel_mode(channel_name: str) -> str:
    return ARCHITECT_CORE_IDENTITY + "\n\n" + get_department_prompt(channel_name)


def build_task_instance(task_id: str, task_def: dict):
    return {
        "id": task_id,
        "label": task_def["label"],
        "department": task_def["department"],
        "default_time": task_def["default_time"],
        "scheduled_time": task_def["default_time"],
        "priority": task_def["priority"],
        "required": task_def["required"],
        "time_sensitive": task_def["time_sensitive"],
        "can_skip_if_late": task_def["can_skip_if_late"],
        "follow_up_prompt": task_def["follow_up_prompt"],
        "status": "pending",
        "completed": False,
        "completed_at": "",
        "missed_at": "",
        "skipped_at": "",
        "rescheduled_to": "",
        "follow_up_sent": False,
        "follow_up_sent_at": "",
        "late": False,
        "last_prompt_sent_at": "",
        "notes": "",
    }


def reset_operating_day_state():
    global operating_day_state

    tasks = {}
    for task_id, task_def in TASK_DEFINITIONS.items():
        tasks[task_id] = build_task_instance(task_id, task_def)

    operating_day_state = {
        "date": today_dr(),
        "tasks": tasks,
        "meta": {
            "day_started_at": utc_now_iso(),
            "last_updated": utc_now_iso(),
        }
    }


def ensure_operating_day_state():
    global operating_day_state

    if operating_day_state["date"] != today_dr() or not operating_day_state["tasks"]:
        reset_operating_day_state()

    operating_day_state["meta"]["last_updated"] = utc_now_iso()
    return operating_day_state


def get_task_state(task_id: str):
    state = ensure_operating_day_state()
    return state["tasks"].get(task_id)


def set_task_status(task_id: str, status: str, notes: str = ""):
    state = ensure_operating_day_state()
    task = state["tasks"].get(task_id)
    if not task:
        return None

    now_iso = utc_now_iso()
    task["status"] = status
    task["notes"] = notes
    state["meta"]["last_updated"] = now_iso

    if status == "completed":
        task["completed"] = True
        task["completed_at"] = now_iso
    elif status == "missed":
        task["completed"] = False
        task["missed_at"] = now_iso
    elif status == "skipped":
        task["completed"] = False
        task["skipped_at"] = now_iso

    return task


def mark_task_prompt_sent(task_id: str):
    task = get_task_state(task_id)
    if task:
        task["last_prompt_sent_at"] = utc_now_iso()


def mark_task_follow_up_sent(task_id: str):
    task = get_task_state(task_id)
    if task:
        task["follow_up_sent"] = True
        task["follow_up_sent_at"] = utc_now_iso()

def reschedule_task(task_id: str, new_time: str, notes: str = ""):
    task = get_task_state(task_id)
    if not task:
        return None

    task["status"] = "rescheduled"
    task["rescheduled_to"] = new_time
    task["scheduled_time"] = new_time
    task["notes"] = notes
    task["late"] = True
    operating_day_state["meta"]["last_updated"] = utc_now_iso()
    return task


def get_pending_tasks():
    state = ensure_operating_day_state()
    return [task for task in state["tasks"].values() if task["status"] in ("pending", "rescheduled") and not task["completed"]]


def get_completed_tasks():
    state = ensure_operating_day_state()
    return [task for task in state["tasks"].values() if task["completed"]]


def get_missed_tasks():
    state = ensure_operating_day_state()
    return [task for task in state["tasks"].values() if task["status"] == "missed"]


def get_skipped_tasks():
    state = ensure_operating_day_state()
    return [task for task in state["tasks"].values() if task["status"] == "skipped"]


def get_rescheduled_tasks():
    state = ensure_operating_day_state()
    return [task for task in state["tasks"].values() if task["status"] == "rescheduled"]


def get_task_sort_key(task: dict):
    return (-task["priority"], task["scheduled_time"])


def get_next_priority_task():
    pending = get_pending_tasks()
    if not pending:
        return None
    return sorted(pending, key=get_task_sort_key)[0]


def get_overdue_tasks(now_hhmm: str | None = None):
    state = ensure_operating_day_state()
    now_hhmm = now_hhmm or dr_now().strftime("%H:%M")

    overdue = []
    for task in state["tasks"].values():
        if task["completed"]:
            continue
        if task["status"] in ("skipped", "missed"):
            continue
        if task["scheduled_time"] < now_hhmm:
            overdue.append(task)

    return sorted(overdue, key=get_task_sort_key)


def get_daily_state_counts():
    state = ensure_operating_day_state()
    tasks = list(state["tasks"].values())

    return {
        "total": len(tasks),
        "completed": len([t for t in tasks if t["completed"]]),
        "pending": len([t for t in tasks if t["status"] in ("pending", "rescheduled") and not t["completed"]]),
        "missed": len([t for t in tasks if t["status"] == "missed"]),
        "skipped": len([t for t in tasks if t["status"] == "skipped"]),
        "rescheduled": len([t for t in tasks if t["status"] == "rescheduled"]),
    }


def build_day_status_report():
    ensure_operating_day_state()

    completed = get_completed_tasks()
    pending = get_pending_tasks()
    missed = get_missed_tasks()
    skipped = get_skipped_tasks()
    rescheduled = get_rescheduled_tasks()

    completed_text = "\n".join([f"- {t['label']}" for t in completed]) if completed else "- none yet"
    pending_text = "\n".join([f"- {t['label']} ({t['scheduled_time']})" for t in sorted(pending, key=get_task_sort_key)]) if pending else "- nothing pending"
    missed_text = "\n".join([f"- {t['label']}" for t in missed]) if missed else "- none"
    skipped_text = "\n".join([f"- {t['label']}" for t in skipped]) if skipped else "- none"
    rescheduled_text = "\n".join([f"- {t['label']} -> {t['scheduled_time']}" for t in rescheduled]) if rescheduled else "- none"

    counts = get_daily_state_counts()

    return (
        "ARCHITECT DAY STATUS\n\n"
        f"Date: {operating_day_state['date']}\n"
        f"Completed: {counts['completed']}/{counts['total']}\n"
        f"Pending: {counts['pending']}\n"
        f"Missed: {counts['missed']}\n"
        f"Skipped: {counts['skipped']}\n"
        f"Rescheduled: {counts['rescheduled']}\n\n"
        "Completed:\n"
        f"{completed_text}\n\n"
        "Pending:\n"
        f"{pending_text}\n\n"
        "Missed:\n"
        f"{missed_text}\n\n"
        "Skipped:\n"
        f"{skipped_text}\n\n"
        "Rescheduled:\n"
        f"{rescheduled_text}"
    )


def build_follow_up_report():
    ensure_operating_day_state()

    overdue = get_overdue_tasks()
    if overdue:
        next_task = overdue[0]
        return (
            "ARCHITECT FOLLOW-UP\n\n"
            f"Most important overdue item:\n- {next_task['label']}\n\n"
            "Prompt:\n"
            f"{next_task['follow_up_prompt']}"
        )

    next_task = get_next_priority_task()
    if not next_task:
        return (
            "ARCHITECT FOLLOW-UP\n\n"
            "✅ Everything on your tracked list is complete today.\n"
            "Good work. Stay sharp and close strong."
        )

    return (
        "ARCHITECT FOLLOW-UP\n\n"
        f"Next priority item:\n- {next_task['label']} ({next_task['scheduled_time']})\n\n"
        "Prompt:\n"
        f"{next_task['follow_up_prompt']}"
    )


def has_meaningful_brief_data(user_id: str) -> bool:
    memory = get_memory()
    user = memory.get(user_id, {})
    context = user.get("context", {})
    workout_engine = user.get("user_workout_engine", {})

    has_context = any([
        context.get("week_mode"),
        context.get("week_focus"),
        context.get("training_mode"),
        context.get("nutrition_mode"),
        context.get("daily_goals"),
        context.get("watchlist"),
    ])

    has_logs = any([
        user.get("sleep_logs"),
        user.get("mood_logs"),
        user.get("focus_logs"),
        user.get("activity_logs"),
        user.get("workouts"),
    ])

    has_profile = any([
        user.get("body_baseline"),
        user.get("body_goal"),
        user.get("fitness_profile"),
        user.get("transformation_goal"),
        user.get("activity_baseline"),
        workout_engine.get("workout_phase"),
        workout_engine.get("equipment"),
    ])

    return has_context or has_logs or has_profile


def has_gym_access(user_id: str) -> bool:
    memory = get_memory()
    user = memory.get(user_id, {})
    fp = user.get("fitness_profile", {})
    resources = str(fp.get("available_resources", "")).lower()
    equipment = [x.lower() for x in user.get("user_workout_engine", {}).get("equipment", [])]

    return (
        "gym" in resources or
        "full_gym" in resources or
        "barbell" in equipment or
        "machine" in equipment or
        "cable" in equipment
    )


def build_equipment_modifier_text(user_id: str) -> str:
    equipment = get_memory().get(user_id, {}).get("user_workout_engine", {}).get("equipment", [])
    return ", ".join(equipment) if equipment else "No extra equipment updated yet."


def analyze_adjustment_engine(user_id: str):
    memory = get_memory()
    user = memory.get(user_id, {})

    workouts = user.get("workouts", [])
    activity = user.get("activity_logs", [])

    training_days = len(workouts[-7:])
    activity_days = len(activity[-7:])

    recommendation = "maintain current plan"
    if training_days < 3:
        recommendation = "increase training frequency"
    if activity_days < 3:
        recommendation = "add cardio or daily activity"
    if training_days >= 5 and activity_days >= 5:
        recommendation = "training load high — ensure recovery"

    memory, user = get_or_create_user_memory(user_id)
    user["adjustment_engine"]["last_analysis"] = {
        "recommendation": recommendation,
        "training_days": training_days,
        "activity_days": activity_days,
    }
    user["adjustment_engine"]["last_updated"] = utc_now_iso()
    memory[user_id] = user
    save_memory(memory)

    return user["adjustment_engine"]["last_analysis"]


def build_mission_text() -> str:
    return (
        "Architect Mission:\n"
        "Architect exists to help Luis build a disciplined, high-performance life.\n\n"
        "Its purpose is to serve as:\n"
        "- a coach\n"
        "- a strategist\n"
        "- a second brain\n"
        "- a system builder\n\n"
        "Architect helps across trading, fitness, nutrition, knowledge, execution, mindset, and reflection.\n"
        "It is designed to turn data, ideas, habits, and behavior into clear next steps and steady improvement."
    )


def compute_transformation_status(user_id: str):
    memory = get_memory()
    user = memory.get(user_id, {})
    transformation = user.get("transformation_goal", {})
    body_baseline = user.get("body_baseline", {})
    body_goal = user.get("body_goal", {})
    fitness_profile = user.get("fitness_profile", {})

    if not transformation:
        return None

    current_weight = safe_float(transformation.get("current_weight_lb") or body_baseline.get("weight_lb"), 0)
    target_low = safe_float(transformation.get("target_weight_low_lb") or body_goal.get("target_weight_low_lb"), 0)
    target_high = safe_float(transformation.get("target_weight_high_lb") or body_goal.get("target_weight_high_lb"), 0)
    deadline_text = transformation.get("deadline_date", "")
    goal_type = transformation.get("goal_type", "Not set")

    try:
        deadline = date.fromisoformat(deadline_text)
    except Exception:
        return {"valid": False, "error": "Invalid deadline date. Use YYYY-MM-DD."}

    today = dr_now().date()
    days_left = (deadline - today).days
    weeks_left = days_left / 7 if days_left is not None else 0

    if target_low <= 0 or target_high <= 0 or current_weight <= 0:
        return {"valid": False, "error": "Transformation goal is missing valid weight data."}

    midpoint_target = (target_low + target_high) / 2
    pounds_to_goal = current_weight - midpoint_target
    pounds_per_week = pounds_to_goal / weeks_left if weeks_left > 0 else 0

    training_days = safe_int(fitness_profile.get("training_days_available", 0), 0)
    current_mode = fitness_profile.get("current_training_mode", "Not set")
    current_phase = fitness_profile.get("current_phase", "Not set")
    resources = fitness_profile.get("available_resources", "Not set")

    if days_left < 0:
        pace_status = "Deadline passed"
    elif pounds_per_week > 2.0:
        pace_status = "Aggressive"
    elif pounds_per_week > 1.25:
        pace_status = "Demanding"
    elif pounds_per_week > 0:
        pace_status = "Reasonable"
    elif pounds_per_week == 0:
        pace_status = "At target"
    else:
        pace_status = "Below target range / reassess"

    notes = []
    if days_left < 0:
        notes.append("The deadline has already passed. Set a new transformation date and reassess the plan.")
    elif pounds_per_week > 2.0:
        notes.append("Your required pace is aggressive. Tight nutrition, training consistency, and recovery matter more.")
    elif pounds_per_week > 1.25:
        notes.append("Your pace is demanding but realistic if compliance stays high.")
    elif pounds_per_week > 0:
        notes.append("Your pace is reasonable. Focus on consistency instead of overcorrecting.")
    else:
        notes.append("You may already be near target. Shift focus toward body quality and muscle retention.")

    if training_days == 0:
        notes.append("Training days are not set yet. Set the fitness profile so Architect can coach better.")

    return {
        "valid": True,
        "current_weight": current_weight,
        "target_low": target_low,
        "target_high": target_high,
        "midpoint_target": midpoint_target,
        "deadline_text": deadline_text,
        "days_left": days_left,
        "weeks_left": weeks_left,
        "pounds_to_goal": pounds_to_goal,
        "pounds_per_week": pounds_per_week,
        "goal_type": goal_type,
        "pace_status": pace_status,
        "current_mode": current_mode,
        "current_phase": current_phase,
        "training_days": training_days,
        "resources": resources,
        "recommendation_lines": notes,
    }

def build_body_baseline_report(user_id: str) -> str:
    baseline = get_memory().get(user_id, {}).get("body_baseline", {})
    if not baseline:
        return "No body baseline saved yet. Use !architect set-body-baseline ..."
    return (
        "Architect Body Baseline:\n"
        f"- Weight: {baseline.get('weight_lb', 0):.1f} lb\n"
        f"- Body Fat: {baseline.get('body_fat_percent', 0):.1f}%\n"
        f"- BMI: {baseline.get('bmi', 0):.1f}\n"
        f"- Skeletal Muscle: {baseline.get('skeletal_muscle_percent', 0):.1f}%\n"
        f"- Muscle Mass: {baseline.get('muscle_mass_lb', 0):.1f} lb\n"
        f"- BMR: {baseline.get('bmr_kcal', 0):.0f} kcal\n"
        f"- Body Type: {baseline.get('body_type', 'Not set')}\n"
        f"- Metabolic Age: {baseline.get('metabolic_age', 0)}"
    )


def build_body_goal_report(user_id: str) -> str:
    goal = get_memory().get(user_id, {}).get("body_goal", {})
    if not goal:
        return "No body goal saved yet. Use !architect set-body-goal 190 200 11"
    return (
        "Architect Body Goal:\n"
        f"- Target weight range: {goal.get('target_weight_low_lb', 0):.1f} to {goal.get('target_weight_high_lb', 0):.1f} lb\n"
        f"- Target body fat: {goal.get('target_body_fat_percent', 0):.1f}%"
    )


def build_body_change_report(user_id: str) -> str:
    change = get_memory().get(user_id, {}).get("body_change", {})
    if not change:
        return "No body change snapshot saved yet. Use !architect set-body-change 32.6 4.8 7.5"
    return (
        "Architect Body Change Snapshot:\n"
        f"- Weight change: +{change.get('weight_change_lb', 0):.1f} lb\n"
        f"- BMI change: +{change.get('bmi_change', 0):.1f}\n"
        f"- Body fat change: +{change.get('body_fat_change_percent', 0):.1f}%"
    )


def build_activity_baseline_report(user_id: str) -> str:
    baseline = get_memory().get(user_id, {}).get("activity_baseline", {})
    if not baseline:
        return "No activity baseline saved yet. Use !architect set-activity-baseline 900 60 12 10000 5"
    return (
        "Architect Activity Baseline:\n"
        f"- Active calories daily: {baseline.get('active_calories_daily', 0):.0f}\n"
        f"- Exercise minutes daily: {baseline.get('exercise_minutes_daily', 0):.0f}\n"
        f"- Stand hours daily: {baseline.get('stand_hours_daily', 0):.0f}\n"
        f"- Steps daily: {baseline.get('steps_daily', 0)}\n"
        f"- Workouts per week: {baseline.get('workouts_per_week', 0)}"
    )


def build_profile_identity_report(user_id: str) -> str:
    profile = get_memory().get(user_id, {}).get("profile", {})
    if not profile:
        return "No profile identity saved yet. Use !architect set-profile 12/24/1986 6:00AM"
    return (
        "Architect Profile:\n"
        f"- Birth date: {profile.get('birth_date', 'Not set')}\n"
        f"- Birth time: {profile.get('birth_time', 'Not set')}"
    )


def build_transformation_status_report(user_id: str) -> str:
    status = compute_transformation_status(user_id)
    if not status:
        return "No transformation goal saved yet. Use !architect set-transformation-goal ..."
    if not status.get("valid", False):
        return f"Transformation status error: {status.get('error', 'Unknown error')}"

    recommendations = "\n".join([f"- {x}" for x in status.get("recommendation_lines", [])])

    return (
        "Architect Transformation Status:\n"
        f"- Goal type: {status.get('goal_type', 'Not set')}\n"
        f"- Current weight: {status.get('current_weight', 0):.1f} lb\n"
        f"- Target range: {status.get('target_low', 0):.1f} to {status.get('target_high', 0):.1f} lb\n"
        f"- Target midpoint: {status.get('midpoint_target', 0):.1f} lb\n"
        f"- Deadline: {status.get('deadline_text', 'Not set')}\n"
        f"- Days left: {status.get('days_left', 0)}\n"
        f"- Weeks left: {status.get('weeks_left', 0):.1f}\n"
        f"- Pounds to midpoint target: {status.get('pounds_to_goal', 0):.1f} lb\n"
        f"- Required pace: {status.get('pounds_per_week', 0):.2f} lb/week\n"
        f"- Pace status: {status.get('pace_status', 'Not set')}\n"
        f"- Current training mode: {status.get('current_mode', 'Not set')}\n"
        f"- Current phase: {status.get('current_phase', 'Not set')}\n"
        f"- Training days available: {status.get('training_days', 0)}\n"
        f"- Resources: {status.get('resources', 'Not set')}\n\n"
        f"Recommendations:\n{recommendations}"
    )


def build_fitness_profile_report(user_id: str) -> str:
    fp = get_memory().get(user_id, {}).get("fitness_profile", {})
    if not fp:
        return "No fitness profile saved yet. Use !architect set-fitness-profile ..."
    return (
        "Architect Fitness Profile:\n"
        f"- Current training mode: {fp.get('current_training_mode', 'Not set')}\n"
        f"- Current phase: {fp.get('current_phase', 'Not set')}\n"
        f"- Training days available: {fp.get('training_days_available', 0)}\n"
        f"- Available resources: {fp.get('available_resources', 'Not set')}\n"
        f"- Current challenge: {fp.get('current_challenge', 'Not set')}\n"
        f"- Movement base: {fp.get('movement_base', 'Not set')}\n"
        f"- Physique target: {fp.get('physique_target', 'Not set')}\n"
        f"- Starting point notes: {fp.get('starting_point_notes', 'Not set')}"
    )


def build_fitness_adjustment_report(user_id: str) -> str:
    user = get_memory().get(user_id, {})
    fitness_profile = user.get("fitness_profile", {})
    transformation_goal = user.get("transformation_goal", {})
    status = compute_transformation_status(user_id)

    if not fitness_profile:
        return "No fitness profile saved yet. Use !architect set-fitness-profile ... first."
    if not transformation_goal:
        return "No transformation goal saved yet. Use !architect set-transformation-goal ... first."
    if not status or not status.get("valid", False):
        return f"Fitness adjustment unavailable: {status.get('error', 'Missing valid transformation data') if status else 'Missing transformation data'}"

    return (
        "Architect Fitness Adjustment:\n"
        f"- Current mode: {fitness_profile.get('current_training_mode', 'Not set')}\n"
        f"- Current phase: {fitness_profile.get('current_phase', 'Not set')}\n"
        f"- Training days available: {fitness_profile.get('training_days_available', 0)}\n"
        f"- Resources: {fitness_profile.get('available_resources', 'Not set')}\n"
        f"- Pace status: {status.get('pace_status', 'Not set')}\n"
        f"- Required weekly pace: {status.get('pounds_per_week', 0):.2f} lb/week"
    )


def build_weekly_workout_plan(user_id: str) -> str:
    phase_data = get_memory().get(user_id, {}).get("user_workout_engine", {})
    workout_phase = phase_data.get("workout_phase", "not set")
    phase_duration_weeks = phase_data.get("phase_duration_weeks", 0)
    gym_mode = has_gym_access(user_id)
    mode_label = "gym/hybrid" if gym_mode else "home/bodyweight"

    lines = [
        "Architect Weekly Workout Plan:",
        f"- Workout phase: {workout_phase}",
        f"- Planned phase duration: {phase_duration_weeks} week(s)",
        f"- Build mode used today: {mode_label}",
        f"- Extra equipment: {build_equipment_modifier_text(user_id)}",
        "",
    ]

    for day_name in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
        block = WEEKLY_WORKOUT_LIBRARY[day_name]
        exercises = block["gym"] if gym_mode else block["home"]
        lines.append(f"{day_name.title()} - {block['title']}")
        lines.extend([f"- {x}" for x in exercises])
        lines.append("")

    return "\n".join(lines).strip()


def build_today_workout(user_id: str) -> str:
    today_name = dr_now().strftime("%A").lower()
    block = WEEKLY_WORKOUT_LIBRARY.get(today_name)
    if not block:
        return "I couldn't determine today's workout."

    phase_data = get_memory().get(user_id, {}).get("user_workout_engine", {})
    workout_phase = phase_data.get("workout_phase", "not set")
    phase_duration_weeks = phase_data.get("phase_duration_weeks", 0)
    gym_mode = has_gym_access(user_id)
    exercises = block["gym"] if gym_mode else block["home"]

    lines = [
        "Architect Today Workout:",
        f"- Day: {today_name.title()}",
        f"- Session: {block['title']}",
        f"- Focus: {block['focus']}",
        f"- Workout phase: {workout_phase}",
        f"- Phase duration: {phase_duration_weeks} week(s)",
        "",
        "Today's exercises:",
    ]
    lines.extend([f"- {x}" for x in exercises])
    return "\n".join(lines)


def build_pushup_plan(user_id: str, total_target: int = 300, max_set: int = 25) -> str:
    total_target = total_target if total_target > 0 else 300
    max_set = max_set if max_set > 0 else 25

    return (
        "Architect Push-Up Plan:\n"
        f"- Daily target: {total_target}\n"
        f"- Current max set: {max_set}\n\n"
        "Recommended options:\n"
        "- Option 1: 15 sets of 20 = 300 total\n"
        "- Option 2: 12 sets of 25 = 300 total\n"
        "- Option 3: EMOM style — 10 to 15 reps every hour across the day until target is complete"
    )


def build_activity_report(user_id: str) -> str:
    user = get_memory().get(user_id, {})
    logs = user.get("activity_logs", [])
    if not logs:
        return "No activity data saved yet. Use !architect log-activity."

    today_logs = [x for x in logs if x.get("date") == today_dr()]
    total_logs = len(logs)

    return (
        "Architect Activity Report:\n"
        f"- Activity sessions logged: {total_logs}\n"
        f"- Today's active calories: {sum(x.get('active_calories', 0) for x in today_logs):.0f}\n"
        f"- Today's exercise minutes: {sum(x.get('exercise_minutes', 0) for x in today_logs):.0f}\n"
        f"- Today's steps: {sum(x.get('steps', 0) for x in today_logs)}"
    )


def build_knowledge_report(user_id: str):
    user = get_memory().get(user_id, {})
    notes = user.get("notes", [])
    ideas = user.get("ideas", [])
    report = (
        "Knowledge System Report:\n"
        f"- Notes saved: {len(notes)}\n"
        f"- Ideas saved: {len(ideas)}\n"
    )
    if notes:
        report += f"\nLatest note:\n- {notes[-1]['text']}\n"
    if ideas:
        report += f"\nLatest idea:\n- {ideas[-1]['text']}\n"
    return report

def build_pnl_report(user_id: str):
    pnl_logs = get_memory().get(user_id, {}).get("pnl_logs", [])
    if not pnl_logs:
        return "No PnL logs saved yet. Use !architect log-pnl 250"

    total = sum(x["value"] for x in pnl_logs)
    avg_day = total / len(pnl_logs)
    green = sum(1 for x in pnl_logs if x["value"] > 0)
    red = sum(1 for x in pnl_logs if x["value"] < 0)
    flat = sum(1 for x in pnl_logs if x["value"] == 0)

    best_day = max(pnl_logs, key=lambda x: x["value"])
    worst_day = min(pnl_logs, key=lambda x: x["value"])
    today_total = sum(x["value"] for x in pnl_logs if x["date"] == today_dr())

    return (
        "PnL Report:\n"
        f"- Days logged: {len(pnl_logs)}\n"
        f"- Today: {today_total:.2f}\n"
        f"- Total PnL: {total:.2f}\n"
        f"- Average day: {avg_day:.2f}\n"
        f"- Green days: {green}\n"
        f"- Red days: {red}\n"
        f"- Flat days: {flat}\n"
        f"- Best day: {best_day['value']:.2f} ({best_day['date']})\n"
        f"- Worst day: {worst_day['value']:.2f} ({worst_day['date']})"
    )


def build_daily_report(user_id: str):
    memory = get_memory().get(user_id, {})
    trades = get_trades().get(user_id, [])
    today = today_dr()

    sleep_today = [x for x in memory.get("sleep_logs", []) if x["date"] == today]
    mood_today = [x for x in memory.get("mood_logs", []) if x["date"] == today]
    focus_today = [x for x in memory.get("focus_logs", []) if x["date"] == today]
    habits_today = [x for x in memory.get("habits", []) if x["timestamp"][:10] == today]
    workouts_today = [x for x in memory.get("workouts", []) if x["date"] == today]
    notes_today = [x for x in memory.get("notes", []) if x["timestamp"][:10] == today]
    ideas_today = [x for x in memory.get("ideas", []) if x["timestamp"][:10] == today]
    pnl_today = [x for x in memory.get("pnl_logs", []) if x["date"] == today]
    wins_today = [x for x in memory.get("wins", []) if x["date"] == today]
    mistakes_today = [x for x in memory.get("mistakes", []) if x["date"] == today]
    trades_today = [x for x in trades if x["timestamp"][:10] == today]

    return (
        "Architect Daily System Report:\n"
        f"- Date: {today}\n"
        f"- Sleep: {sleep_today[-1]['hours']} hrs\n" if sleep_today else "Architect Daily System Report:\n"
        f"- Date: {today}\n- Sleep: No sleep logged\n"
    ) + (
        f"- Mood: {mood_today[-1]['score']}\n" if mood_today else "- Mood: No mood logged\n"
    ) + (
        f"- Focus: {focus_today[-1]['score']}\n" if focus_today else "- Focus: No focus logged\n"
    ) + (
        f"- Habits logged today: {len(habits_today)}\n"
        f"- Workouts logged today: {len(workouts_today)}\n"
        f"- Notes saved today: {len(notes_today)}\n"
        f"- Ideas saved today: {len(ideas_today)}\n"
        f"- Wins logged today: {len(wins_today)}\n"
        f"- Mistakes logged today: {len(mistakes_today)}\n"
        f"- Trades logged today: {len(trades_today)}\n"
        f"- PnL today: {sum(x['value'] for x in pnl_today):.2f}"
    )


def build_week_plan(user_id: str):
    user = get_memory().get(user_id, {})
    context = user.get("context", {})
    focus_text = ", ".join(context.get("week_focus", [])) if context.get("week_focus") else "Not set"
    watchlist_text = ", ".join(context.get("watchlist", [])) if context.get("watchlist") else "Not set"
    latest_goal = context.get("daily_goals", [])[-1]["text"] if context.get("daily_goals") else "No daily goal set"

    return (
        "Architect Week Plan:\n"
        f"- Week mode: {context.get('week_mode', 'Not set')}\n"
        f"- Week focus: {focus_text}\n"
        f"- Training mode: {context.get('training_mode', 'Not set')}\n"
        f"- Nutrition mode: {context.get('nutrition_mode', 'Not set')}\n"
        f"- Watchlist: {watchlist_text}\n"
        f"- Latest daily goal: {latest_goal}"
    )


def build_morning_brief(user_id: str):
    user = get_memory().get(user_id, {})
    context = user.get("context", {})
    body_baseline = user.get("body_baseline", {})
    body_goal = user.get("body_goal", {})
    fp = user.get("fitness_profile", {})
    tg = user.get("transformation_goal", {})
    today_pretty = dr_now().strftime("%A, %B %d, %Y")

    lines = ["Architect Morning Brief:", f"- Date: {today_pretty}"]

    if body_baseline:
        lines.append(f"- Body baseline: {body_baseline.get('weight_lb', 0):.1f} lb | BF {body_baseline.get('body_fat_percent', 0):.1f}% | BMI {body_baseline.get('bmi', 0):.1f}")
    if body_goal:
        lines.append(f"- Body goal: {body_goal.get('target_weight_low_lb', 0):.1f} to {body_goal.get('target_weight_high_lb', 0):.1f} lb | BF {body_goal.get('target_body_fat_percent', 0):.1f}%")
    if fp:
        lines.append(f"- Current phase: {fp.get('current_phase', 'Not set')}")
        lines.append(f"- Fitness mode: {fp.get('current_training_mode', 'Not set')}")
    if tg:
        lines.append(f"- Transformation deadline: {tg.get('deadline_date', 'Not set')}")

    today_name = dr_now().strftime("%A").lower()
    today_block = WEEKLY_WORKOUT_LIBRARY.get(today_name)
    if today_block:
        lines.append(f"- Today's workout: {today_block['title']}")

    lines.extend([
        f"- Week mode: {context.get('week_mode', 'Not set')}",
        f"- Week focus: {', '.join(context.get('week_focus', [])) if context.get('week_focus') else 'Not set'}",
        f"- Training mode: {context.get('training_mode', 'Not set')}",
        f"- Nutrition mode: {context.get('nutrition_mode', 'Not set')}",
        f"- Daily goal: {context.get('daily_goals', [])[-1]['text'] if context.get('daily_goals') else 'No daily goal set'}",
        f"- Watchlist: {', '.join(context.get('watchlist', [])) if context.get('watchlist') else 'Not set'}",
        "- Recommendation: Stay disciplined, execute the plan, and log your data.",
    ])

    return "\n".join(lines)


def build_profile_text(user_id: str) -> str:
    user = get_memory().get(user_id, {})
    user_trades = get_trades().get(user_id, [])
    lines = ["Profile snapshot:"]

    profile = user.get("profile", {})
    if profile:
        lines.append(f"- Birth date: {profile.get('birth_date', 'Not set')}")
        lines.append(f"- Birth time: {profile.get('birth_time', 'Not set')}")

    if user.get("body_baseline"):
        bb = user["body_baseline"]
        lines.append(f"- Body baseline: {bb.get('weight_lb', 0):.1f} lb | BF {bb.get('body_fat_percent', 0):.1f}% | BMI {bb.get('bmi', 0):.1f}")

    lines.append(f"- Total trades logged: {len(user_trades)}")
    return "\n".join(lines)


def build_weekly_report(user_id: str) -> str:
    user = get_memory().get(user_id, {})
    trades = get_trades().get(user_id, [])

    return (
        "Weekly performance snapshot:\n"
        f"- Weight logs: {len(user.get('weights', []))}\n"
        f"- Goals logged: {len(user.get('goals', []))}\n"
        f"- Habits logged: {len(user.get('habits', []))}\n"
        f"- Check-ins logged: {len(user.get('checkins', []))}\n"
        f"- Sleep logs: {len(user.get('sleep_logs', []))}\n"
        f"- Mood logs: {len(user.get('mood_logs', []))}\n"
        f"- Focus logs: {len(user.get('focus_logs', []))}\n"
        f"- Workout logs: {len(user.get('workouts', []))}\n"
        f"- Activity logs: {len(user.get('activity_logs', []))}\n"
        f"- PnL logs: {len(user.get('pnl_logs', []))}\n"
        f"- Wins logged: {len(user.get('wins', []))}\n"
        f"- Mistakes logged: {len(user.get('mistakes', []))}\n"
        f"- Trades logged: {len(trades)}"
    )


def log_trade_raw(user_id: str, raw_trade: str):
    trades = get_trades()
    user_trades = trades.get(user_id, [])
    user_trades.append({"type": "raw_review", "raw": raw_trade, "timestamp": utc_now_iso()})
    trades[user_id] = user_trades
    save_trades(trades)


def log_trade_structured(user_id: str, instrument: str, entry: float, stop: float, target: float, setup: str, exit_price: float):
    risk_pts = abs(entry - stop)
    target_pts = abs(target - entry)
    result_pts = exit_price - entry
    planned_r = target_pts / risk_pts if risk_pts else 0
    realized_r = result_pts / risk_pts if risk_pts else 0

    trades = get_trades()
    user_trades = trades.get(user_id, [])
    user_trades.append({
        "type": "structured",
        "instrument": instrument,
        "entry": entry,
        "stop": stop,
        "target": target,
        "setup": setup,
        "exit_price": exit_price,
        "risk_pts": risk_pts,
        "target_pts": target_pts,
        "result_pts": result_pts,
        "planned_r": planned_r,
        "realized_r": realized_r,
        "timestamp": utc_now_iso(),
    })
    trades[user_id] = user_trades
    save_trades(trades)

    return {
        "risk_pts": risk_pts,
        "target_pts": target_pts,
        "result_pts": result_pts,
        "planned_r": planned_r,
        "realized_r": realized_r,
    }


def get_structured_trades(user_id: str):
    return [t for t in get_trades().get(user_id, []) if t.get("type") == "structured"]


def build_trade_stats(user_id: str) -> str:
    structured = get_structured_trades(user_id)
    if not structured:
        return "No structured trades logged yet. Use !architect trade-log MNQ 18450 18420 18520 breakout_retest 18515"

    total = len(structured)
    wins = sum(1 for t in structured if t.get("result_pts", 0) > 0)
    losses = sum(1 for t in structured if t.get("result_pts", 0) < 0)
    breakeven = sum(1 for t in structured if t.get("result_pts", 0) == 0)

    avg_result = sum(t.get("result_pts", 0) for t in structured) / total
    avg_realized_r = sum(t.get("realized_r", 0) for t in structured) / total
    avg_planned_r = sum(t.get("planned_r", 0) for t in structured) / total

    return (
        "Trading stats:\n"
        f"- Total structured trades: {total}\n"
        f"- Wins: {wins}\n"
        f"- Losses: {losses}\n"
        f"- Breakeven: {breakeven}\n"
        f"- Win rate: {(wins / total) * 100:.1f}%\n"
        f"- Average result (pts): {avg_result:.2f}\n"
        f"- Average realized R: {avg_realized_r:.2f}\n"
        f"- Average planned R: {avg_planned_r:.2f}"
    )


def build_dashboard(user_id: str) -> str:
    structured = get_structured_trades(user_id)
    if not structured:
        return "No structured trades logged yet. Use !architect trade-log MNQ 18450 18420 18520 breakout_retest 18515"

    total = len(structured)
    wins = sum(1 for t in structured if t.get("result_pts", 0) > 0)
    total_points = sum(t.get("result_pts", 0) for t in structured)
    total_realized_r = sum(t.get("realized_r", 0) for t in structured)

    return (
        "Architect Trading Dashboard:\n"
        f"- Total structured trades: {total}\n"
        f"- Wins: {wins}\n"
        f"- Win rate: {(wins / total) * 100:.1f}%\n"
        f"- Total points: {total_points:.2f}\n"
        f"- Total realized R: {total_realized_r:.2f}"
    )


def build_coach_report(user_id: str) -> str:
    structured = get_structured_trades(user_id)
    if not structured:
        return "No structured trades logged yet. Use !architect trade-log ..."
    total = len(structured)
    avg_planned_r = sum(t.get("planned_r", 0) for t in structured) / total
    avg_realized_r = sum(t.get("realized_r", 0) for t in structured) / total
    capture_ratio = avg_realized_r / avg_planned_r if avg_planned_r else 0

    return (
        "Architect Coach Report:\n"
        f"- Total structured trades reviewed: {total}\n"
        f"- Average planned R: {avg_planned_r:.2f}\n"
        f"- Average realized R: {avg_realized_r:.2f}\n"
        f"- Reward capture ratio: {capture_ratio:.2f}\n\n"
        "Next focus:\n"
        "- Keep logging every trade.\n"
        "- Compare best setup vs all others after more sample size.\n"
        "- Watch whether realized R keeps lagging planned R."
    )

async def send_automatic_morning_brief(guild: discord.Guild):
    guild_id = str(guild.id)
    guild_state = get_guild_state()
    state = guild_state.get(guild_id, {})
    primary_user_id = state.get("primary_user_id", "").strip()
    last_sent_date = state.get("last_morning_brief_date", "").strip()
    today = today_dr()

    if not primary_user_id or last_sent_date == today or not has_meaningful_brief_data(primary_user_id):
        return

    channel = get_system_channel(guild, "mission_brief")
    if channel is None:
        return

    await channel.send(build_morning_brief(primary_user_id))
    state["last_morning_brief_date"] = today
    guild_state[guild_id] = state
    save_guild_state(guild_state)


async def post_morning_brief_to_system_channel(guild: discord.Guild, user_id: str):
    channel = get_system_channel(guild, "mission_brief")
    if channel is None:
        return False, "I couldn’t find #mission-brief in this server."

    register_guild_user(str(guild.id), user_id)

    if not has_meaningful_brief_data(user_id):
        return False, "I found #mission-brief, but your Architect profile is still blank, so I stopped the post."

    await channel.send(build_morning_brief(user_id))
    set_last_morning_brief_date(str(guild.id), today_dr())
    return True, f"Morning brief posted in #{channel.name}."


async def run_ai_reply(message: discord.Message, prompt: str):
    system_prompt = get_channel_mode(message.channel.name)

    async with message.channel.typing():
        response = ai_client.responses.create(
            model="gpt-5-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        )

    reply = response.output_text or "I understood you, but I didn’t get usable text back."
    chunks = [reply[i:i + 1900] for i in range(0, len(reply), 1900)]
    for chunk in chunks:
        await message.channel.send(chunk)


async def trigger_event(bot_client, event: str):
    ensure_operating_day_state()
    task = get_task_state(event)
    if task is None:
        return

    for guild in bot_client.guilds:
        if event == "wake":
            message = "🌅 Wake up. New day. Lock in."
        elif event == "movement":
            message = "🧘 Time for movement / yoga. Activate your body."
        elif event == "breakfast":
            message = "🍳 Breakfast time. Fuel your system. Log your meal."
        elif event == "trading_brief":
            message = "📊 Trading briefing. Align your bias and prepare."
        elif event == "premarket_check":
            message = "⏰ Premarket check. Be ready for execution."
        elif event == "lunch":
            message = "🥗 Lunch time. Eat clean. Stay sharp."
        elif event == "trade_talk_prompt":
            message = "🧠 What time do you want to review your trades today?"
        elif event == "recap":
            message = "📉 Market recap. What happened today?"
        elif event == "reflection":
            message = "🌙 Reflection time. What did you learn today?"
        else:
            message = f"Task triggered: {task['label']}"

        await send_to_department(guild, task["department"], message)

    mark_task_prompt_sent(event)


async def auto_follow_up_check(bot_client):
    ensure_operating_day_state()
    overdue_tasks = get_overdue_tasks(dr_now().strftime("%H:%M"))

    if not overdue_tasks:
        return

    for task in overdue_tasks:
        if task["follow_up_sent"]:
            continue

        for guild in bot_client.guilds:
            message = (
                "⚠️ ARCHITECT FOLLOW-UP\n\n"
                f"Overdue:\n- {task['label']}\n\n"
                "Prompt:\n"
                f"{task['follow_up_prompt']}"
            )
            await send_to_department(guild, task["department"], message)

        mark_task_follow_up_sent(task["id"])


async def scheduler_loop(bot_client):
    await bot_client.wait_until_ready()

    while not bot_client.is_closed():
        ensure_operating_day_state()
        now = dr_now().strftime("%H:%M")

        for time_str, event in SCHEDULE.items():
            if now == time_str:
                today_key = f"{time_str}-{today_dr()}"
                if last_triggered.get(today_key):
                    continue
                last_triggered[today_key] = True
                await trigger_event(bot_client, event)

        await auto_follow_up_check(bot_client)
        await asyncio.sleep(60)


@tasks.loop(minutes=1)
async def morning_brief_loop():
    now = dr_now()
    if now.hour != MORNING_BRIEF_HOUR or now.minute != MORNING_BRIEF_MINUTE:
        return

    for guild in bot.guilds:
        try:
            await send_automatic_morning_brief(guild)
        except Exception as e:
            print(f"Morning brief error in guild {guild.id}: {e}")


@morning_brief_loop.before_loop
async def before_morning_brief_loop():
    await bot.wait_until_ready()


@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")

    if not morning_brief_loop.is_running():
        morning_brief_loop.start()

    if not hasattr(bot, "_architect_scheduler_started"):
        bot._architect_scheduler_started = True
        bot.loop.create_task(scheduler_loop(bot))


@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return

    content = message.content.strip()
    if not content.startswith("!architect"):
        return

    prompt = extract_prompt(content)
    if not prompt:
        await message.channel.send("Give me something after !architect.")
        return

    command, body = split_command_and_body(prompt)
    user_id = get_user_key(message)
    ensure_operating_day_state()

    if message.guild is not None:
        register_guild_user(str(message.guild.id), user_id)

    try:
        if command == "mission":
            await message.channel.send(build_mission_text())
            return

        if command == "post-morning-brief":
            if message.guild is None:
                await message.channel.send("This command must be used inside your Discord server.")
                return
            ok, result_text = await post_morning_brief_to_system_channel(message.guild, user_id)
            await message.channel.send(result_text)
            return

        if command == "day-status":
            await message.channel.send(build_day_status_report())
            return

        if command == "follow-up-check":
            await message.channel.send(build_follow_up_report())
            return

        if command == "save-book":
            if not body:
                await message.channel.send("Usage: !architect save-book Atomic_Habits James_Clear")
                return
            entry = f"📘 BOOK LOGGED\n{body}"
            append_memory_item(user_id, "notes", {"text": entry, "timestamp": utc_now_iso()})
            await message.channel.send(entry)
            if message.guild:
                await route_department_report(message.guild, "knowledge_vault", entry)
            return

        if command == "save-lesson":
            if not body:
                await message.channel.send("Usage: !architect save-lesson Identity_based_habits_are_stronger_than_motivation")
                return
            entry = f"🧠 LESSON SAVED\n{body}"
            append_memory_item(user_id, "notes", {"text": entry, "timestamp": utc_now_iso()})
            await message.channel.send(entry)
            if message.guild:
                await route_department_report(message.guild, "knowledge_vault", entry)
            return

        if command == "save-note":
            if not body:
                await message.channel.send("Usage: !architect save-note your note")
                return
            append_memory_item(user_id, "notes", {"text": body, "timestamp": utc_now_iso()})
            await message.channel.send(f"Note saved: {body}")
            if message.guild:
                await route_department_report(message.guild, "knowledge_vault", f"📝 NOTE SAVED\n{body}")
            return

        if command == "save-idea":
            if not body:
                await message.channel.send("Usage: !architect save-idea your idea")
                return
            append_memory_item(user_id, "ideas", {"text": body, "timestamp": utc_now_iso()})
            await message.channel.send(f"Idea saved: {body}")
            return

        if command == "notes":
            notes = get_memory().get(user_id, {}).get("notes", [])
            await message.channel.send("No notes saved yet." if not notes else "Saved notes:\n" + "\n".join([f"- {n['text']}" for n in notes[-10:]]))
            return

        if command == "ideas":
            ideas = get_memory().get(user_id, {}).get("ideas", [])
            await message.channel.send("No ideas saved yet." if not ideas else "Saved ideas:\n" + "\n".join([f"- {i['text']}" for i in ideas[-10:]]))
            return

        if command == "knowledge-report":
            await message.channel.send(build_knowledge_report(user_id))
            return

        if command == "set-body-baseline":
            parts = body.split()
            if len(parts) < 15:
                await message.channel.send("Usage: !architect set-body-baseline 221.6 31 32.8 44.5 145.2 3 15.8 1867 152.8 26.6 15 49.8 7.6 Heavy 45")
                return
            memory, user = get_or_create_user_memory(user_id)
            user["body_baseline"] = {
                "weight_lb": float(parts[0]),
                "body_fat_percent": float(parts[1]),
                "bmi": float(parts[2]),
                "skeletal_muscle_percent": float(parts[3]),
                "muscle_mass_lb": float(parts[4]),
                "muscle_storage_ability_level": int(float(parts[5])),
                "protein_percent": float(parts[6]),
                "bmr_kcal": float(parts[7]),
                "fat_free_body_weight_lb": float(parts[8]),
                "subcutaneous_fat_percent": float(parts[9]),
                "visceral_fat": int(float(parts[10])),
                "body_water_percent": float(parts[11]),
                "bone_mass_lb": float(parts[12]),
                "body_type": parts[13],
                "metabolic_age": int(float(parts[14])),
                "timestamp": utc_now_iso(),
            }
            memory[user_id] = user
            save_memory(memory)
            await message.channel.send(build_body_baseline_report(user_id))
            return

        if command == "body-baseline":
            await message.channel.send(build_body_baseline_report(user_id))
            return

        if command == "set-body-goal":
            parts = body.split()
            if len(parts) < 3:
                await message.channel.send("Usage: !architect set-body-goal 190 200 11")
                return
            memory, user = get_or_create_user_memory(user_id)
            user["body_goal"] = {
                "target_weight_low_lb": float(parts[0]),
                "target_weight_high_lb": float(parts[1]),
                "target_body_fat_percent": float(parts[2]),
                "timestamp": utc_now_iso(),
            }
            memory[user_id] = user
            save_memory(memory)
            await message.channel.send(build_body_goal_report(user_id))
            return

        if command == "body-goal":
            await message.channel.send(build_body_goal_report(user_id))
            return

        if command == "set-body-change":
            parts = body.split()
            if len(parts) < 3:
                await message.channel.send("Usage: !architect set-body-change 32.6 4.8 7.5")
                return
            memory, user = get_or_create_user_memory(user_id)
            user["body_change"] = {
                "weight_change_lb": float(parts[0]),
                "bmi_change": float(parts[1]),
                "body_fat_change_percent": float(parts[2]),
                "timestamp": utc_now_iso(),
            }
            memory[user_id] = user
            save_memory(memory)
            await message.channel.send(build_body_change_report(user_id))
            return

        if command == "body-change":
            await message.channel.send(build_body_change_report(user_id))
            return

        if command == "set-activity-baseline":
            parts = body.split()
            if len(parts) < 5:
                await message.channel.send("Usage: !architect set-activity-baseline 900 60 12 10000 5")
                return
            memory, user = get_or_create_user_memory(user_id)
            user["activity_baseline"] = {
                "active_calories_daily": float(parts[0]),
                "exercise_minutes_daily": float(parts[1]),
                "stand_hours_daily": float(parts[2]),
                "steps_daily": int(float(parts[3])),
                "workouts_per_week": int(float(parts[4])),
                "timestamp": utc_now_iso(),
            }
            memory[user_id] = user
            save_memory(memory)
            await message.channel.send(build_activity_baseline_report(user_id))
            return

        if command == "activity-baseline":
            await message.channel.send(build_activity_baseline_report(user_id))
            return

        if command == "log-activity":
            parts = body.split()
            if len(parts) < 4:
                await message.channel.send("Usage: !architect log-activity 650 52 9800 lifting_and_incline_walk")
                return
            append_memory_item(user_id, "activity_logs", {
                "active_calories": float(parts[0]),
                "exercise_minutes": float(parts[1]),
                "steps": int(float(parts[2])),
                "activity_type": parts[3],
                "date": today_dr(),
                "timestamp": utc_now_iso(),
            })
            await message.channel.send("Activity logged.")
            return

        if command == "activity-report":
            await message.channel.send(build_activity_report(user_id))
            return

        if command == "set-profile":
            parts = body.split()
            if len(parts) < 2:
                await message.channel.send("Usage: !architect set-profile 12/24/1986 6:00AM")
                return
            memory, user = get_or_create_user_memory(user_id)
            user["profile"] = {"birth_date": parts[0], "birth_time": parts[1], "timestamp": utc_now_iso()}
            memory[user_id] = user
            save_memory(memory)
            await message.channel.send(build_profile_identity_report(user_id))
            return

        if command == "profile":
            await message.channel.send(build_profile_identity_report(user_id))
            return

        if command == "set-transformation-goal":
            parts = body.split()
            if len(parts) < 5:
                await message.channel.send("Usage: !architect set-transformation-goal 221.6 190 200 2026-06-01 lean-aesthetic")
                return
            memory, user = get_or_create_user_memory(user_id)
            user["transformation_goal"] = {
                "current_weight_lb": float(parts[0]),
                "target_weight_low_lb": float(parts[1]),
                "target_weight_high_lb": float(parts[2]),
                "deadline_date": parts[3],
                "goal_type": parts[4],
                "timestamp": utc_now_iso(),
            }
            memory[user_id] = user
            save_memory(memory)
            await message.channel.send(build_transformation_status_report(user_id))
            return

        if command == "transformation-status":
            await message.channel.send(build_transformation_status_report(user_id))
            return

        if command == "set-fitness-profile":
            parts = body.split()
            if len(parts) < 8:
                await message.channel.send("Usage: !architect set-fitness-profile hybrid base_building 5 home_bodyweight_soon_gym 300_pushups_daily pushups_situps_squats_lunges_fullbody bodyweight_aesthetics_to_lean_bulk current_starting_phase")
                return
            memory, user = get_or_create_user_memory(user_id)
            user["fitness_profile"] = {
                "current_training_mode": parts[0],
                "current_phase": parts[1],
                "training_days_available": int(float(parts[2])),
                "available_resources": parts[3],
                "current_challenge": parts[4],
                "movement_base": parts[5],
                "physique_target": parts[6],
                "starting_point_notes": parts[7],
                "timestamp": utc_now_iso(),
            }
            memory[user_id] = user
            save_memory(memory)
            await message.channel.send(build_fitness_profile_report(user_id))
            return

        if command == "show-fitness-profile":
            await message.channel.send(build_fitness_profile_report(user_id))
            return

        if command == "update-resources":
            if not body:
                await message.channel.send("Usage: !architect update-resources full_gym_home_cardio")
                return
            memory, user = get_or_create_user_memory(user_id)
            user.setdefault("fitness_profile", {})
            user["fitness_profile"]["available_resources"] = body
            user["fitness_profile"]["timestamp"] = utc_now_iso()
            memory[user_id] = user
            save_memory(memory)
            await message.channel.send(f"Resources updated: {body}")
            return

        if command == "update-training-days":
            if not body:
                await message.channel.send("Usage: !architect update-training-days 6")
                return
            memory, user = get_or_create_user_memory(user_id)
            user.setdefault("fitness_profile", {})
            user["fitness_profile"]["training_days_available"] = int(float(body))
            user["fitness_profile"]["timestamp"] = utc_now_iso()
            memory[user_id] = user
            save_memory(memory)
            await message.channel.send(f"Training days updated: {int(float(body))}")
            return

        if command == "update-fitness-mode":
            parts = body.split()
            if len(parts) < 2:
                await message.channel.send("Usage: !architect update-fitness-mode hybrid strength_recomp")
                return
            memory, user = get_or_create_user_memory(user_id)
            user.setdefault("fitness_profile", {})
            user["fitness_profile"]["current_training_mode"] = parts[0]
            user["fitness_profile"]["current_phase"] = parts[1]
            user["fitness_profile"]["timestamp"] = utc_now_iso()
            memory[user_id] = user
            save_memory(memory)
            await message.channel.send(f"Fitness mode updated:\n- Training mode: {parts[0]}\n- Phase: {parts[1]}")
            return

        if command == "adjust-goal-timeline":
            if not body:
                await message.channel.send("Usage: !architect adjust-goal-timeline 2026-06-15")
                return
            memory, user = get_or_create_user_memory(user_id)
            user.setdefault("transformation_goal", {})
            user["transformation_goal"]["deadline_date"] = body
            user["transformation_goal"]["timestamp"] = utc_now_iso()
            memory[user_id] = user
            save_memory(memory)
            await message.channel.send(f"Transformation deadline updated: {body}")
            return

        if command == "fitness-adjustment":
            report = build_fitness_adjustment_report(user_id)
            await message.channel.send(report)
            if message.guild:
                await send_to_department(message.guild, "fitness_lab", report)
            return

        if command == "adjustment-engine":
            result = analyze_adjustment_engine(user_id)
            await message.channel.send(
                "Architect Adjustment Engine:\n"
                f"- Recommendation: {result.get('recommendation', 'No recommendation')}\n"
                f"- Training days counted: {result.get('training_days', 0)}\n"
                f"- Activity days counted: {result.get('activity_days', 0)}"
            )
            return

        if command == "set-workout-phase":
            parts = body.split()
            if len(parts) < 2:
                await message.channel.send("Usage: !architect set-workout-phase calisthenics 12")
                return
            memory, user = get_or_create_user_memory(user_id)
            user["user_workout_engine"]["workout_phase"] = parts[0]
            user["user_workout_engine"]["phase_duration_weeks"] = int(float(parts[1]))
            memory[user_id] = user
            save_memory(memory)
            await message.channel.send(f"Workout phase saved:\n- Phase: {parts[0]}\n- Duration: {int(float(parts[1]))} week(s)")
            return

        if command == "update-equipment":
            if not body:
                await message.channel.send("Usage: !architect update-equipment kettlebell weighted_vest bands")
                return
            items = body.split()
            memory, user = get_or_create_user_memory(user_id)
            user["user_workout_engine"]["equipment"] = items
            memory[user_id] = user
            save_memory(memory)
            await message.channel.send("Equipment updated:\n- " + ", ".join(items))
            return

        if command == "weekly-workout-plan":
            await message.channel.send(build_weekly_workout_plan(user_id))
            return

        if command == "today-workout":
            await message.channel.send(build_today_workout(user_id))
            return

        if command == "pushup-plan":
            parts = body.split()
            total_target = int(float(parts[0])) if len(parts) >= 1 else 300
            max_set = int(float(parts[1])) if len(parts) >= 2 else 25
            await message.channel.send(build_pushup_plan(user_id, total_target, max_set))
            return

        if command == "log-weight":
            if not body:
                await message.channel.send("Usage: !architect log-weight 186.4")
                return
            append_memory_item(user_id, "weights", {"value": body, "timestamp": utc_now_iso()})
            await message.channel.send(f"Logged weight: {body}")
            return

        if command == "log-goal":
            if not body:
                await message.channel.send("Usage: !architect log-goal Stay disciplined this week")
                return
            append_memory_item(user_id, "goals", {"text": body, "timestamp": utc_now_iso()})
            await message.channel.send(f"Logged goal: {body}")
            return

        if command == "log-habit":
            if not body:
                await message.channel.send("Usage: !architect log-habit cardio complete")
                return
            append_memory_item(user_id, "habits", {"text": body, "timestamp": utc_now_iso()})
            await message.channel.send(f"Logged habit: {body}")
            return

        if command == "checkin":
            parts = body.split()
            if len(parts) < 6:
                await message.channel.send("Usage: !architect checkin energy 8 motivation 7 focus 9")
                return
            append_memory_item(user_id, "checkins", {
                "energy": parts[1],
                "motivation": parts[3],
                "focus": parts[5],
                "timestamp": utc_now_iso(),
            })
            await message.channel.send(f"Check-in logged: Energy {parts[1]} | Motivation {parts[3]} | Focus {parts[5]}")
            return

        if command == "log-sleep":
            if not body:
                await message.channel.send("Usage: !architect log-sleep 7.5")
                return
            append_memory_item(user_id, "sleep_logs", {"hours": float(body), "date": today_dr(), "timestamp": utc_now_iso()})
            await message.channel.send(f"Sleep logged: {float(body):.2f} hours")
            return

        if command == "log-mood":
            if not body:
                await message.channel.send("Usage: !architect log-mood 8")
                return
            append_memory_item(user_id, "mood_logs", {"score": float(body), "date": today_dr(), "timestamp": utc_now_iso()})
            await message.channel.send(f"Mood logged: {float(body):.2f}")
            return

        if command == "log-focus":
            if not body:
                await message.channel.send("Usage: !architect log-focus 7")
                return
            append_memory_item(user_id, "focus_logs", {"score": float(body), "date": today_dr(), "timestamp": utc_now_iso()})
            await message.channel.send(f"Focus logged: {float(body):.2f}")
            return

        if command == "log-workout":
            if not body:
                await message.channel.send("Usage: !architect log-workout pushups 300")
                return
            append_memory_item(user_id, "workouts", {"text": body, "date": today_dr(), "timestamp": utc_now_iso()})
            await message.channel.send(f"Workout logged: {body}")
            return

        if command == "life-report":
            await message.channel.send(build_daily_report(user_id))
            return

        if command == "set-week-mode":
            if not body:
                await message.channel.send("Usage: !architect set-week-mode trading")
                return
            memory, user = get_or_create_user_memory(user_id)
            user["context"]["week_mode"] = body
            memory[user_id] = user
            save_memory(memory)
            await message.channel.send(f"Week mode set: {body}")
            return

        if command == "set-week-focus":
            if not body:
                await message.channel.send("Usage: !architect set-week-focus trading fitness knowledge")
                return
            items = body.split()
            memory, user = get_or_create_user_memory(user_id)
            user["context"]["week_focus"] = items
            memory[user_id] = user
            save_memory(memory)
            await message.channel.send(f"Week focus set: {', '.join(items)}")
            return

        if command == "set-training-mode":
            if not body:
                await message.channel.send("Usage: !architect set-training-mode calisthenics")
                return
            memory, user = get_or_create_user_memory(user_id)
            user["context"]["training_mode"] = body
            memory[user_id] = user
            save_memory(memory)
            await message.channel.send(f"Training mode set: {body}")
            return

        if command == "set-nutrition":
            if not body:
                await message.channel.send("Usage: !architect set-nutrition lean-bulk")
                return
            memory, user = get_or_create_user_memory(user_id)
            user["context"]["nutrition_mode"] = body
            memory[user_id] = user
            save_memory(memory)
            await message.channel.send(f"Nutrition mode set: {body}")
            return

        if command == "set-daily-goal":
            if not body:
                await message.channel.send("Usage: !architect set-daily-goal pushups 300")
                return
            memory, user = get_or_create_user_memory(user_id)
            user["context"]["daily_goals"].append({"text": body, "timestamp": utc_now_iso()})
            memory[user_id] = user
            save_memory(memory)
            await message.channel.send(f"Daily goal set: {body}")
            return

        if command in ("watchlist", "set-watchlist"):
            if not body:
                await message.channel.send("Usage: !architect set-watchlist MNQ US30 NAS100 TSLA")
                return
            tickers = body.split()
            memory, user = get_or_create_user_memory(user_id)
            user["context"]["watchlist"] = tickers
            user["notes"].append({"text": f"WATCHLIST::{' '.join(tickers)}", "timestamp": utc_now_iso()})
            memory[user_id] = user
            save_memory(memory)
            await message.channel.send(f"ARTEMIS WATCHLIST SET\n\nTracking:\n{' '.join(tickers)}\n\nArtemis is now locked into your market focus.")
            return

        if command == "week-plan":
            await message.channel.send(build_week_plan(user_id))
            return

        if command == "morning-brief":
            await message.channel.send(build_morning_brief(user_id))
            return

        if command == "log-pnl":
            if not body:
                await message.channel.send("Usage: !architect log-pnl 250")
                return
            append_memory_item(user_id, "pnl_logs", {"value": float(body), "date": today_dr(), "timestamp": utc_now_iso()})
            await message.channel.send(f"PnL logged: {float(body):.2f}")
            return

        if command == "pnl-report":
            await message.channel.send(build_pnl_report(user_id))
            return

        if command == "win":
            if not body:
                await message.channel.send("Usage: !architect win Executed with patience")
                return
            append_memory_item(user_id, "wins", {"text": body, "date": today_dr(), "timestamp": utc_now_iso()})
            await message.channel.send(f"Win logged: {body}")
            return

        if command == "mistake":
            if not body:
                await message.channel.send("Usage: !architect mistake Entered before confirmation")
                return
            append_memory_item(user_id, "mistakes", {"text": body, "date": today_dr(), "timestamp": utc_now_iso()})
            await message.channel.send(f"Mistake logged: {body}")
            return

        if command == "daily-report":
            await message.channel.send(build_daily_report(user_id))
            return

        if command == "show-profile":
            await message.channel.send(build_profile_text(user_id))
            return

        if command == "weekly-report":
            await message.channel.send(build_weekly_report(user_id))
            return

        if command == "trade-review":
            if not body:
                await message.channel.send("Usage: !architect trade-review Instrument: MNQ | Entry: 18450 | Stop: 18420 | Target: 18520 | Reason: breakout retest | Result: +65 pts")
                return
            log_trade_raw(user_id, body)
            review_prompt = (
                "Review this trade like a sharp trading coach. "
                "Identify strengths, weaknesses, discipline issues, risk issues, and next-step improvements.\n\n"
                f"Trade:\n{body}"
            )
            await run_ai_reply(message, review_prompt)
            return

        if command == "trade-log":
            parts = body.split()
            if len(parts) < 6:
                await message.channel.send("Usage: !architect trade-log MNQ 18450 18420 18520 breakout_retest 18515")
                return
            calc = log_trade_structured(
                user_id=user_id,
                instrument=parts[0],
                entry=float(parts[1]),
                stop=float(parts[2]),
                target=float(parts[3]),
                setup=parts[4],
                exit_price=float(parts[5]),
            )
            await message.channel.send(
                "Trade logged:\n"
                f"{parts[0]} | Entry {float(parts[1])} | Stop {float(parts[2])} | Target {float(parts[3])} | Exit {float(parts[5])}\n"
                f"Setup: {parts[4]}\n"
                f"Risk: {calc['risk_pts']:.2f} pts\n"
                f"Target distance: {calc['target_pts']:.2f} pts\n"
                f"Result: {calc['result_pts']:.2f} pts\n"
                f"Planned R: {calc['planned_r']:.2f}\n"
                f"Realized R: {calc['realized_r']:.2f}"
            )
            return

        if command == "stats":
            await message.channel.send(build_trade_stats(user_id))
            return

        if command == "dashboard":
            await message.channel.send(build_dashboard(user_id))
            return

        if command == "coach":
            await message.channel.send(build_coach_report(user_id))
            return

        if command == "artemis-brief":
            await message.channel.send(
                "ARTEMIS BRIEF\n\n"
                "Market Focus:\n"
                "• Your watchlist is active\n\n"
                "Macro Awareness:\n"
                "• Check for CPI / Fed / NFP this week\n\n"
                "Execution Reminder:\n"
                "• Wait for HTF alignment\n"
                "• Execute break & retest\n"
                "• No chasing\n\n"
                "Discipline Focus:\n"
                "• Patience\n"
                "• Confirmation\n"
                "• Precision"
            )
            return

        if command in ("artemis-talk", "artemis-nudge"):
            await message.channel.send(
                "ARTEMIS CHECK-IN\n\n"
                "Luis — when do you want to run today's market talk?\n\n"
                "Drop a time (example: 8 PM)\n\n"
                "We’ll break down:\n"
                "• What you did\n"
                "• What you missed\n"
                "• What the market actually did\n"
                "• What we improve tomorrow\n\n"
                "I'm ready when you are."
            )
            return

        if command == "artemis-weekly":
            await message.channel.send(
                "ARTEMIS WEEKLY BRIEF\n\n"
                "Luis — here is what we are tracking this week:\n\n"
                "Macro Events:\n"
                "- CPI / Inflation data\n"
                "- Fed speakers\n"
                "- NFP if applicable\n\n"
                "Earnings Watch:\n"
                "- Check your watchlist tickers\n"
                "- Compare to last earnings report\n\n"
                "Focus:\n"
                "- Trade reaction, not prediction\n"
                "- Let volatility create opportunity\n\n"
                "Stay sharp this week."
            )
            return

        if command == "artemis-reminder":
            await message.channel.send(
                "ARTEMIS REMINDER\n\n"
                "Luis — quick heads up:\n\n"
                "High impact event approaching.\n"
                "Check the time and prepare your levels.\n\n"
                "Remember:\n"
                "- No chasing\n"
                "- Wait for confirmation\n"
                "- Protect capital\n\n"
                "Execution over emotion."
            )
            return

        if command == "artemis-recap":
            await message.channel.send(
                "ARTEMIS MARKET RECAP\n\n"
                "Luis — let's review your execution based on YOUR system:\n\n"
                "1. HTF Alignment\n"
                "2. Liquidity & Structure\n"
                "3. Entry Model\n"
                "4. Execution Review\n"
                "5. Missed Opportunities\n"
                "6. Market Behavior\n"
                "7. Improvement Focus\n\n"
                "Execution > Emotion\n"
                "Discipline builds consistency."
            )
            return

        if command == "artemis-bias":
            await message.channel.send(
                "ARTEMIS BIAS ENGINE\n\n"
                "1. HTF Bias First\n"
                "2. Liquidity First\n"
                "3. Structure Second\n"
                "4. Entry Model Focus\n"
                "5. Timing Windows\n"
                "6. Execution Reminder\n\n"
                "Bias before entry. Structure before size. Discipline before profit."
            )
            return

        if command == "artemis-watchlist":
            await message.channel.send(
                "ARTEMIS WATCHLIST BRIDGE\n\n"
                "Futures / Indices:\n- MNQ\n- ES\n- YM\n- US30\n- NAS100\n\n"
                "Options Focus:\n- TSLA\n- AAPL\n- NVDA\n- SPY\n- QQQ\n\n"
                "Forex Swing Focus:\n- EUR/USD\n- GBP/USD\n- XAU/USD\n- USD/JPY\n"
            )
            return

        if command == "artemis-daily":
            await message.channel.send(
                "ARTEMIS DAILY EXECUTION SYSTEM\n\n"
                "FOCUS:\n- Primary: MNQ / NAS100\n- Secondary: US30\n- Confirmation: ES\n\n"
                "ENTRY MODEL:\n- Sweep → reclaim → BOS → pullback → entry\n- VWAP / EMA confluence required\n\n"
                "EXECUTION RULES:\n- Do not chase\n- Do not predict, react\n- No structure = no trade\n"
            )
            return

        await run_ai_reply(message, prompt)

    except Exception as e:
        print(f"Error in on_message: {e}")
        await message.channel.send(f"Something went wrong while processing that request.\n\nError: {str(e)[:180]}")


bot.run(DISCORD_TOKEN)
