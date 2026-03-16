import os
import json
from datetime import datetime, timezone, date
from zoneinfo import ZoneInfo

import discord
from discord.ext import tasks
from openai import OpenAI

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

MEMORY_FILE = "memory.json"
TRADES_FILE = "trades.json"
GUILD_STATE_FILE = "guild_state.json"

DR_TZ = ZoneInfo("America/Santo_Domingo")
MORNING_BRIEF_HOUR = 8
MORNING_BRIEF_MINUTE = 0

CHANNELS = {
    "mission_brief": "mission-brief",
    "daily_checkin": "daily-checkin",
    "weekly_review": "weekly-review",
    "performance_report": "performance-report",
    "system_analysis": "system-analysis",
}

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
""".strip()

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

USER_DEFAULT = {
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
    "adjustment_engine": {"last_analysis": {}, "last_updated": ""},
    "user_workout_engine": {"workout_phase": "", "phase_duration_weeks": 0, "equipment": []},
    "context": {
        "week_mode": "",
        "week_focus": [],
        "training_mode": "",
        "nutrition_mode": "",
        "daily_goals": [],
        "watchlist": [],
    },
}

DEPARTMENT_PROMPTS = {
    "trading": """
You are currently operating inside the Trading Desk department.

Priority:
- trading discipline
- execution quality
- review process
- risk management
- repeatable edge
- performance tracking

Respond like a sharp trading coach and strategist.
Be practical, structured, and direct.
""".strip(),
    "fitness": """
You are currently operating inside the Fitness Lab department.

Priority:
- workouts
- training consistency
- body recomposition
- recovery
- performance habits

Respond like a practical performance coach.
Be structured, motivating, and realistic.
""".strip(),
    "nutrition": """
You are currently operating inside the Nutrition Lab department.

Priority:
- meal consistency
- food quality
- macros
- sustainable choices
- body support

Respond like a practical nutrition coach.
Keep advice simple, useful, and repeatable.
""".strip(),
    "knowledge": """
You are currently operating inside the Knowledge Vault department.

Priority:
- idea capture
- note quality
- insight retrieval
- organizing thinking
- second-brain support

Respond like a strategist and knowledge architect.
Help turn information into usable insight.
""".strip(),
    "builder": """
You are currently operating inside the Builder Lab department.

Priority:
- project execution
- business building
- systems
- shipping ideas
- creating momentum

Respond like an execution advisor and builder.
Help turn ideas into next steps and systems.
""".strip(),
    "cosmic": """
You are currently operating inside the Cosmic Reflection department.

Priority:
- reflection
- mindset
- emotional clarity
- alignment
- perspective

Respond with depth, calm, and grounded wisdom.
Be reflective but still practical.
""".strip(),
    "analysis": """
You are currently operating inside the Architect Analysis / Performance department.

Priority:
- pattern recognition
- personal review
- discipline
- progress tracking
- extracting lessons from behavior and data

Respond like a high-level performance analyst and coach.
Be honest, constructive, and useful.
""".strip(),
    "general": """
You are operating in a general Architect OS context.

Respond as Architect:
strategic, practical, clear, and helpful.
""".strip(),
}


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


def dr_now():
    return datetime.now(DR_TZ)


def today_dr():
    return dr_now().date().isoformat()


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


def clamp_int(value, low, high):
    return max(low, min(high, value))


def normalize_token(text: str) -> str:
    return str(text or "").strip().lower().replace("-", "_")


def parse_iso_date_safe(text: str):
    try:
        return date.fromisoformat(text)
    except Exception:
        return None


def load_json_file(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json_file(path, data):
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


def deep_merge_defaults(data, defaults):
    if not isinstance(data, dict):
        data = {}
    for key, value in defaults.items():
        if isinstance(value, dict):
            data[key] = deep_merge_defaults(data.get(key, {}), value)
        else:
            data.setdefault(key, value[:] if isinstance(value, list) else value)
    return data


def get_or_create_user_memory(user_id: str):
    memory = get_memory()
    user_data = deep_merge_defaults(memory.get(user_id, {}), USER_DEFAULT.copy())
    return memory, user_data


def save_user_memory(user_id: str, user_data: dict):
    memory = get_memory()
    memory[user_id] = user_data
    save_memory(memory)


def update_user_section(user_id: str, section: str, payload: dict):
    memory, user = get_or_create_user_memory(user_id)
    user[section] = payload
    memory[user_id] = user
    save_memory(memory)


def append_user_list(user_id: str, section: str, payload: dict):
    memory, user = get_or_create_user_memory(user_id)
    user.setdefault(section, []).append(payload)
    memory[user_id] = user
    save_memory(memory)


def register_guild_user(guild_id: str, user_id: str):
    state = get_guild_state()
    guild = state.get(guild_id, {"primary_user_id": "", "last_morning_brief_date": ""})
    guild["primary_user_id"] = user_id
    state[guild_id] = guild
    save_guild_state(state)


def set_last_morning_brief_date(guild_id: str, date_text: str):
    state = get_guild_state()
    guild = state.get(guild_id, {"primary_user_id": "", "last_morning_brief_date": ""})
    guild["last_morning_brief_date"] = date_text
    state[guild_id] = guild
    save_guild_state(state)


def get_department_prompt(channel_name: str) -> str:
    name = (channel_name or "").lower()
    if "trading" in name or name in {"market-prep", "chart-review", "market-notes"}:
        return DEPARTMENT_PROMPTS["trading"]
    if "fitness" in name or name in {"fitness-log", "training-protocol", "supplement-stack"}:
        return DEPARTMENT_PROMPTS["fitness"]
    if "nutrition" in name or name in {"meal-log", "meal-architect"}:
        return DEPARTMENT_PROMPTS["nutrition"]
    if "knowledge" in name or name in {"reading-log", "pdf-archive"}:
        return DEPARTMENT_PROMPTS["knowledge"]
    if "builder" in name or name in {"project-builder", "research-lab"}:
        return DEPARTMENT_PROMPTS["builder"]
    if "cosmic" in name or "reflection" in name or name in {"daily-alignment", "cosmic-notes", "life-design"}:
        return DEPARTMENT_PROMPTS["cosmic"]
    if "analysis" in name or "performance" in name or name in {"system-analysis", "performance-report"}:
        return DEPARTMENT_PROMPTS["analysis"]
    return DEPARTMENT_PROMPTS["general"]


def get_channel_mode(channel_name: str) -> str:
    return ARCHITECT_CORE_IDENTITY + "\n\n" + get_department_prompt(channel_name)


def extract_prompt(content: str) -> str:
    return content.replace("!architect", "", 1).strip()


def split_command_and_body(prompt: str):
    if not prompt:
        return "", ""
    parts = prompt.split(" ", 1)
    return parts[0].strip().lower(), (parts[1].strip() if len(parts) > 1 else "")


def find_text_channel_by_name(guild: discord.Guild, channel_name: str):
    for channel in guild.text_channels:
        if channel.name == channel_name:
            return channel
    return None


def get_system_channel(guild: discord.Guild, key: str):
    return find_text_channel_by_name(guild, CHANNELS.get(key, ""))


def get_equipment_list(user_id: str):
    _, user = get_or_create_user_memory(user_id)
    return user["user_workout_engine"].get("equipment", [])


def get_workout_phase_data(user_id: str):
    _, user = get_or_create_user_memory(user_id)
    return user["user_workout_engine"]


def tokenize_resource_text(text: str):
    raw = normalize_token(text)
    if not raw:
        return set()
    parts = set(raw.replace(",", " ").split())
    expanded = set(parts)
    for part in parts:
        expanded.update(x for x in part.split("_") if x)
    expanded.add(raw)
    return expanded


def has_gym_access(user_id: str) -> bool:
    _, user = get_or_create_user_memory(user_id)
    resources = str(user.get("fitness_profile", {}).get("available_resources", "")).lower()
    equipment = {x.lower() for x in get_equipment_list(user_id)}
    return ("gym" in resources or "full_gym" in resources or
            any(x in equipment for x in {"barbell", "machine", "cable"}))


def build_training_setup_snapshot(user_id: str):
    _, user = get_or_create_user_memory(user_id)
    fp = user.get("fitness_profile", {})
    equipment = {normalize_token(x) for x in get_equipment_list(user_id)}
    has_gym = has_gym_access(user_id)
    snapshot = {
        "resources_text": str(fp.get("available_resources", "")),
        "resource_tokens": tokenize_resource_text(fp.get("available_resources", "")),
        "equipment": sorted(equipment),
        "has_gym": has_gym,
        "has_kettlebell": any(x in equipment for x in {"kettlebell", "kettlebells"}),
        "has_weighted_vest": any(x in equipment for x in {"weighted_vest", "vest"}),
        "has_pullup_bar": any(x in equipment for x in {"pull_up_bar", "pullup_bar"}),
        "has_bands": any(x in equipment for x in {"bands", "band"}),
        "has_dumbbells": any(x in equipment for x in {"dumbbells", "dumbbell"}),
        "has_trx": "trx" in equipment,
    }
    snapshot["home_bodyweight_only"] = not any([
        snapshot["has_gym"],
        snapshot["has_kettlebell"],
        snapshot["has_weighted_vest"],
        snapshot["has_pullup_bar"],
        snapshot["has_bands"],
        snapshot["has_dumbbells"],
        snapshot["has_trx"],
    ])
    snapshot["mode_label"] = "gym/hybrid" if snapshot["has_gym"] else "home/bodyweight"
    return snapshot


def build_equipment_modifier_text(user_id: str) -> str:
    equipment = get_equipment_list(user_id)
    return ", ".join(equipment) if equipment else "No extra equipment updated yet."


def has_meaningful_brief_data(user_id: str) -> bool:
    _, user = get_or_create_user_memory(user_id)
    context = user.get("context", {})
    return any([
        any(context.get(k) for k in ["week_mode", "week_focus", "training_mode", "nutrition_mode", "daily_goals", "watchlist"]),
        any(user.get(k) for k in ["sleep_logs", "mood_logs", "focus_logs", "activity_logs"]),
        any([
            user.get("body_baseline"),
            user.get("body_goal"),
            user.get("fitness_profile"),
            user.get("transformation_goal"),
            user.get("activity_baseline"),
            user.get("user_workout_engine", {}).get("workout_phase"),
            user.get("user_workout_engine", {}).get("equipment"),
        ])
    ])


def set_body_baseline(user_id: str, *vals):
    keys = [
        "weight_lb", "body_fat_percent", "bmi", "skeletal_muscle_percent",
        "muscle_mass_lb", "muscle_storage_ability_level", "protein_percent", "bmr_kcal",
        "fat_free_body_weight_lb", "subcutaneous_fat_percent", "visceral_fat",
        "body_water_percent", "bone_mass_lb", "body_type", "metabolic_age"
    ]
    payload = dict(zip(keys, vals))
    payload["timestamp"] = utc_now_iso()
    update_user_section(user_id, "body_baseline", payload)


def build_body_baseline_report(user_id: str) -> str:
    _, user = get_or_create_user_memory(user_id)
    b = user.get("body_baseline", {})
    if not b:
        return "No body baseline saved yet.\nUse:\n`!architect set-body-baseline 221.6 31 32.8 44.5 145.2 3 15.8 1867 152.8 26.6 15 49.8 7.6 Heavy 45`"
    return "\n".join([
        "Architect Body Baseline:",
        f"- Weight: {safe_float(b.get('weight_lb')):.1f} lb",
        f"- Body Fat: {safe_float(b.get('body_fat_percent')):.1f}%",
        f"- BMI: {safe_float(b.get('bmi')):.1f}",
        f"- Skeletal Muscle: {safe_float(b.get('skeletal_muscle_percent')):.1f}%",
        f"- Muscle Mass: {safe_float(b.get('muscle_mass_lb')):.1f} lb",
        f"- Muscle Storage Ability Level: {safe_int(b.get('muscle_storage_ability_level'))}",
        f"- Protein: {safe_float(b.get('protein_percent')):.1f}%",
        f"- BMR: {safe_float(b.get('bmr_kcal')):.0f} kcal",
        f"- Fat-Free Body Weight: {safe_float(b.get('fat_free_body_weight_lb')):.1f} lb",
        f"- Subcutaneous Fat: {safe_float(b.get('subcutaneous_fat_percent')):.1f}%",
        f"- Visceral Fat: {safe_int(b.get('visceral_fat'))}",
        f"- Body Water: {safe_float(b.get('body_water_percent')):.1f}%",
        f"- Bone Mass: {safe_float(b.get('bone_mass_lb')):.1f} lb",
        f"- Body Type: {b.get('body_type', 'Not set')}",
        f"- Metabolic Age: {safe_int(b.get('metabolic_age'))}",
    ])


def set_body_goal(user_id: str, low: float, high: float, bf: float):
    update_user_section(user_id, "body_goal", {
        "target_weight_low_lb": low,
        "target_weight_high_lb": high,
        "target_body_fat_percent": bf,
        "timestamp": utc_now_iso(),
    })


def build_body_goal_report(user_id: str) -> str:
    _, user = get_or_create_user_memory(user_id)
    g = user.get("body_goal", {})
    if not g:
        return "No body goal saved yet. Use `!architect set-body-goal 190 200 11`"
    return (
        "Architect Body Goal:\n"
        f"- Target weight range: {safe_float(g.get('target_weight_low_lb')):.1f} to {safe_float(g.get('target_weight_high_lb')):.1f} lb\n"
        f"- Target body fat: {safe_float(g.get('target_body_fat_percent')):.1f}%"
    )


def set_body_change(user_id: str, weight_change_lb: float, bmi_change: float, body_fat_change_percent: float):
    update_user_section(user_id, "body_change", {
        "weight_change_lb": weight_change_lb,
        "bmi_change": bmi_change,
        "body_fat_change_percent": body_fat_change_percent,
        "timestamp": utc_now_iso(),
    })


def build_body_change_report(user_id: str) -> str:
    _, user = get_or_create_user_memory(user_id)
    c = user.get("body_change", {})
    if not c:
        return "No body change snapshot saved yet. Use `!architect set-body-change 32.6 4.8 7.5`"
    return (
        "Architect Body Change Snapshot:\n"
        f"- Weight change: +{safe_float(c.get('weight_change_lb')):.1f} lb\n"
        f"- BMI change: +{safe_float(c.get('bmi_change')):.1f}\n"
        f"- Body fat change: +{safe_float(c.get('body_fat_change_percent')):.1f}%"
    )


def set_activity_baseline(user_id: str, active_calories_daily: float, exercise_minutes_daily: float, stand_hours_daily: float, steps_daily: int, workouts_per_week: int):
    update_user_section(user_id, "activity_baseline", {
        "active_calories_daily": active_calories_daily,
        "exercise_minutes_daily": exercise_minutes_daily,
        "stand_hours_daily": stand_hours_daily,
        "steps_daily": steps_daily,
        "workouts_per_week": workouts_per_week,
        "timestamp": utc_now_iso(),
    })


def build_activity_baseline_report(user_id: str) -> str:
    _, user = get_or_create_user_memory(user_id)
    a = user.get("activity_baseline", {})
    if not a:
        return "No activity baseline saved yet. Use `!architect set-activity-baseline 900 60 12 10000 5`"
    return (
        "Architect Activity Baseline:\n"
        f"- Active calories daily: {safe_float(a.get('active_calories_daily')):.0f}\n"
        f"- Exercise minutes daily: {safe_float(a.get('exercise_minutes_daily')):.0f}\n"
        f"- Stand hours daily: {safe_float(a.get('stand_hours_daily')):.0f}\n"
        f"- Steps daily: {safe_int(a.get('steps_daily'))}\n"
        f"- Workouts per week: {safe_int(a.get('workouts_per_week'))}"
    )


def log_activity(user_id: str, active_calories: float, exercise_minutes: float, steps: int, activity_type: str):
    append_user_list(user_id, "activity_logs", {
        "active_calories": active_calories,
        "exercise_minutes": exercise_minutes,
        "steps": steps,
        "activity_type": activity_type,
        "date": today_dr(),
        "timestamp": utc_now_iso(),
    })


def build_activity_report(user_id: str) -> str:
    _, user = get_or_create_user_memory(user_id)
    baseline = user.get("activity_baseline", {})
    logs = user.get("activity_logs", [])
    if not baseline and not logs:
        return "No activity data saved yet. Use `!architect set-activity-baseline` and `!architect log-activity`."
    today_logs = [x for x in logs if x.get("date") == today_dr()]
    total = len(logs)
    avg_active = sum(safe_float(x.get("active_calories")) for x in logs) / total if total else 0
    avg_ex = sum(safe_float(x.get("exercise_minutes")) for x in logs) / total if total else 0
    avg_steps = sum(safe_int(x.get("steps")) for x in logs) / total if total else 0
    return "\n".join([
        "Architect Activity Report:",
        *([
            f"- Baseline active calories: {safe_float(baseline.get('active_calories_daily')):.0f}",
            f"- Baseline exercise minutes: {safe_float(baseline.get('exercise_minutes_daily')):.0f}",
            f"- Baseline stand hours: {safe_float(baseline.get('stand_hours_daily')):.0f}",
            f"- Baseline steps: {safe_int(baseline.get('steps_daily'))}",
            f"- Baseline workouts per week: {safe_int(baseline.get('workouts_per_week'))}",
        ] if baseline else []),
        f"- Activity sessions logged: {total}",
        f"- Today's active calories: {sum(safe_float(x.get('active_calories')) for x in today_logs):.0f}",
        f"- Today's exercise minutes: {sum(safe_float(x.get('exercise_minutes')) for x in today_logs):.0f}",
        f"- Today's steps: {sum(safe_int(x.get('steps')) for x in today_logs)}",
        f"- Today's latest activity type: {today_logs[-1].get('activity_type', 'No activity type logged today') if today_logs else 'No activity type logged today'}",
        f"- Average active calories per session: {avg_active:.0f}",
        f"- Average exercise minutes per session: {avg_ex:.0f}",
        f"- Average steps per session: {avg_steps:.0f}",
    ])


def set_profile(user_id: str, birth_date: str, birth_time: str):
    _, user = get_or_create_user_memory(user_id)
    profile = user.get("profile", {})
    profile.update({"birth_date": birth_date, "birth_time": birth_time, "timestamp": utc_now_iso()})
    update_user_section(user_id, "profile", profile)


def build_profile_identity_report(user_id: str) -> str:
    _, user = get_or_create_user_memory(user_id)
    p = user.get("profile", {})
    if not p:
        return "No profile identity saved yet. Use `!architect set-profile 12/24/1986 6:00AM`"
    return f"Architect Profile:\n- Birth date: {p.get('birth_date', 'Not set')}\n- Birth time: {p.get('birth_time', 'Not set')}"


def set_transformation_goal(user_id: str, current_weight_lb: float, target_weight_low_lb: float, target_weight_high_lb: float, deadline_date: str, goal_type: str):
    update_user_section(user_id, "transformation_goal", {
        "current_weight_lb": current_weight_lb,
        "target_weight_low_lb": target_weight_low_lb,
        "target_weight_high_lb": target_weight_high_lb,
        "deadline_date": deadline_date,
        "goal_type": goal_type,
        "timestamp": utc_now_iso(),
    })


def set_fitness_profile(user_id: str, current_training_mode: str, current_phase: str, training_days_available: int, available_resources: str, current_challenge: str, movement_base: str, physique_target: str, starting_point_notes: str):
    update_user_section(user_id, "fitness_profile", {
        "current_training_mode": current_training_mode,
        "current_phase": current_phase,
        "training_days_available": training_days_available,
        "available_resources": available_resources,
        "current_challenge": current_challenge,
        "movement_base": movement_base,
        "physique_target": physique_target,
        "starting_point_notes": starting_point_notes,
        "timestamp": utc_now_iso(),
    })


def build_fitness_profile_report(user_id: str) -> str:
    _, user = get_or_create_user_memory(user_id)
    fp = user.get("fitness_profile", {})
    if not fp:
        return (
            "No fitness profile saved yet.\n"
            "Use:\n"
            "`!architect set-fitness-profile hybrid base_building 5 home_bodyweight_soon_gym 300_pushups_daily pushups_situps_squats_lunges_fullbody bodyweight_aesthetics_to_lean_bulk current_starting_phase`"
        )
    return "\n".join([
        "Architect Fitness Profile:",
        f"- Current training mode: {fp.get('current_training_mode', 'Not set')}",
        f"- Current phase: {fp.get('current_phase', 'Not set')}",
        f"- Training days available: {safe_int(fp.get('training_days_available'))}",
        f"- Available resources: {fp.get('available_resources', 'Not set')}",
        f"- Current challenge: {fp.get('current_challenge', 'Not set')}",
        f"- Movement base: {fp.get('movement_base', 'Not set')}",
        f"- Physique target: {fp.get('physique_target', 'Not set')}",
        f"- Starting point notes: {fp.get('starting_point_notes', 'Not set')}",
    ])


def update_resources(user_id: str, resources: str):
    _, user = get_or_create_user_memory(user_id)
    fp = user.get("fitness_profile", {})
    fp["available_resources"] = resources
    fp["timestamp"] = utc_now_iso()
    update_user_section(user_id, "fitness_profile", fp)


def update_training_days(user_id: str, days: int):
    _, user = get_or_create_user_memory(user_id)
    fp = user.get("fitness_profile", {})
    fp["training_days_available"] = days
    fp["timestamp"] = utc_now_iso()
    update_user_section(user_id, "fitness_profile", fp)


def update_fitness_mode(user_id: str, current_training_mode: str, current_phase: str):
    _, user = get_or_create_user_memory(user_id)
    fp = user.get("fitness_profile", {})
    fp["current_training_mode"] = current_training_mode
    fp["current_phase"] = current_phase
    fp["timestamp"] = utc_now_iso()
    update_user_section(user_id, "fitness_profile", fp)


def adjust_goal_timeline(user_id: str, deadline_date: str):
    _, user = get_or_create_user_memory(user_id)
    tg = user.get("transformation_goal", {})
    tg["deadline_date"] = deadline_date
    tg["timestamp"] = utc_now_iso()
    update_user_section(user_id, "transformation_goal", tg)


def set_workout_phase(user_id: str, workout_phase: str, phase_duration_weeks: int):
    _, user = get_or_create_user_memory(user_id)
    uwe = user.get("user_workout_engine", {})
    uwe["workout_phase"] = workout_phase
    uwe["phase_duration_weeks"] = phase_duration_weeks
    update_user_section(user_id, "user_workout_engine", uwe)


def update_equipment(user_id: str, equipment_items):
    _, user = get_or_create_user_memory(user_id)
    uwe = user.get("user_workout_engine", {})
    uwe["equipment"] = [normalize_token(x) for x in equipment_items if normalize_token(x)]
    update_user_section(user_id, "user_workout_engine", uwe)


def get_weight_history_values(user_id: str):
    _, user = get_or_create_user_memory(user_id)
    vals = []
    for x in [
        user.get("body_baseline", {}).get("weight_lb"),
        user.get("transformation_goal", {}).get("current_weight_lb"),
    ]:
        fx = safe_float(x, 0)
        if fx > 0:
            vals.append(fx)
    for row in user.get("weights", []):
        fx = safe_float(row.get("value"), 0)
        if fx > 0:
            vals.append(fx)
    return vals


def estimate_current_weight(user_id: str):
    vals = get_weight_history_values(user_id)
    return vals[-1] if vals else 0.0


def get_recent_activity_stats(user_id: str, days: int = 7):
    _, user = get_or_create_user_memory(user_id)
    logs = user.get("activity_logs", [])
    today = dr_now().date()
    keep = []
    for row in logs:
        d = parse_iso_date_safe(row.get("date", ""))
        if d and 0 <= (today - d).days < days:
            keep.append(row)
    count = len(keep)
    return {
        "days": days,
        "sessions": count,
        "avg_active_calories": sum(safe_float(x.get("active_calories")) for x in keep) / count if count else 0,
        "avg_exercise_minutes": sum(safe_float(x.get("exercise_minutes")) for x in keep) / count if count else 0,
        "avg_steps": sum(safe_int(x.get("steps")) for x in keep) / count if count else 0,
    }


def get_recent_workout_days(user_id: str, days: int = 7):
    _, user = get_or_create_user_memory(user_id)
    today = dr_now().date()
    return len({
        row.get("date") for row in user.get("workouts", [])
        if (d := parse_iso_date_safe(row.get("date", ""))) and 0 <= (today - d).days < days
    })


def estimate_calorie_adjustment_from_pace(pounds_per_week: float):
    return int(round(max(pounds_per_week, 0) * 500))


def compute_transformation_status(user_id: str):
    _, user = get_or_create_user_memory(user_id)
    tr = user.get("transformation_goal", {})
    bg = user.get("body_goal", {})
    bb = user.get("body_baseline", {})
    fp = user.get("fitness_profile", {})
    if not tr:
        return None

    current_weight = safe_float(tr.get("current_weight_lb") or bb.get("weight_lb"), 0)
    target_low = safe_float(tr.get("target_weight_low_lb") or bg.get("target_weight_low_lb"), 0)
    target_high = safe_float(tr.get("target_weight_high_lb") or bg.get("target_weight_high_lb"), 0)
    deadline_text = tr.get("deadline_date", "")
    goal_type = tr.get("goal_type", "Not set")

    try:
        deadline = date.fromisoformat(deadline_text)
    except Exception:
        return {"valid": False, "error": "Invalid deadline date. Use YYYY-MM-DD."}

    if min(current_weight, target_low, target_high) <= 0:
        return {"valid": False, "error": "Transformation goal is missing valid weight data."}

    days_left = (deadline - dr_now().date()).days
    weeks_left = days_left / 7 if days_left is not None else 0
    midpoint_target = (target_low + target_high) / 2
    pounds_to_goal = current_weight - midpoint_target
    pounds_per_week = pounds_to_goal / weeks_left if weeks_left > 0 else 0
    training_days = safe_int(fp.get("training_days_available"), 0)
    current_mode = fp.get("current_training_mode", "Not set")
    current_phase = fp.get("current_phase", "Not set")
    resources = fp.get("available_resources", "Not set")

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

    recs = []
    if days_left < 0:
        recs.append("The deadline has already passed. Set a new transformation date and reassess the plan.")
    elif pounds_per_week > 2.0:
        recs.append("Your required pace is aggressive. You may need tighter nutrition, higher consistency, and possibly more training or cardio.")
    elif pounds_per_week > 1.25:
        recs.append("Your pace is demanding but possible if compliance stays high across training, sleep, and nutrition.")
    elif pounds_per_week > 0:
        recs.append("Your pace is reasonable. Focus on consistency instead of overcorrecting.")
    else:
        recs.append("Your current target range may already be close. Reassess whether the focus should shift toward lean quality and muscle retention.")

    if training_days > 0:
        if pounds_per_week > 1.25 and training_days < 5:
            recs.append("Given the timeframe, adding an extra training day could help if recovery and schedule allow.")
        elif training_days >= 5:
            recs.append("Training frequency is already solid. Prioritize recovery and food precision over blindly adding more volume.")
        else:
            recs.append("Keep training days realistic and sustainable so recovery does not collapse.")
    else:
        recs.append("Training days are not set yet. Set your fitness profile so Architect can coach more intelligently.")

    if str(current_mode).lower() == "calisthenics":
        recs.append("Calisthenics is a strong base for control and aesthetics. If resources expand, hybrid training can accelerate body recomposition.")
    elif str(current_mode).lower() == "hybrid":
        recs.append("Hybrid mode gives more options for body recomposition. Make sure programming matches recovery and your actual equipment access.")

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
        "recommendation_lines": recs,
    }


def build_transformation_status_report(user_id: str) -> str:
    _, user = get_or_create_user_memory(user_id)
    if not user.get("transformation_goal", {}):
        return "No transformation goal saved yet. Use `!architect set-transformation-goal 221.6 190 200 2026-06-01 lean-aesthetic`"
    s = compute_transformation_status(user_id)
    if not s:
        return "Transformation status unavailable."
    if not s.get("valid", False):
        return f"Transformation status error: {s.get('error', 'Unknown error')}"
    return "\n".join([
        "Architect Transformation Status:",
        f"- Goal type: {s.get('goal_type', 'Not set')}",
        f"- Current weight: {safe_float(s.get('current_weight')):.1f} lb",
        f"- Target range: {safe_float(s.get('target_low')):.1f} to {safe_float(s.get('target_high')):.1f} lb",
        f"- Target midpoint: {safe_float(s.get('midpoint_target')):.1f} lb",
        f"- Deadline: {s.get('deadline_text', 'Not set')}",
        f"- Days left: {safe_int(s.get('days_left'))}",
        f"- Weeks left: {safe_float(s.get('weeks_left')):.1f}",
        f"- Pounds to midpoint target: {safe_float(s.get('pounds_to_goal')):.1f} lb",
        f"- Required pace: {safe_float(s.get('pounds_per_week')):.2f} lb/week",
        f"- Pace status: {s.get('pace_status', 'Not set')}",
        f"- Current training mode: {s.get('current_mode', 'Not set')}",
        f"- Current phase: {s.get('current_phase', 'Not set')}",
        f"- Training days available: {safe_int(s.get('training_days'))}",
        f"- Resources: {s.get('resources', 'Not set')}",
        "",
        "Recommendations:",
        *[f"- {x}" for x in s.get("recommendation_lines", [])],
    ])


def build_fitness_adjustment_report(user_id: str) -> str:
    _, user = get_or_create_user_memory(user_id)
    fp = user.get("fitness_profile", {})
    tg = user.get("transformation_goal", {})
    ab = user.get("activity_baseline", {})
    status = compute_transformation_status(user_id)

    if not fp:
        return "No fitness profile saved yet. Use `!architect set-fitness-profile ...` first."
    if not tg:
        return "No transformation goal saved yet. Use `!architect set-transformation-goal ...` first."
    if not status or not status.get("valid", False):
        return f"Fitness adjustment unavailable: {status.get('error', 'Missing valid transformation data') if status else 'Missing transformation data'}"

    mode = fp.get("current_training_mode", "Not set")
    phase = fp.get("current_phase", "Not set")
    days = safe_int(fp.get("training_days_available"), 0)
    resources = fp.get("available_resources", "Not set")
    challenge = fp.get("current_challenge", "Not set")
    pace = status.get("pace_status", "Not set")
    ppw = safe_float(status.get("pounds_per_week"), 0)

    options, notes = [], []
    if pace == "Aggressive":
        options += [
            "Option A: Keep the deadline and tighten execution hard across nutrition, steps, recovery, and training consistency.",
            *(["Option B: Add 1 extra training day if recovery, schedule, and nutrition can actually support it."] if days < 6 else []),
            "Option C: Keep current training days but increase weekly calorie expenditure through structured cardio or higher daily movement.",
            "Option D: Extend the deadline slightly so the cut is more realistic and muscle retention improves.",
        ]
    elif pace == "Demanding":
        options += [
            "Option A: Stay at current days and improve compliance before increasing volume.",
            *(["Option B: Add 1 training day only if sleep and soreness remain controlled."] if days < 6 else []),
            "Option C: Tighten nutrition and keep daily activity more consistent.",
        ]
    elif pace == "Reasonable":
        options += [
            "Option A: Do not overcorrect. Keep the plan simple and sustainable.",
            "Option B: Use current structure and refine execution quality first.",
            "Option C: Increase output only if progress stalls for multiple weeks.",
        ]
    else:
        options += [
            "Option A: Reassess goal range and timeline together.",
            "Option B: Focus on body quality, strength, and consistency first.",
        ]

    if "gym" in str(resources).lower():
        notes.append("You now have gym access in your resource picture, so hybrid training has more upside.")
    else:
        notes.append("Your current resource profile still looks limited, so bodyweight and hybrid efficiency matter more than complexity.")

    if str(mode).lower() == "calisthenics":
        notes.append("Calisthenics remains excellent for body control and aesthetics, but gym access can increase progression options once ready.")
    elif str(mode).lower() == "hybrid":
        notes.append("Hybrid mode gives you the most flexibility right now, especially if your goal includes leaning out while preserving or rebuilding muscle.")

    if days >= 6:
        notes.append("You already have a high training frequency. More is not automatically better; recovery quality now matters a lot.")
    elif days <= 4:
        notes.append("Your current training frequency is modest. If the timeline is tight, an additional day may help if recovery is stable.")

    if ab:
        notes.append(f"Your current activity target is around {safe_float(ab.get('active_calories_daily')):.0f} active calories and {safe_float(ab.get('exercise_minutes_daily')):.0f} exercise minutes per day.")

    notes.append(f"Current challenge in system: {challenge}.")
    notes.append(f"Current pace requirement: {ppw:.2f} lb/week.")

    return "\n".join([
        "Architect Fitness Adjustment:",
        f"- Current mode: {mode}",
        f"- Current phase: {phase}",
        f"- Training days available: {days}",
        f"- Resources: {resources}",
        f"- Pace status: {pace}",
        f"- Required weekly pace: {ppw:.2f} lb/week",
        "",
        "Adjustment options:",
        *[f"- {x}" for x in options],
        "",
        "Intelligent notes:",
        *[f"- {x}" for x in notes],
    ])


def adapt_home_exercise_line(exercise: str, setup: dict) -> str:
    text = exercise
    lower = text.lower()
    if setup["home_bodyweight_only"]:
        replacements = [
            ("weighted or tempo push-ups", "Tempo Push-Ups or Standard Push-Ups"),
            ("incline push-ups or feet elevated push-ups", "Incline Push-Ups or Standard Push-Ups"),
            ("goblet squats or bodyweight tempo squats", "Bodyweight Tempo Squats or Pause Squats"),
            ("trx rows or doorframe rows", "Towel Rows on a sturdy anchor, Doorframe Rows if safe, or Superman Holds"),
            ("db rdl or backpack rdl", "Hip Hinge Tempo Good Mornings or Single-Leg Bodyweight RDL"),
            ("nordic negatives or banded ham curls", "Nordic Negatives with foot anchor or Hamstring Walkouts"),
            ("pike push-ups or db overhead press", "Pike Push-Ups"),
            ("db curl + hammer curl", "Isometric Towel Curls + Slow Negative Towel Curls"),
            ("bench dips or overhead triceps extension", "Bench Dips on a stable surface or Diamond Push-Ups"),
            ("pull-ups, band pulldowns, or inverted rows", "Doorframe Rows if safe, Towel Rows on a sturdy anchor, or Prone Y-T-W Raises"),
            ("kettlebell swings or fast bodyweight circuits", "Fast Bodyweight Circuits"),
            ("jump rope hiit or fast step-ups", "Fast Step-Ups or March-In-Place Sprints"),
            ("foam roll or mobility ball work", "Floor Mobility Flow"),
            ("bike ride 30-45 min or incline walk 30 min or outdoor walk", "Outdoor Walk 30-45 min or Marching Cardio"),
        ]
        for a, b in replacements:
            if a in lower:
                return text.lower().replace(a, b.lower()).title()
        return text

    if not setup["has_kettlebell"]:
        text = text.replace("Kettlebell Swings or ", "").replace("Goblet Squats or ", "")
    if not setup["has_dumbbells"]:
        text = text.replace("DB RDL or ", "").replace("DB Overhead Press or ", "").replace("DB Curl + Hammer Curl", "Towel Curls + Slow Negative Curls")
    if not setup["has_trx"]:
        text = text.replace("TRX Rows or ", "")
    if not setup["has_bands"]:
        text = text.replace("Banded Ham Curls", "Hamstring Walkouts").replace("Band Pulldowns, or ", "")
    if not setup["has_pullup_bar"]:
        text = text.replace("Pull-Ups, ", "").replace("Pull-Ups or ", "")
    return text


def get_adapted_exercise_list(user_id: str, day_name: str):
    block = WEEKLY_WORKOUT_LIBRARY.get(day_name)
    if not block:
        return []
    setup = build_training_setup_snapshot(user_id)
    items = block["gym"] if setup["has_gym"] else block["home"]
    return items if setup["has_gym"] else [adapt_home_exercise_line(x, setup) for x in items]


def get_body_fat_value(user_id: str):
    _, user = get_or_create_user_memory(user_id)
    return safe_float(user.get("body_baseline", {}).get("body_fat_percent"), 0)


def run_adjustment_engine(user_id: str):
    _, user = get_or_create_user_memory(user_id)
    baseline = user.get("body_baseline", {})
    body_goal = user.get("body_goal", {})
    transformation = user.get("transformation_goal", {})
    fitness_profile = user.get("fitness_profile", {})
    activity_baseline = user.get("activity_baseline", {})
    status = compute_transformation_status(user_id)
    setup = build_training_setup_snapshot(user_id)

    current_weight = estimate_current_weight(user_id)
    body_fat = get_body_fat_value(user_id)
    training_days = safe_int(fitness_profile.get("training_days_available"), 0)
    current_mode = fitness_profile.get("current_training_mode", "Not set")
    challenge = fitness_profile.get("current_challenge", "Not set")
    target_low = safe_float(transformation.get("target_weight_low_lb") or body_goal.get("target_weight_low_lb"), 0)
    target_high = safe_float(transformation.get("target_weight_high_lb") or body_goal.get("target_weight_high_lb"), 0)

    recent_activity = get_recent_activity_stats(user_id, 7)
    recent_workout_days = get_recent_workout_days(user_id, 7)

    recs, reasoning, workout_guidance, nutrition_guidance, cardio_guidance = [], [], [], [], []

    if not baseline:
        reasoning.append("Body baseline is still incomplete, so body-composition recommendations are less precise.")
    if not transformation:
        reasoning.append("Transformation goal is not fully set, so timeline analysis is limited.")
    if not fitness_profile:
        reasoning.append("Fitness profile is not fully set, so training recommendations use defaults.")

    if setup["home_bodyweight_only"]:
        workout_guidance += [
            "Current build mode is true bodyweight-only. Keep programming simple, repeatable, and recovery-aware.",
            "Primary tools right now are push-up variations, squats, lunges, tempo work, pauses, core circuits, jumps, and walking/cardio.",
        ]
    else:
        if setup["has_kettlebell"]:
            workout_guidance.append("Kettlebell is available, so Architect can unlock goblet squats, swings, carries, and floor-press accessories.")
        if setup["has_weighted_vest"]:
            workout_guidance.append("Weighted vest is available, so Architect can load push-ups, squats, lunges, and walks without redesigning the base plan.")
        if setup["has_gym"]:
            workout_guidance.append("Gym access is live, so hybrid progression can now include machines, barbells, cables, and vertical pulling.")

    if current_weight > 0 and target_low > 0 and target_high > 0:
        midpoint = (target_low + target_high) / 2
        delta = current_weight - midpoint
        reasoning.append(f"Current estimated weight is {current_weight:.1f} lb and midpoint target is {midpoint:.1f} lb.")
        reasoning.append(
            f"You are roughly {delta:.1f} lb above your midpoint physique target."
            if delta > 0 else
            "You are already near or below your midpoint target range, so body quality and muscle retention matter more than scale aggression."
        )

    if body_fat > 0:
        reasoning.append(f"Current saved body-fat baseline is {body_fat:.1f}%.")

    if status and status.get("valid", False):
        pace = status.get("pace_status", "Not set")
        ppw = safe_float(status.get("pounds_per_week"), 0)
        reasoning.append(f"Timeline pace status is {pace} at about {ppw:.2f} lb/week.")

        if pace == "Aggressive":
            recs += ["Add cardio.", "Adjust calories."]
            recs.append("Increase training days." if training_days < 5 else "Maintain current training days and tighten execution.")
            cardio_guidance += [
                "Add 2-4 low-impact cardio sessions per week, 20-35 minutes each.",
                "Favor incline walk, outdoor walk, bike, pool laps, or step-up intervals over random exhaustion work.",
            ]
            cal = estimate_calorie_adjustment_from_pace(min(ppw, 2.0))
            if cal > 0:
                nutrition_guidance.append(f"Use tighter food control and consider a daily deficit around {cal} to {cal + 150} kcal if recovery stays intact.")
            nutrition_guidance.append("Keep protein high and avoid crashing calories so hard that push-up volume and recovery collapse.")
        elif pace == "Demanding":
            recs.append("Adjust calories.")
            if recent_activity["avg_steps"] < 7000 or recent_activity["avg_exercise_minutes"] < 35:
                recs.append("Add cardio.")
                cardio_guidance.append("Add 2-3 easy cardio sessions per week or raise daily step count.")
            recs.append("Increase training days." if training_days < 5 else "Maintain current plan with tighter compliance.")
            cal = estimate_calorie_adjustment_from_pace(max(ppw - 0.25, 0.5))
            if cal > 0:
                nutrition_guidance.append(f"Slightly tighten calories by about {max(200, cal - 100)} to {cal} kcal/day before adding unnecessary complexity.")
        elif pace == "Reasonable":
            recs.append("Maintain current plan.")
            reasoning.append("Timeline is still realistic, so consistency matters more than dramatic changes.")
            if recent_activity["avg_steps"] < 6000 and not setup["has_gym"]:
                recs.append("Add light cardio.")
                cardio_guidance.append("Add a simple walk block most days to improve expenditure without hurting bodyweight recovery.")
            nutrition_guidance.append("Keep calories controlled and repeatable instead of making aggressive changes.")
        elif pace == "At target":
            recs.append("Maintain current plan.")
            nutrition_guidance.append("Shift focus toward body quality, muscle retention, recovery, and clean execution.")
        else:
            recs.append("Reassess goal timeline.")
            nutrition_guidance.append("Recheck target date and desired physique rate before making hard training changes.")
    else:
        recs.append("Set transformation goal data.")

    if training_days <= 0:
        recs.append("Set training days clearly.")
    elif training_days <= 3:
        reasoning.append(f"Current training frequency is {training_days} day(s) per week, which is low for a June body-composition push.")
        recs.append("Increase training days.")
        workout_guidance.append("Move toward 4-5 training days if recovery and schedule allow.")
    elif training_days >= 6:
        reasoning.append(f"Current training frequency is already {training_days} day(s) per week.")
        workout_guidance.append("Do not add more training days blindly. Protect joints, sleep, and push-up quality.")
    else:
        reasoning.append(f"Current training frequency is {training_days} day(s) per week, which is workable.")

    if recent_workout_days == 0 and training_days > 0:
        reasoning.append("No recent workout logs were found in the last 7 days.")
        recs.append("Improve training consistency.")
    elif recent_workout_days > 0:
        reasoning.append(f"Recent logged workout days in the last week: {recent_workout_days}.")

    if activity_baseline:
        base_cals = safe_float(activity_baseline.get("active_calories_daily"), 0)
        base_min = safe_float(activity_baseline.get("exercise_minutes_daily"), 0)
        if recent_activity["sessions"] > 0:
            reasoning.append(f"Recent activity average is {recent_activity['avg_active_calories']:.0f} active calories and {recent_activity['avg_exercise_minutes']:.0f} exercise minutes per session.")
            if base_cals > 0 and recent_activity["avg_active_calories"] < base_cals * 0.7:
                recs.append("Increase activity output.")
            if base_min > 0 and recent_activity["avg_exercise_minutes"] < base_min * 0.7:
                recs.append("Add cardio.")
        else:
            reasoning.append("No recent activity logs were found for the last 7 days.")

    if str(current_mode).lower() == "calisthenics":
        workout_guidance.append("Calisthenics rebuild stays the base. Progress through volume quality, tempo, pauses, leverage, and density.")
    elif str(current_mode).lower() == "hybrid":
        workout_guidance.append("Hybrid mode is fine, but right now it should still obey your actual equipment reality instead of fantasy programming.")
    else:
        workout_guidance.append("Keep the training identity simple: bodyweight aesthetics first, hybrid later when tools exist.")

    if "300" in str(challenge):
        workout_guidance += [
            "The 300 push-up challenge should be spread through the day in submaximal sets, not forced into all-out burnout blocks.",
            "On harder lower-body or conditioning days, keep push-up execution cleaner and avoid grinding every set to failure.",
        ]

    deduped = []
    seen = set()
    for x in recs or ["Maintain current plan."]:
        k = x.lower()
        if k not in seen:
            seen.add(k)
            deduped.append(x)

    analysis = {
        "generated_at": utc_now_iso(),
        "current_weight": current_weight,
        "body_fat": body_fat,
        "training_days": training_days,
        "goal_type": transformation.get("goal_type", "Not set"),
        "deadline_date": transformation.get("deadline_date", ""),
        "recent_activity": recent_activity,
        "recent_workout_days": recent_workout_days,
        "setup": setup,
        "recommendations": deduped,
        "reasoning": reasoning,
        "workout_guidance": workout_guidance,
        "nutrition_guidance": nutrition_guidance,
        "cardio_guidance": cardio_guidance,
        "status": status or {},
    }

    _, user = get_or_create_user_memory(user_id)
    ae = user.get("adjustment_engine", {})
    ae["last_analysis"] = analysis
    ae["last_updated"] = utc_now_iso()
    user["adjustment_engine"] = ae
    save_user_memory(user_id, user)
    return analysis


def build_adjustment_engine_report(user_id: str) -> str:
    a = run_adjustment_engine(user_id)
    s = a.get("status", {})
    setup = a.get("setup", {})
    return "\n".join([
        "Architect Adjustment Engine:",
        f"- Current estimated weight: {safe_float(a.get('current_weight')):.1f} lb",
        f"- Current body fat baseline: {safe_float(a.get('body_fat')):.1f}%",
        f"- Training days available: {safe_int(a.get('training_days'))}",
        f"- Deadline: {a.get('deadline_date', 'Not set')}",
        f"- Goal type: {a.get('goal_type', 'Not set')}",
        f"- Pace status: {s.get('pace_status', 'Not set') if isinstance(s, dict) else 'Not set'}",
        f"- Days left: {safe_int(s.get('days_left')) if isinstance(s, dict) else 0}",
        f"- Required weekly pace: {safe_float(s.get('pounds_per_week')) if isinstance(s, dict) else 0:.2f} lb/week",
        f"- Recent workout days logged (7d): {safe_int(a.get('recent_workout_days'))}",
        f"- Recent activity sessions (7d): {safe_int(a.get('recent_activity', {}).get('sessions'))}",
        f"- Avg active calories/session (7d): {safe_float(a.get('recent_activity', {}).get('avg_active_calories')):.0f}",
        f"- Avg exercise minutes/session (7d): {safe_float(a.get('recent_activity', {}).get('avg_exercise_minutes')):.0f}",
        f"- Avg steps/session (7d): {safe_float(a.get('recent_activity', {}).get('avg_steps')):.0f}",
        "",
        "Equipment + environment:",
        f"- Build mode: {setup.get('mode_label', 'unknown')}",
        f"- Home bodyweight only: {'Yes' if setup.get('home_bodyweight_only') else 'No'}",
        f"- Gym access: {'Yes' if setup.get('has_gym') else 'No'}",
        f"- Kettlebell: {'Yes' if setup.get('has_kettlebell') else 'No'}",
        f"- Weighted vest: {'Yes' if setup.get('has_weighted_vest') else 'No'}",
        f"- Pull-up bar: {'Yes' if setup.get('has_pullup_bar') else 'No'}",
        f"- Bands: {'Yes' if setup.get('has_bands') else 'No'}",
        f"- Dumbbells: {'Yes' if setup.get('has_dumbbells') else 'No'}",
        "",
        "Recommendations:",
        *[f"- {x}" for x in a.get("recommendations", [])],
        "",
        "Reasoning:",
        *[f"- {x}" for x in a.get("reasoning", [])] or ["- Not enough reasoning data yet."],
        "",
        "Workout guidance:",
        *[f"- {x}" for x in a.get("workout_guidance", [])] or ["- No workout guidance yet."],
        "",
        "Nutrition guidance:",
        *[f"- {x}" for x in a.get("nutrition_guidance", [])] or ["- No nutrition guidance yet."],
        "",
        "Cardio guidance:",
        *[f"- {x}" for x in a.get("cardio_guidance", [])] or ["- No cardio guidance yet."],
    ])


def build_weekly_workout_plan(user_id: str) -> str:
    phase = get_workout_phase_data(user_id)
    setup = build_training_setup_snapshot(user_id)
    lines = [
        "Architect Weekly Workout Plan:",
        f"- Workout phase: {phase.get('workout_phase', 'not set')}",
        f"- Planned phase duration: {safe_int(phase.get('phase_duration_weeks'))} week(s)",
        f"- Build mode used today: {setup['mode_label']}",
        f"- Extra equipment: {build_equipment_modifier_text(user_id)}",
        "",
    ]
    for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
        block = WEEKLY_WORKOUT_LIBRARY[day]
        lines.append(f"{day.title()} - {block['title']}")
        lines += [f"- {x}" for x in get_adapted_exercise_list(user_id, day)]
        lines.append("")
    if setup["home_bodyweight_only"]:
        lines += [
            "Adjustment Engine note:",
            "- This plan is locked to true bodyweight-only reality right now.",
            "- As soon as you add kettlebell, vest, bands, pull-up bar, dumbbells, or gym access, Architect can scale the same structure upward.",
        ]
    return "\n".join(lines).strip()


def build_today_workout(user_id: str) -> str:
    day = dr_now().strftime("%A").lower()
    block = WEEKLY_WORKOUT_LIBRARY.get(day)
    if not block:
        return "I couldn't determine today's workout."
    phase = get_workout_phase_data(user_id)
    setup = build_training_setup_snapshot(user_id)
    lines = [
        "Architect Today Workout:",
        f"- Day: {day.title()}",
        f"- Session: {block['title']}",
        f"- Focus: {block['focus']}",
        f"- Workout phase: {phase.get('workout_phase', 'not set')}",
        f"- Phase duration: {safe_int(phase.get('phase_duration_weeks'))} week(s)",
        f"- Build mode used: {setup['mode_label']}",
        f"- Extra equipment: {build_equipment_modifier_text(user_id)}",
        "",
        "Today's exercises:",
        *[f"- {x}" for x in get_adapted_exercise_list(user_id, day)],
        "",
        "Why this session:",
        "- It matches your weekly structure from the hybrid manual.",
        "- It keeps daily intention high instead of guessing what to train.",
        "- It lets Architect adapt the session around your current access and tools.",
    ]
    if setup["home_bodyweight_only"]:
        lines.append("- Adjustment Engine confirms this session is bodyweight-only and does not assume gear you do not currently have.")
    return "\n".join(lines)


def build_pushup_plan(user_id: str, total_target: int = 300, max_set: int = 25) -> str:
    total_target = total_target if total_target > 0 else 300
    safe_max = clamp_int(max_set if max_set > 0 else 25, 8, 60)
    setup = build_training_setup_snapshot(user_id)

    def set_plan(target, set_size):
        full_sets, rem = divmod(target, set_size)
        return f"{full_sets} sets of {set_size} = {target}" if rem == 0 else f"{full_sets} sets of {set_size} + 1 finisher set of {rem} = {target}"

    s1 = max(8, int(round(safe_max * 0.60)))
    s2 = max(10, int(round(safe_max * 0.75)))
    s3 = min(safe_max, max(12, int(round(safe_max * 0.90))))

    freq = "Spread the volume across the full day in 6-12 mini sessions."
    if safe_max >= 35:
        freq = "You can use slightly larger clusters, but still keep most sets submaximal so the daily target stays repeatable."
    elif safe_max <= 20:
        freq = "Keep the sets smaller and cleaner so the challenge builds work capacity instead of turning into ugly grinders."

    lines = [
        "Architect Push-Up Plan:",
        f"- Daily target: {total_target}",
        f"- Current max set: {max_set}",
        f"- Intelligent planning max used: {safe_max}",
        "",
        "Recommended options:",
        f"- Option 1 (most sustainable): {set_plan(total_target, s1)}",
        f"- Option 2 (balanced): {set_plan(total_target, s2)}",
        f"- Option 3 (denser): {set_plan(total_target, s3)}",
        "- Option 4: EMOM style — 10 to 20 reps every hour across the day until target is complete",
        "",
        "Rest guidance:",
        f"- Smaller sets ({s1}ish): rest 30 to 60 sec",
        f"- Moderate sets ({s2}ish): rest 45 to 90 sec",
        f"- Larger sets ({s3}ish): rest 75 to 120 sec",
        "",
        "Reasoning:",
        "- Frequent submaximal sets let you accumulate volume without frying your shoulders or triceps too early.",
        "- This builds work capacity, muscular endurance, movement quality, and consistency.",
        "- The goal is to dominate total daily volume while staying fresh enough to repeat it.",
        f"- {freq}",
    ]
    if setup["home_bodyweight_only"]:
        lines.append("- Current setup note: this challenge fits your true bodyweight-only rebuild phase well.")
    if setup["has_weighted_vest"]:
        lines.append("- Weighted vest note: use the vest only on a smaller portion of the total volume, not all 300.")
    if setup["has_kettlebell"]:
        lines.append("- Kettlebell note: use kettlebell floor press or swings as accessory work, not as a replacement for the daily push-up target.")
    return "\n".join(lines)


def log_weight(user_id: str, value: str):
    append_user_list(user_id, "weights", {"value": value, "timestamp": utc_now_iso()})


def log_goal(user_id: str, goal: str):
    append_user_list(user_id, "goals", {"text": goal, "timestamp": utc_now_iso()})


def log_habit(user_id: str, habit_text: str):
    append_user_list(user_id, "habits", {"text": habit_text, "timestamp": utc_now_iso()})


def log_checkin(user_id: str, energy: str, motivation: str, focus: str):
    append_user_list(user_id, "checkins", {
        "energy": energy,
        "motivation": motivation,
        "focus": focus,
        "timestamp": utc_now_iso(),
    })


def log_note(user_id: str, note: str):
    append_user_list(user_id, "notes", {"text": note, "timestamp": utc_now_iso()})


def log_idea(user_id: str, idea: str):
    append_user_list(user_id, "ideas", {"text": idea, "timestamp": utc_now_iso()})


def log_pnl(user_id: str, pnl_value: float):
    append_user_list(user_id, "pnl_logs", {"value": pnl_value, "date": today_dr(), "timestamp": utc_now_iso()})


def log_win(user_id: str, text: str):
    append_user_list(user_id, "wins", {"text": text, "date": today_dr(), "timestamp": utc_now_iso()})


def log_mistake(user_id: str, text: str):
    append_user_list(user_id, "mistakes", {"text": text, "date": today_dr(), "timestamp": utc_now_iso()})


def log_sleep(user_id: str, hours: float):
    append_user_list(user_id, "sleep_logs", {"hours": hours, "date": today_dr(), "timestamp": utc_now_iso()})


def log_mood(user_id: str, score: float):
    append_user_list(user_id, "mood_logs", {"score": score, "date": today_dr(), "timestamp": utc_now_iso()})


def log_focus_score(user_id: str, score: float):
    append_user_list(user_id, "focus_logs", {"score": score, "date": today_dr(), "timestamp": utc_now_iso()})


def log_workout(user_id: str, workout_text: str):
    append_user_list(user_id, "workouts", {"text": workout_text, "date": today_dr(), "timestamp": utc_now_iso()})


def set_week_mode(user_id: str, mode: str):
    _, user = get_or_create_user_memory(user_id)
    ctx = user["context"]
    ctx["week_mode"] = mode
    update_user_section(user_id, "context", ctx)


def set_week_focus(user_id: str, focus_items):
    _, user = get_or_create_user_memory(user_id)
    ctx = user["context"]
    ctx["week_focus"] = focus_items
    update_user_section(user_id, "context", ctx)


def set_training_mode(user_id: str, mode: str):
    _, user = get_or_create_user_memory(user_id)
    ctx = user["context"]
    ctx["training_mode"] = mode
    update_user_section(user_id, "context", ctx)


def set_nutrition_mode(user_id: str, mode: str):
    _, user = get_or_create_user_memory(user_id)
    ctx = user["context"]
    ctx["nutrition_mode"] = mode
    update_user_section(user_id, "context", ctx)


def set_daily_goal(user_id: str, goal_text: str):
    _, user = get_or_create_user_memory(user_id)
    ctx = user["context"]
    ctx.setdefault("daily_goals", []).append({"text": goal_text, "timestamp": utc_now_iso()})
    update_user_section(user_id, "context", ctx)


def set_watchlist(user_id: str, tickers):
    _, user = get_or_create_user_memory(user_id)
    ctx = user["context"]
    ctx["watchlist"] = tickers
    update_user_section(user_id, "context", ctx)


def show_notes(user_id: str):
    _, user = get_or_create_user_memory(user_id)
    notes = user.get("notes", [])
    return "No notes saved yet." if not notes else "Saved notes:\n" + "\n".join(f"- {x['text']}" for x in notes[-10:])


def show_ideas(user_id: str):
    _, user = get_or_create_user_memory(user_id)
    ideas = user.get("ideas", [])
    return "No ideas saved yet." if not ideas else "Saved ideas:\n" + "\n".join(f"- {x['text']}" for x in ideas[-10:])


def build_knowledge_report(user_id: str):
    _, user = get_or_create_user_memory(user_id)
    notes, ideas = user.get("notes", []), user.get("ideas", [])
    lines = [f"Knowledge System Report:\n- Notes saved: {len(notes)}\n- Ideas saved: {len(ideas)}"]
    if notes:
        lines.append(f"\nLatest note:\n- {notes[-1]['text']}")
    if ideas:
        lines.append(f"\nLatest idea:\n- {ideas[-1]['text']}")
    return "".join(lines)


def build_pnl_report(user_id: str):
    _, user = get_or_create_user_memory(user_id)
    logs = user.get("pnl_logs", [])
    if not logs:
        return "No PnL logs saved yet. Use `!architect log-pnl 250`"
    total = sum(safe_float(x["value"]) for x in logs)
    avg = total / len(logs)
    green = sum(1 for x in logs if safe_float(x["value"]) > 0)
    red = sum(1 for x in logs if safe_float(x["value"]) < 0)
    flat = sum(1 for x in logs if safe_float(x["value"]) == 0)
    best = max(logs, key=lambda x: safe_float(x["value"]))
    worst = min(logs, key=lambda x: safe_float(x["value"]))
    today_total = sum(safe_float(x["value"]) for x in logs if x.get("date") == today_dr())
    return "\n".join([
        "PnL Report:",
        f"- Days logged: {len(logs)}",
        f"- Today: {today_total:.2f}",
        f"- Total PnL: {total:.2f}",
        f"- Average day: {avg:.2f}",
        f"- Green days: {green}",
        f"- Red days: {red}",
        f"- Flat days: {flat}",
        f"- Best day: {safe_float(best['value']):.2f} ({best['date']})",
        f"- Worst day: {safe_float(worst['value']):.2f} ({worst['date']})",
    ])


def build_daily_report(user_id: str):
    _, user = get_or_create_user_memory(user_id)
    trades = get_trades().get(user_id, [])
    today = today_dr()

    def rows(name, key="timestamp", prefix=None):
        arr = user.get(name, [])
        if key == "date":
            return [x for x in arr if x.get(key) == today]
        return [x for x in arr if str(x.get(key, ""))[:10] == today]

    habits_today = rows("habits")
    checkins_today = rows("checkins")
    notes_today = rows("notes")
    ideas_today = rows("ideas")
    pnl_today = rows("pnl_logs", "date")
    wins_today = rows("wins", "date")
    mistakes_today = rows("mistakes", "date")
    sleep_today = rows("sleep_logs", "date")
    mood_today = rows("mood_logs", "date")
    focus_today = rows("focus_logs", "date")
    workouts_today = rows("workouts", "date")
    activity_today = rows("activity_logs", "date")
    trades_today = [x for x in trades if str(x.get("timestamp", ""))[:10] == today]

    latest_checkin = checkins_today[-1] if checkins_today else {}
    latest_checkin_text = (
        f"Energy {latest_checkin.get('energy')} | Motivation {latest_checkin.get('motivation')} | Focus {latest_checkin.get('focus')}"
        if latest_checkin else "No check-in today"
    )

    return "\n".join([
        "Architect Daily System Report:",
        f"- Date: {today}",
        f"- Sleep: {sleep_today[-1]['hours']} hrs" if sleep_today else "- Sleep: No sleep logged",
        f"- Mood: {mood_today[-1]['score']}" if mood_today else "- Mood: No mood logged",
        f"- Focus: {focus_today[-1]['score']}" if focus_today else "- Focus: No focus logged",
        f"- Check-in: {latest_checkin_text}",
        f"- Habits logged today: {len(habits_today)}",
        f"- Workouts logged today: {len(workouts_today)}",
        f"- Activity sessions today: {len(activity_today)}",
        f"- Activity calories today: {sum(safe_float(x.get('active_calories')) for x in activity_today):.0f}",
        f"- Activity minutes today: {sum(safe_float(x.get('exercise_minutes')) for x in activity_today):.0f}",
        f"- Notes saved today: {len(notes_today)}",
        f"- Ideas saved today: {len(ideas_today)}",
        f"- Wins logged today: {len(wins_today)}",
        f"- Mistakes logged today: {len(mistakes_today)}",
        f"- Trades logged today: {len(trades_today)}",
        f"- PnL today: {sum(safe_float(x.get('value')) for x in pnl_today):.2f}",
    ])


def build_life_report(user_id: str):
    _, user = get_or_create_user_memory(user_id)
    sleep_logs = user.get("sleep_logs", [])
    mood_logs = user.get("mood_logs", [])
    focus_logs = user.get("focus_logs", [])
    workouts = user.get("workouts", [])
    habits = user.get("habits", [])
    notes = user.get("notes", [])
    ideas = user.get("ideas", [])
    body_baseline = user.get("body_baseline", {})
    body_goal = user.get("body_goal", {})
    transformation = user.get("transformation_goal", {})
    fitness_profile = user.get("fitness_profile", {})
    activity_baseline = user.get("activity_baseline", {})
    activity_logs = user.get("activity_logs", [])

    if not any([sleep_logs, mood_logs, focus_logs, workouts, body_baseline, body_goal, transformation, fitness_profile, activity_baseline, activity_logs]):
        return "No life performance logs yet. Use `!architect log-sleep`, `!architect log-mood`, `!architect log-focus`, `!architect log-workout`, `!architect set-body-baseline`, `!architect set-body-goal`, `!architect set-fitness-profile`, and `!architect set-activity-baseline`."

    avg = lambda arr, key: sum(safe_float(x.get(key)) for x in arr) / len(arr) if arr else 0
    lines = ["Architect Life Performance Report:"]
    if body_baseline:
        lines += [
            f"- Baseline weight: {safe_float(body_baseline.get('weight_lb')):.1f} lb",
            f"- Baseline body fat: {safe_float(body_baseline.get('body_fat_percent')):.1f}%",
            f"- Baseline BMI: {safe_float(body_baseline.get('bmi')):.1f}",
        ]
    if body_goal:
        lines.append(f"- Body goal: {safe_float(body_goal.get('target_weight_low_lb')):.1f} to {safe_float(body_goal.get('target_weight_high_lb')):.1f} lb | BF {safe_float(body_goal.get('target_body_fat_percent')):.1f}%")
    if fitness_profile:
        lines += [
            f"- Current training mode: {fitness_profile.get('current_training_mode', 'Not set')}",
            f"- Current phase: {fitness_profile.get('current_phase', 'Not set')}",
            f"- Training days available: {safe_int(fitness_profile.get('training_days_available'))}",
        ]
    if activity_baseline:
        lines += [
            f"- Activity baseline calories: {safe_float(activity_baseline.get('active_calories_daily')):.0f}",
            f"- Activity baseline exercise minutes: {safe_float(activity_baseline.get('exercise_minutes_daily')):.0f}",
            f"- Activity baseline steps: {safe_int(activity_baseline.get('steps_daily'))}",
        ]
    lines += [
        f"- Sleep logs: {len(sleep_logs)}",
        f"- Average sleep: {avg(sleep_logs, 'hours'):.2f} hrs",
        f"- Mood logs: {len(mood_logs)}",
        f"- Average mood: {avg(mood_logs, 'score'):.2f}",
        f"- Focus logs: {len(focus_logs)}",
        f"- Average focus: {avg(focus_logs, 'score'):.2f}",
        f"- Workouts logged: {len(workouts)}",
        f"- Activity sessions logged: {len(activity_logs)}",
        f"- Average activity calories: {avg(activity_logs, 'active_calories'):.0f}",
        f"- Average activity minutes: {avg(activity_logs, 'exercise_minutes'):.0f}",
        f"- Habits logged: {len(habits)}",
        f"- Notes captured: {len(notes)}",
        f"- Ideas captured: {len(ideas)}",
    ]
    return "\n".join(lines)


def build_week_plan(user_id: str):
    _, user = get_or_create_user_memory(user_id)
    ctx, fp, ab = user.get("context", {}), user.get("fitness_profile", {}), user.get("activity_baseline", {})
    goals = ctx.get("daily_goals", [])
    return "\n".join([
        "Architect Week Plan:",
        f"- Week mode: {ctx.get('week_mode', 'Not set')}",
        f"- Week focus: {', '.join(ctx.get('week_focus', [])) if ctx.get('week_focus') else 'Not set'}",
        f"- Training mode: {ctx.get('training_mode', 'Not set')}",
        f"- Nutrition mode: {ctx.get('nutrition_mode', 'Not set')}",
        *([
            f"- Current phase: {fp.get('current_phase', 'Not set')}",
            f"- Training days available: {safe_int(fp.get('training_days_available'))}",
            f"- Current challenge: {fp.get('current_challenge', 'Not set')}",
        ] if fp else []),
        *([
            f"- Activity target calories: {safe_float(ab.get('active_calories_daily')):.0f}",
            f"- Activity target exercise minutes: {safe_float(ab.get('exercise_minutes_daily')):.0f}",
        ] if ab else []),
        f"- Watchlist: {', '.join(ctx.get('watchlist', [])) if ctx.get('watchlist') else 'Not set'}",
        f"- Latest daily goal: {goals[-1]['text'] if goals else 'No daily goal set'}",
    ])


def build_morning_brief(user_id: str):
    _, user = get_or_create_user_memory(user_id)
    ctx = user.get("context", {})
    body_baseline = user.get("body_baseline", {})
    body_goal = user.get("body_goal", {})
    fitness_profile = user.get("fitness_profile", {})
    transformation_goal = user.get("transformation_goal", {})
    activity_baseline = user.get("activity_baseline", {})
    today = today_dr()
    pretty = dr_now().strftime("%A, %B %d, %Y")

    def latest_or_today(name):
        arr = user.get(name, [])
        today_arr = [x for x in arr if x.get("date") == today]
        return (today_arr or arr[-1:])[-1] if (today_arr or arr[-1:]) else None

    sleep = latest_or_today("sleep_logs")
    mood = latest_or_today("mood_logs")
    focus = latest_or_today("focus_logs")
    activity_today = [x for x in user.get("activity_logs", []) if x.get("date") == today]
    phase = get_workout_phase_data(user_id)
    today_name = dr_now().strftime("%A").lower()
    block = WEEKLY_WORKOUT_LIBRARY.get(today_name)
    training_mode = str(ctx.get("training_mode", "")).lower()
    if training_mode == "calisthenics":
        recommendation = "Training mode is calisthenics. Get your volume done early and keep nutrition aligned with recovery."
    elif training_mode == "hybrid":
        recommendation = "Training mode is hybrid. Balance strength, conditioning, and recovery without losing consistency."
    else:
        recommendation = "Stay disciplined, execute the plan, and log your data."

    goals = ctx.get("daily_goals", [])
    lines = [
        "Architect Morning Brief:",
        f"- Date: {pretty}",
        *( [f"- Body baseline: {safe_float(body_baseline.get('weight_lb')):.1f} lb | BF {safe_float(body_baseline.get('body_fat_percent')):.1f}% | BMI {safe_float(body_baseline.get('bmi')):.1f}"] if body_baseline else [] ),
        *( [f"- Body goal: {safe_float(body_goal.get('target_weight_low_lb')):.1f} to {safe_float(body_goal.get('target_weight_high_lb')):.1f} lb | BF {safe_float(body_goal.get('target_body_fat_percent')):.1f}%"] if body_goal else [] ),
        *( [
            f"- Current phase: {fitness_profile.get('current_phase', 'Not set')}",
            f"- Fitness mode: {fitness_profile.get('current_training_mode', 'Not set')}",
            f"- Current challenge: {fitness_profile.get('current_challenge', 'Not set')}",
        ] if fitness_profile else [] ),
        *( [f"- Transformation deadline: {transformation_goal.get('deadline_date', 'Not set')}"] if transformation_goal else [] ),
        *( [f"- Activity baseline: {safe_float(activity_baseline.get('active_calories_daily')):.0f} cal | {safe_float(activity_baseline.get('exercise_minutes_daily')):.0f} min | {safe_int(activity_baseline.get('steps_daily'))} steps"] if activity_baseline else [] ),
        *( [f"- Activity today: {sum(safe_float(x.get('active_calories')) for x in activity_today):.0f} cal | {sum(safe_float(x.get('exercise_minutes')) for x in activity_today):.0f} min | {sum(safe_int(x.get('steps')) for x in activity_today)} steps"] if activity_today else [] ),
        *( [f"- Workout engine phase: {phase.get('workout_phase')}"] if phase.get("workout_phase") else [] ),
        *( [f"- Today's workout: {block['title']}"] if block else [] ),
        f"- Week mode: {ctx.get('week_mode', 'Not set')}",
        f"- Week focus: {', '.join(ctx.get('week_focus', [])) if ctx.get('week_focus') else 'Not set'}",
        f"- Training mode: {ctx.get('training_mode', 'Not set')}",
        f"- Nutrition mode: {ctx.get('nutrition_mode', 'Not set')}",
        f"- Daily goal: {goals[-1]['text'] if goals else 'No daily goal set'}",
        f"- Watchlist: {', '.join(ctx.get('watchlist', [])) if ctx.get('watchlist') else 'Not set'}",
        f"- Sleep: {sleep['hours']} hrs" if sleep else "- Sleep: Not logged",
        f"- Mood: {mood['score']}" if mood else "- Mood: Not logged",
        f"- Focus: {focus['score']}" if focus else "- Focus: Not logged",
        f"- Recommendation: {recommendation}",
    ]
    return "\n".join(lines)


def log_trade_raw(user_id: str, raw_trade: str):
    trades = get_trades()
    arr = trades.get(user_id, [])
    arr.append({"type": "raw_review", "raw": raw_trade, "timestamp": utc_now_iso()})
    trades[user_id] = arr
    save_trades(trades)


def log_trade_structured(user_id: str, instrument: str, entry: float, stop: float, target: float, setup: str, exit_price: float):
    risk_pts = abs(entry - stop)
    target_pts = abs(target - entry)
    result_pts = exit_price - entry
    planned_r = target_pts / risk_pts if risk_pts else 0
    realized_r = result_pts / risk_pts if risk_pts else 0

    trades = get_trades()
    arr = trades.get(user_id, [])
    arr.append({
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
    trades[user_id] = arr
    save_trades(trades)
    return {"risk_pts": risk_pts, "target_pts": target_pts, "result_pts": result_pts, "planned_r": planned_r, "realized_r": realized_r}


def get_structured_trades(user_id: str):
    return [x for x in get_trades().get(user_id, []) if x.get("type") == "structured"]


def build_trade_stats(user_id: str) -> str:
    structured = get_structured_trades(user_id)
    if not structured:
        return "No structured trades logged yet. Use `!architect trade-log MNQ 18450 18420 18520 breakout_retest 18515`"
    total = len(structured)
    wins = sum(1 for t in structured if safe_float(t.get("result_pts")) > 0)
    losses = sum(1 for t in structured if safe_float(t.get("result_pts")) < 0)
    breakeven = total - wins - losses
    avg_result = sum(safe_float(t.get("result_pts")) for t in structured) / total
    avg_realized_r = sum(safe_float(t.get("realized_r")) for t in structured) / total
    avg_planned_r = sum(safe_float(t.get("planned_r")) for t in structured) / total
    setup_counts = {}
    for t in structured:
        setup_counts[t.get("setup", "unknown")] = setup_counts.get(t.get("setup", "unknown"), 0) + 1
    best_setup = max(setup_counts, key=setup_counts.get) if setup_counts else "N/A"
    return "\n".join([
        "Trading stats:",
        f"- Total structured trades: {total}",
        f"- Wins: {wins}",
        f"- Losses: {losses}",
        f"- Breakeven: {breakeven}",
        f"- Win rate: {(wins / total) * 100:.1f}%",
        f"- Average result (pts): {avg_result:.2f}",
        f"- Average realized R: {avg_realized_r:.2f}",
        f"- Average planned R: {avg_planned_r:.2f}",
        f"- Most used setup: {best_setup}",
    ])


def build_dashboard(user_id: str) -> str:
    structured = get_structured_trades(user_id)
    if not structured:
        return "No structured trades logged yet. Use `!architect trade-log MNQ 18450 18420 18520 breakout_retest 18515`"
    total = len(structured)
    wins = sum(1 for t in structured if safe_float(t.get("result_pts")) > 0)
    losses = sum(1 for t in structured if safe_float(t.get("result_pts")) < 0)
    breakeven = total - wins - losses
    total_points = sum(safe_float(t.get("result_pts")) for t in structured)
    total_realized_r = sum(safe_float(t.get("realized_r")) for t in structured)
    avg_result = total_points / total
    avg_realized_r = total_realized_r / total
    avg_planned_r = sum(safe_float(t.get("planned_r")) for t in structured) / total
    win_rate = (wins / total) * 100
    best_trade = max(structured, key=lambda t: safe_float(t.get("result_pts")))
    worst_trade = min(structured, key=lambda t: safe_float(t.get("result_pts")))
    setup_counts = {}
    for t in structured:
        setup_counts[t.get("setup", "unknown")] = setup_counts.get(t.get("setup", "unknown"), 0) + 1
    best_setup = max(setup_counts, key=setup_counts.get) if setup_counts else "N/A"
    return "\n".join([
        "Architect Trading Dashboard:",
        f"- Total structured trades: {total}",
        f"- Wins: {wins}",
        f"- Losses: {losses}",
        f"- Breakeven: {breakeven}",
        f"- Win rate: {win_rate:.1f}%",
        f"- Total points: {total_points:.2f}",
        f"- Total realized R: {total_realized_r:.2f}",
        f"- Average result (pts): {avg_result:.2f}",
        f"- Average realized R: {avg_realized_r:.2f}",
        f"- Average planned R: {avg_planned_r:.2f}",
        f"- Most used setup: {best_setup}",
        f"- Best trade: {best_trade.get('instrument', 'N/A')} | {best_trade.get('setup', 'N/A')} | {safe_float(best_trade.get('result_pts')):.2f} pts | {safe_float(best_trade.get('realized_r')):.2f}R",
        f"- Worst trade: {worst_trade.get('instrument', 'N/A')} | {worst_trade.get('setup', 'N/A')} | {safe_float(worst_trade.get('result_pts')):.2f} pts | {safe_float(worst_trade.get('realized_r')):.2f}R",
    ])


def build_coach_report(user_id: str) -> str:
    structured = get_structured_trades(user_id)
    if not structured:
        return "No structured trades logged yet. Use `!architect trade-log MNQ 18450 18420 18520 breakout_retest 18515`"
    total = len(structured)
    wins = [t for t in structured if safe_float(t.get("result_pts")) > 0]
    losses = [t for t in structured if safe_float(t.get("result_pts")) < 0]
    avg_planned_r = sum(safe_float(t.get("planned_r")) for t in structured) / total
    avg_realized_r = sum(safe_float(t.get("realized_r")) for t in structured) / total
    capture_ratio = (avg_realized_r / avg_planned_r) if avg_planned_r else 0

    setup_stats = {}
    for t in structured:
        setup = t.get("setup", "unknown")
        s = setup_stats.setdefault(setup, {"count": 0, "wins": 0, "total_r": 0.0})
        s["count"] += 1
        s["total_r"] += safe_float(t.get("realized_r"))
        if safe_float(t.get("result_pts")) > 0:
            s["wins"] += 1

    best_setup_text = "Not enough data"
    if setup_stats:
        best_name, best = max(setup_stats.items(), key=lambda item: ((item[1]["wins"] / item[1]["count"]) if item[1]["count"] else 0, item[1]["total_r"]))
        best_setup_text = f"{best_name} | Trades: {best['count']} | Win rate: {(best['wins'] / best['count']) * 100:.1f}% | Avg R: {best['total_r'] / best['count']:.2f}"

    coaching = []
    if capture_ratio < 0.7:
        coaching.append("You may be cutting winners early. Your average realized R is much lower than your average planned R.")
    elif capture_ratio < 0.9:
        coaching.append("You are capturing a decent portion of your planned reward, but there is still room to improve trade management.")
    else:
        coaching.append("You are capturing most of your planned reward well. That suggests solid follow-through on trade management.")
    coaching.append(
        "Losses currently outnumber wins. Tighten selectivity and make sure you are only taking your best setups."
        if len(losses) > len(wins) else
        "Wins currently outnumber losses. Keep protecting discipline so good execution does not get diluted by random trades."
        if len(wins) > len(losses) else
        "Wins and losses are balanced. Keep logging and let the sample size grow."
    )
    coaching.append(
        "Sample size is still small. Focus on logging trades consistently before making big strategic conclusions."
        if total < 5 else
        "You now have enough data to start identifying behavior patterns instead of judging yourself off one trade."
    )

    biggest_win = max(structured, key=lambda t: safe_float(t.get("realized_r")))
    biggest_loss = min(structured, key=lambda t: safe_float(t.get("realized_r")))
    return "\n".join([
        "Architect Coach Report:",
        f"- Total structured trades reviewed: {total}",
        f"- Average planned R: {avg_planned_r:.2f}",
        f"- Average realized R: {avg_realized_r:.2f}",
        f"- Reward capture ratio: {capture_ratio:.2f}",
        f"- Best setup so far: {best_setup_text}",
        f"- Biggest winner: {biggest_win.get('instrument', 'N/A')} | {biggest_win.get('setup', 'N/A')} | {safe_float(biggest_win.get('realized_r')):.2f}R",
        f"- Biggest loser: {biggest_loss.get('instrument', 'N/A')} | {biggest_loss.get('setup', 'N/A')} | {safe_float(biggest_loss.get('realized_r')):.2f}R",
        "",
        "Key coaching notes:",
        *[f"- {x}" for x in coaching],
        "",
        "Next focus:",
        "- Keep logging every trade.",
        "- Compare your best setup against all others after 10+ trades.",
        "- Watch whether realized R keeps lagging planned R.",
    ])


def build_profile_text(user_id: str) -> str:
    _, user = get_or_create_user_memory(user_id)
    user_trades = get_trades().get(user_id, [])
    weights = user.get("weights", [])
    goals = user.get("goals", [])
    habits = user.get("habits", [])
    checkins = user.get("checkins", [])
    body_baseline = user.get("body_baseline", {})
    body_goal = user.get("body_goal", {})
    profile = user.get("profile", {})
    transformation_goal = user.get("transformation_goal", {})
    fitness_profile = user.get("fitness_profile", {})
    activity_baseline = user.get("activity_baseline", {})
    workout_engine = user.get("user_workout_engine", {})
    latest_checkin = checkins[-1] if checkins else None

    lines = ["Profile snapshot:"]
    if profile:
        lines += [f"- Birth date: {profile.get('birth_date', 'Not set')}", f"- Birth time: {profile.get('birth_time', 'Not set')}"]
    if body_baseline:
        lines.append(f"- Body baseline: {safe_float(body_baseline.get('weight_lb')):.1f} lb | BF {safe_float(body_baseline.get('body_fat_percent')):.1f}% | BMI {safe_float(body_baseline.get('bmi')):.1f}")
    if body_goal:
        lines.append(f"- Body goal: {safe_float(body_goal.get('target_weight_low_lb')):.1f} to {safe_float(body_goal.get('target_weight_high_lb')):.1f} lb | BF {safe_float(body_goal.get('target_body_fat_percent')):.1f}%")
    if transformation_goal:
        lines.append(f"- Transformation goal: {transformation_goal.get('goal_type', 'Not set')} by {transformation_goal.get('deadline_date', 'Not set')}")
    if fitness_profile:
        lines += [f"- Current training mode: {fitness_profile.get('current_training_mode', 'Not set')}", f"- Current phase: {fitness_profile.get('current_phase', 'Not set')}"]
    if activity_baseline:
        lines.append(f"- Activity baseline: {safe_float(activity_baseline.get('active_calories_daily')):.0f} cal | {safe_float(activity_baseline.get('exercise_minutes_daily')):.0f} min | {safe_int(activity_baseline.get('steps_daily'))} steps")
    if workout_engine.get("workout_phase"):
        lines += [f"- Workout engine phase: {workout_engine.get('workout_phase', 'Not set')}", f"- Workout phase duration: {safe_int(workout_engine.get('phase_duration_weeks'))} week(s)"]
    if workout_engine.get("equipment"):
        lines.append(f"- Extra equipment: {', '.join(workout_engine.get('equipment', []))}")
    lines += [
        f"- Latest weight: {weights[-1]['value'] if weights else 'No weight logged yet'}",
        f"- Latest goal: {goals[-1]['text'] if goals else 'No goal logged yet'}",
        f"- Latest habit: {habits[-1]['text'] if habits else 'No habits logged yet'}",
        f"- Latest check-in: Energy {latest_checkin['energy']} | Motivation {latest_checkin['motivation']} | Focus {latest_checkin['focus']}" if latest_checkin else "- Latest check-in: No check-in logged yet",
        f"- Total trades logged: {len(user_trades)}",
    ]
    return "\n".join(lines)


def build_weekly_report(user_id: str) -> str:
    _, user = get_or_create_user_memory(user_id)
    user_trades = get_trades().get(user_id, [])
    lines = [
        "Weekly performance snapshot:",
        f"- Weight logs: {len(user.get('weights', []))}",
        f"- Goals logged: {len(user.get('goals', []))}",
        f"- Habits logged: {len(user.get('habits', []))}",
        f"- Check-ins logged: {len(user.get('checkins', []))}",
        f"- Sleep logs: {len(user.get('sleep_logs', []))}",
        f"- Mood logs: {len(user.get('mood_logs', []))}",
        f"- Focus logs: {len(user.get('focus_logs', []))}",
        f"- Workout logs: {len(user.get('workouts', []))}",
        f"- Activity logs: {len(user.get('activity_logs', []))}",
        f"- PnL logs: {len(user.get('pnl_logs', []))}",
        f"- Wins logged: {len(user.get('wins', []))}",
        f"- Mistakes logged: {len(user.get('mistakes', []))}",
        f"- Trades logged: {len(user_trades)}",
    ]
    if user.get("body_baseline"):
        bb = user["body_baseline"]
        lines.append(f"- Body baseline: {safe_float(bb.get('weight_lb')):.1f} lb | BF {safe_float(bb.get('body_fat_percent')):.1f}% | BMI {safe_float(bb.get('bmi')):.1f}")
    if user.get("body_goal"):
        bg = user["body_goal"]
        lines.append(f"- Body goal: {safe_float(bg.get('target_weight_low_lb')):.1f} to {safe_float(bg.get('target_weight_high_lb')):.1f} lb | BF {safe_float(bg.get('target_body_fat_percent')):.1f}%")
    if user.get("transformation_goal"):
        tg = user["transformation_goal"]
        lines.append(f"- Transformation goal: {tg.get('goal_type', 'Not set')} by {tg.get('deadline_date', 'Not set')}")
    if user.get("fitness_profile"):
        fp = user["fitness_profile"]
        lines.append(f"- Fitness profile: {fp.get('current_training_mode', 'Not set')} | phase {fp.get('current_phase', 'Not set')} | days {safe_int(fp.get('training_days_available'))}")
    if user.get("activity_baseline"):
        ab = user["activity_baseline"]
        lines.append(f"- Activity baseline: {safe_float(ab.get('active_calories_daily')):.0f} cal | {safe_float(ab.get('exercise_minutes_daily')):.0f} min | {safe_int(ab.get('steps_daily'))} steps")
    if user.get("user_workout_engine", {}).get("workout_phase"):
        uwe = user["user_workout_engine"]
        lines.append(f"- Workout engine: {uwe.get('workout_phase', 'Not set')} | duration {safe_int(uwe.get('phase_duration_weeks'))} week(s)")
    if user.get("user_workout_engine", {}).get("equipment"):
        lines.append(f"- Extra equipment: {', '.join(user['user_workout_engine']['equipment'])}")
    if user.get("weights"):
        lines.append(f"- Latest weight: {user['weights'][-1]['value']}")
    if user.get("goals"):
        lines.append(f"- Latest goal: {user['goals'][-1]['text']}")
    if user.get("habits"):
        lines.append(f"- Latest habit: {user['habits'][-1]['text']}")
    if user.get("checkins"):
        c = user["checkins"][-1]
        lines.append(f"- Latest check-in: Energy {c['energy']} | Motivation {c['motivation']} | Focus {c['focus']}")
    return "\n".join(lines)


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


async def send_automatic_morning_brief(guild: discord.Guild):
    state = get_guild_state().get(str(guild.id), {})
    user_id = str(state.get("primary_user_id", "")).strip()
    last_sent = str(state.get("last_morning_brief_date", "")).strip()
    today = today_dr()
    if not user_id or last_sent == today or not has_meaningful_brief_data(user_id):
        return
    channel = get_system_channel(guild, "mission_brief")
    if channel is None:
        return
    await channel.send(build_morning_brief(user_id))
    set_last_morning_brief_date(str(guild.id), today)


async def post_morning_brief_to_system_channel(guild: discord.Guild, user_id: str):
    channel = get_system_channel(guild, "mission_brief")
    if channel is None:
        return False, "I couldn’t find `#mission-brief` in this server."
    register_guild_user(str(guild.id), user_id)
    if not has_meaningful_brief_data(user_id):
        return False, "I found `#mission-brief`, but your Architect profile for this user is blank right now. I stopped the post so it wouldn’t publish empty defaults."
    await channel.send(build_morning_brief(user_id))
    set_last_morning_brief_date(str(guild.id), today_dr())
    return True, f"Morning brief posted in #{channel.name}."


async def run_ai_reply(message: discord.Message, prompt: str):
    system_prompt = get_channel_mode(message.channel.name)
    async with message.channel.typing():
        response = client.responses.create(
            model="gpt-5-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        )
    reply = response.output_text or "I understood you, but I didn’t get usable text back. Try rewording that."
    chunks = [reply[i:i + 1900] for i in range(0, len(reply), 1900)] or [reply]
    for chunk in chunks:
        await message.channel.send(chunk)


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


def need_body(body, usage):
    if not body:
        raise ValueError(f"Usage: `{usage}`")


def parse_parts(body, min_len, usage):
    parts = body.split()
    if len(parts) < min_len:
        raise ValueError(f"Usage: `{usage}`")
    return parts


def command_reply(text):
    return {"type": "text", "text": text}


def usage(text):
    raise ValueError(text)


@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return

    content = message.content.strip()
    if not content.startswith("!architect"):
        return

    prompt = extract_prompt(content)
    if not prompt:
        await message.channel.send("Give me something after `!architect`.")
        return

    command, body = split_command_and_body(prompt)
    user_id = str(message.author.id)

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
            ok, result = await post_morning_brief_to_system_channel(message.guild, user_id)
            await message.channel.send(result)
            return

        if command == "set-body-baseline":
            p = parse_parts(body, 15, "!architect set-body-baseline 221.6 31 32.8 44.5 145.2 3 15.8 1867 152.8 26.6 15 49.8 7.6 Heavy 45")
            set_body_baseline(
                user_id,
                float(p[0]), float(p[1]), float(p[2]), float(p[3]), float(p[4]),
                int(float(p[5])), float(p[6]), float(p[7]), float(p[8]), float(p[9]),
                int(float(p[10])), float(p[11]), float(p[12]), p[13], int(float(p[14]))
            )
            await message.channel.send(
                "Body baseline saved:\n"
                f"- Weight: {float(p[0]):.1f} lb\n"
                f"- Body Fat: {float(p[1]):.1f}%\n"
                f"- BMI: {float(p[2]):.1f}\n"
                f"- Skeletal Muscle: {float(p[3]):.1f}%\n"
                f"- Muscle Mass: {float(p[4]):.1f} lb\n"
                f"- BMR: {float(p[7]):.0f} kcal\n"
                f"- Body Type: {p[13]}\n"
                f"- Metabolic Age: {int(float(p[14]))}"
            )
            return

        if command == "body-baseline":
            await message.channel.send(build_body_baseline_report(user_id))
            return

        if command == "set-body-goal":
            p = parse_parts(body, 3, "!architect set-body-goal 190 200 11")
            set_body_goal(user_id, float(p[0]), float(p[1]), float(p[2]))
            await message.channel.send(
                "Body goal saved:\n"
                f"- Target weight range: {float(p[0]):.1f} to {float(p[1]):.1f} lb\n"
                f"- Target body fat: {float(p[2]):.1f}%"
            )
            return

        if command == "body-goal":
            await message.channel.send(build_body_goal_report(user_id))
            return

        if command == "set-body-change":
            p = parse_parts(body, 3, "!architect set-body-change 32.6 4.8 7.5")
            set_body_change(user_id, float(p[0]), float(p[1]), float(p[2]))
            await message.channel.send(
                "Body change snapshot saved:\n"
                f"- Weight change: +{float(p[0]):.1f} lb\n"
                f"- BMI change: +{float(p[1]):.1f}\n"
                f"- Body fat change: +{float(p[2]):.1f}%"
            )
            return

        if command == "body-change":
            await message.channel.send(build_body_change_report(user_id))
            return

        if command == "set-activity-baseline":
            p = parse_parts(body, 5, "!architect set-activity-baseline 900 60 12 10000 5")
            set_activity_baseline(user_id, float(p[0]), float(p[1]), float(p[2]), int(float(p[3])), int(float(p[4])))
            await message.channel.send(
                "Activity baseline saved:\n"
                f"- Active calories daily: {float(p[0]):.0f}\n"
                f"- Exercise minutes daily: {float(p[1]):.0f}\n"
                f"- Stand hours daily: {float(p[2]):.0f}\n"
                f"- Steps daily: {int(float(p[3]))}\n"
                f"- Workouts per week: {int(float(p[4]))}"
            )
            return

        if command == "activity-baseline":
            await message.channel.send(build_activity_baseline_report(user_id))
            return

        if command == "log-activity":
            p = parse_parts(body, 4, "!architect log-activity 650 52 9800 lifting_and_incline_walk")
            log_activity(user_id, float(p[0]), float(p[1]), int(float(p[2])), p[3])
            await message.channel.send(
                "Activity logged:\n"
                f"- Active calories: {float(p[0]):.0f}\n"
                f"- Exercise minutes: {float(p[1]):.0f}\n"
                f"- Steps: {int(float(p[2]))}\n"
                f"- Activity type: {p[3]}"
            )
            return

        if command == "activity-report":
            await message.channel.send(build_activity_report(user_id))
            return

        if command == "set-profile":
            p = parse_parts(body, 2, "!architect set-profile 12/24/1986 6:00AM")
            set_profile(user_id, p[0], p[1])
            await message.channel.send(f"Profile saved:\n- Birth date: {p[0]}\n- Birth time: {p[1]}")
            return

        if command == "profile":
            await message.channel.send(build_profile_identity_report(user_id))
            return

        if command == "set-transformation-goal":
            p = parse_parts(body, 5, "!architect set-transformation-goal 221.6 190 200 2026-06-01 lean-aesthetic")
            set_transformation_goal(user_id, float(p[0]), float(p[1]), float(p[2]), p[3], p[4])
            await message.channel.send(
                "Transformation goal saved:\n"
                f"- Current weight: {float(p[0]):.1f} lb\n"
                f"- Target range: {float(p[1]):.1f} to {float(p[2]):.1f} lb\n"
                f"- Deadline: {p[3]}\n"
                f"- Goal type: {p[4]}"
            )
            return

        if command == "transformation-status":
            await message.channel.send(build_transformation_status_report(user_id))
            return

        if command == "set-fitness-profile":
            p = parse_parts(
                body, 8,
                "!architect set-fitness-profile hybrid base_building 5 home_bodyweight_soon_gym 300_pushups_daily pushups_situps_squats_lunges_fullbody bodyweight_aesthetics_to_lean_bulk current_starting_phase"
            )
            set_fitness_profile(user_id, p[0], p[1], int(float(p[2])), p[3], p[4], p[5], p[6], p[7])
            await message.channel.send(
                "Fitness profile saved:\n"
                f"- Current training mode: {p[0]}\n"
                f"- Current phase: {p[1]}\n"
                f"- Training days available: {int(float(p[2]))}\n"
                f"- Available resources: {p[3]}\n"
                f"- Current challenge: {p[4]}\n"
                f"- Movement base: {p[5]}\n"
                f"- Physique target: {p[6]}\n"
                f"- Starting point notes: {p[7]}"
            )
            return

        if command == "show-fitness-profile":
            await message.channel.send(build_fitness_profile_report(user_id))
            return

        if command == "update-resources":
            need_body(body, "!architect update-resources full_gym_home_cardio")
            update_resources(user_id, body)
            await message.channel.send(f"Resources updated: {body}")
            return

        if command == "update-training-days":
            need_body(body, "!architect update-training-days 6")
            days = int(float(body))
            update_training_days(user_id, days)
            await message.channel.send(f"Training days updated: {days}")
            return

        if command == "update-fitness-mode":
            p = parse_parts(body, 2, "!architect update-fitness-mode hybrid strength_recomp")
            update_fitness_mode(user_id, p[0], p[1])
            await message.channel.send(f"Fitness mode updated:\n- Training mode: {p[0]}\n- Phase: {p[1]}")
            return

        if command == "adjust-goal-timeline":
            need_body(body, "!architect adjust-goal-timeline 2026-06-15")
            adjust_goal_timeline(user_id, body)
            await message.channel.send(f"Transformation deadline updated: {body}")
            return

        if command == "fitness-adjustment":
            await message.channel.send(build_fitness_adjustment_report(user_id))
            return

        if command == "adjustment-engine":
            await message.channel.send(build_adjustment_engine_report(user_id))
            return

        if command == "set-workout-phase":
            p = parse_parts(body, 2, "!architect set-workout-phase calisthenics 12")
            set_workout_phase(user_id, p[0], int(float(p[1])))
            await message.channel.send(f"Workout phase saved:\n- Phase: {p[0]}\n- Duration: {int(float(p[1]))} week(s)")
            return

        if command == "update-equipment":
            need_body(body, "!architect update-equipment kettlebell weighted_vest bands")
            items = body.split()
            update_equipment(user_id, items)
            await message.channel.send(f"Equipment updated:\n- {', '.join(normalize_token(x) for x in items)}")
            return

        if command == "weekly-workout-plan":
            await message.channel.send(build_weekly_workout_plan(user_id))
            return

        if command == "today-workout":
            await message.channel.send(build_today_workout(user_id))
            return

        if command == "pushup-plan":
            p = body.split()
            total_target = int(float(p[0])) if len(p) >= 1 else 300
            max_set = int(float(p[1])) if len(p) >= 2 else 25
            await message.channel.send(build_pushup_plan(user_id, total_target, max_set))
            return

        if command == "log-weight":
            need_body(body, "!architect log-weight 186.4")
            log_weight(user_id, body)
            await message.channel.send(f"Logged weight: {body}")
            return

        if command == "log-goal":
            need_body(body, "!architect log-goal Stay disciplined this week")
            log_goal(user_id, body)
            await message.channel.send(f"Logged goal: {body}")
            return

        if command == "log-habit":
            need_body(body, "!architect log-habit cardio complete")
            log_habit(user_id, body)
            await message.channel.send(f"Logged habit: {body}")
            return

        if command == "checkin":
            p = parse_parts(body, 6, "!architect checkin energy 8 motivation 7 focus 9")
            log_checkin(user_id, p[1], p[3], p[5])
            await message.channel.send(f"Check-in logged: Energy {p[1]} | Motivation {p[3]} | Focus {p[5]}")
            return

        if command == "log-sleep":
            need_body(body, "!architect log-sleep 7.5")
            hours = float(body)
            log_sleep(user_id, hours)
            await message.channel.send(f"Sleep logged: {hours:.2f} hours")
            return

        if command == "log-mood":
            need_body(body, "!architect log-mood 8")
            score = float(body)
            log_mood(user_id, score)
            await message.channel.send(f"Mood logged: {score:.2f}")
            return

        if command == "log-focus":
            need_body(body, "!architect log-focus 7")
            score = float(body)
            log_focus_score(user_id, score)
            await message.channel.send(f"Focus logged: {score:.2f}")
            return

        if command == "log-workout":
            need_body(body, "!architect log-workout pushups 300")
            log_workout(user_id, body)
            await message.channel.send(f"Workout logged: {body}")
            return

        if command == "life-report":
            await message.channel.send(build_life_report(user_id))
            return

        if command == "set-week-mode":
            need_body(body, "!architect set-week-mode trading")
            set_week_mode(user_id, body)
            await message.channel.send(f"Week mode set: {body}")
            return

        if command == "set-week-focus":
            need_body(body, "!architect set-week-focus trading fitness knowledge")
            items = body.split()
            set_week_focus(user_id, items)
            await message.channel.send(f"Week focus set: {', '.join(items)}")
            return

        if command == "set-training-mode":
            need_body(body, "!architect set-training-mode calisthenics")
            set_training_mode(user_id, body)
            await message.channel.send(f"Training mode set: {body}")
            return

        if command == "set-nutrition":
            need_body(body, "!architect set-nutrition lean-bulk")
            set_nutrition_mode(user_id, body)
            await message.channel.send(f"Nutrition mode set: {body}")
            return

        if command == "set-daily-goal":
            need_body(body, "!architect set-daily-goal pushups 300")
            set_daily_goal(user_id, body)
            await message.channel.send(f"Daily goal set: {body}")
            return

        if command == "watchlist":
            need_body(body, "!architect watchlist MNQ US30 TSLA")
            tickers = body.split()
            set_watchlist(user_id, tickers)
            await message.channel.send(f"Watchlist set: {', '.join(tickers)}")
            return

        if command == "week-plan":
            await message.channel.send(build_week_plan(user_id))
            return

        if command == "morning-brief":
            await message.channel.send(build_morning_brief(user_id))
            return

        if command == "save-note":
            need_body(body, "!architect save-note your note")
            log_note(user_id, body)
            await message.channel.send(f"Note saved: {body}")
            return

        if command == "save-idea":
            need_body(body, "!architect save-idea your idea")
            log_idea(user_id, body)
            await message.channel.send(f"Idea saved: {body}")
            return

        if command == "notes":
            await message.channel.send(show_notes(user_id))
            return

        if command == "ideas":
            await message.channel.send(show_ideas(user_id))
            return

        if command == "knowledge-report":
            await message.channel.send(build_knowledge_report(user_id))
            return

        if command == "log-pnl":
            need_body(body, "!architect log-pnl 250")
            val = float(body)
            log_pnl(user_id, val)
            await message.channel.send(f"PnL logged: {val:.2f}")
            return

        if command == "pnl-report":
            await message.channel.send(build_pnl_report(user_id))
            return

        if command == "win":
            need_body(body, "!architect win Executed with patience")
            log_win(user_id, body)
            await message.channel.send(f"Win logged: {body}")
            return

        if command == "mistake":
            need_body(body, "!architect mistake Entered before confirmation")
            log_mistake(user_id, body)
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
            need_body(body, "!architect trade-review Instrument: MNQ | Entry: 18450 | Stop: 18420 | Target: 18520 | Reason: breakout retest | Result: +65 pts")
            log_trade_raw(user_id, body)
            review_prompt = (
                "Review this trade like a sharp trading coach. "
                "Identify strengths, weaknesses, discipline issues, risk issues, and next-step improvements.\n\n"
                f"Trade:\n{body}"
            )
            await run_ai_reply(message, review_prompt)
            return

        if command == "trade-log":
            p = parse_parts(body, 6, "!architect trade-log MNQ 18450 18420 18520 breakout_retest 18515")
            calc = log_trade_structured(user_id, p[0], float(p[1]), float(p[2]), float(p[3]), p[4], float(p[5]))
            await message.channel.send(
                "Trade logged:\n"
                f"{p[0]} | Entry {float(p[1])} | Stop {float(p[2])} | Target {float(p[3])} | Exit {float(p[5])}\n"
                f"Setup: {p[4]}\n"
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

        await run_ai_reply(message, prompt)

    except ValueError as e:
        await message.channel.send(str(e))
    except Exception as e:
        print(f"Error in on_message: {e}")
        await message.channel.send(f"Something went wrong while processing that request.\n\nError: `{str(e)[:180]}`")


bot.run(DISCORD_TOKEN)
