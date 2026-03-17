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

def get_department_channel(guild, department):
    """Return the Discord channel object for a department."""
    if department not in DEPARTMENT_CHANNELS:
        return None

    channel_name = DEPARTMENT_CHANNELS[department]

    for channel in guild.text_channels:
        if channel.name == channel_name:
            return channel

    return None


async def send_to_department(guild, department, message):
    """Send a message to a department channel."""
    channel = get_department_channel(guild, department)

    if channel:
        await channel.send(message)
async def route_department_report(guild, department, message):
    # send to the main department
    await send_to_department(guild, department, message)

    # also send to architect analysis for synthesis
    if department != "architect_analysis":
        await send_to_department(guild, "architect_analysis", message)      

async def build_morning_brief(user_id):
    memory = get_memory()
    user = memory.get(user_id, {})

    fitness = user.get("fitness_profile", {})
    nutrition = user.get("nutrition_logs", [])
    workouts = user.get("workout_logs", [])
    activity = user.get("activity_logs", [])

    brief = []

    brief.append("**ARCHITECT MORNING BRIEF**")
    brief.append("")

    brief.append("Mission:")
    brief.append("Stay disciplined. Execute the plan. Build momentum.")
    brief.append("")

    brief.append("Fitness Focus:")
    brief.append("Train with intent. Maintain consistency.")
    brief.append("")

    brief.append("Nutrition Focus:")
    brief.append("Eat clean. Prioritize protein. Stay hydrated.")
    brief.append("")

    brief.append("Trading Awareness:")
    brief.append("Check economic calendar before trading.")
    brief.append("")

    brief.append("Reflection:")
    brief.append("Progress comes from disciplined daily action.")
    brief.append("")

    return "\n".join(brief)
ARCHITECT_CORE_IDENTITY = """
You are Architect.

Architect is the AI operating system built for Luis.

Your purpose is to help Luis build a disciplined, high-performance life through
clear thinking, smart execution, data tracking, strategic reflection, and steady improvement.

You support Luis across multiple departments:

1. Trading Desk
- Help with trading performance, execution, discipline, risk management, journaling, and coaching.

2. Fitness Lab
- Help with workouts, body recomposition, consistency, recovery, and performance.

3. Nutrition Lab
- Help with food choices, macros, meal structure, consistency, and sustainable nutrition habits.

4. Knowledge Vault
- Help store ideas, notes, insights, frameworks, and lessons so they can be reused intelligently.

5. Builder Lab
- Help with projects, business ideas, execution plans, systems, and creating real results.

6. Cosmic Reflection
- Help with reflection, mindset, personal alignment, self-awareness, and thoughtful perspective.

7. Architect Analysis
- Help analyze patterns across Luis's behavior, decisions, habits, and performance.

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


def today_utc():
    return datetime.now(timezone.utc).date().isoformat()


def dr_now():
    return datetime.now(DR_TZ)


def today_dr():
    return dr_now().date().isoformat()


def load_json_file(path: str, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default
    except Exception:
        return default


def save_json_file(path: str, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_user_key(message: discord.Message) -> str:
    return str(message.author.id)


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


def get_department_prompt(channel_name: str) -> str:
    name = (channel_name or "").lower()

    if "trading" in name or name in ["market-prep", "chart-review", "market-notes"]:
        return """
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
"""
    if "fitness" in name or name in ["fitness-log", "training-protocol", "supplement-stack"]:
        return """
You are currently operating inside the Fitness Lab department.

Priority:
- workouts
- training consistency
- body recomposition
- recovery
- performance habits

Respond like a practical performance coach.
Be structured, motivating, and realistic.
"""
    if "nutrition" in name or name in ["meal-log", "meal-architect"]:
        return """
You are currently operating inside the Nutrition Lab department.

Priority:
- meal consistency
- food quality
- macros
- sustainable choices
- body support

Respond like a practical nutrition coach.
Keep advice simple, useful, and repeatable.
"""
    if "knowledge" in name or name in ["reading-log", "pdf-archive"]:
        return """
You are currently operating inside the Knowledge Vault department.

Priority:
- idea capture
- note quality
- insight retrieval
- organizing thinking
- second-brain support

Respond like a strategist and knowledge architect.
Help turn information into usable insight.
"""
    if "builder" in name or name in ["project-builder", "research-lab"]:
        return """
You are currently operating inside the Builder Lab department.

Priority:
- project execution
- business building
- systems
- shipping ideas
- creating momentum

Respond like an execution advisor and builder.
Help turn ideas into next steps and systems.
"""
    if "cosmic" in name or "reflection" in name or name in ["daily-alignment", "cosmic-notes", "life-design"]:
        return """
You are currently operating inside the Cosmic Reflection department.

Priority:
- reflection
- mindset
- emotional clarity
- alignment
- perspective

Respond with depth, calm, and grounded wisdom.
Be reflective but still practical.
"""
    if "analysis" in name or "performance" in name or name in ["system-analysis", "performance-report"]:
        return """
You are currently operating inside the Architect Analysis / Performance department.

Priority:
- pattern recognition
- personal review
- discipline
- progress tracking
- extracting lessons from behavior and data

Respond like a high-level performance analyst and coach.
Be honest, constructive, and useful.
"""

    return """
You are operating in a general Architect OS context.

Respond as Architect:
strategic, practical, clear, and helpful.
"""


def get_channel_mode(channel_name: str) -> str:
    return ARCHITECT_CORE_IDENTITY + "\n\n" + get_department_prompt(channel_name)


def extract_prompt(content: str) -> str:
    return content.replace("!architect", "", 1).strip()


def split_command_and_body(prompt: str):
    if not prompt:
        return "", ""

    parts = prompt.split(" ", 1)
    command = parts[0].strip().lower()
    body = parts[1].strip() if len(parts) > 1 else ""
    return command, body


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


def ensure_guild_state(guild_id: str):
    guild_state = get_guild_state()
    current = guild_state.get(guild_id, {
        "primary_user_id": "",
        "last_morning_brief_date": ""
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
    user_data = memory.get(user_id, {
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
            "last_updated": ""
            },
        "user_workout_engine": {
            "workout_phase": "",
            "phase_duration_weeks": 0,
            "equipment": []
        },
        "context": {
            "week_mode": "",
            "week_focus": [],
            "training_mode": "",
            "nutrition_mode": "",
            "daily_goals": [],
            "watchlist": []
        }
    })

    user_data.setdefault("weights", [])
    user_data.setdefault("goals", [])
    user_data.setdefault("notes", [])
    user_data.setdefault("ideas", [])
    user_data.setdefault("habits", [])
    user_data.setdefault("checkins", [])
    user_data.setdefault("pnl_logs", [])
    user_data.setdefault("wins", [])
    user_data.setdefault("mistakes", [])
    user_data.setdefault("sleep_logs", [])
    user_data.setdefault("mood_logs", [])
    user_data.setdefault("focus_logs", [])
    user_data.setdefault("workouts", [])
    user_data.setdefault("activity_logs", [])
    user_data.setdefault("body_baseline", {})
    user_data.setdefault("body_goal", {})
    user_data.setdefault("body_change", {})
    user_data.setdefault("activity_baseline", {})
    user_data.setdefault("profile", {})
    user_data.setdefault("transformation_goal", {})
    user_data.setdefault("fitness_profile", {})
    user_data.setdefault("user_workout_engine", {})
    user_data["user_workout_engine"].setdefault("workout_phase", "")
    user_data["user_workout_engine"].setdefault("phase_duration_weeks", 0)
    user_data["user_workout_engine"].setdefault("equipment", [])
    user_data.setdefault("context", {})
    user_data["context"].setdefault("week_mode", "")
    user_data["context"].setdefault("week_focus", [])
    user_data["context"].setdefault("training_mode", "")
    user_data["context"].setdefault("nutrition_mode", "")
    user_data["context"].setdefault("daily_goals", [])
    user_data["context"].setdefault("watchlist", [])

    return memory, user_data

def analyze_adjustment_engine(user_id: str):
    memory = get_memory()
    user = memory.get(user_id, {})

    baseline = user.get("body_baseline", {})
    goal = user.get("transformation_goal", {})
    workouts = user.get("workouts", [])
    activity = user.get("activity_logs", [])

    recommendation = "maintain current plan"

    training_days = len(workouts[-7:])
    activity_days = len(activity[-7:])

    if training_days < 3:
        recommendation = "increase training frequency"

    if activity_days < 3:
        recommendation = "add cardio or daily activity"

    if training_days >= 5 and activity_days >= 5:
        recommendation = "training load high — ensure recovery"

    adjustment = {
        "recommendation": recommendation,
        "training_days": training_days,
        "activity_days": activity_days
    }

    user.setdefault("adjustment_engine", {})
    user["adjustment_engine"]["last_analysis"] = adjustment

    memory[user_id] = user
    save_memory(memory)

    return adjustment
def log_detailed_workout(user_id: str, workout_type: str, amount: int, source: str = "manual", notes: str = ""):
    memory = get_memory()
    user = memory.get(user_id, {})

    user.setdefault("workout_logs", [])

    user["workout_logs"].append({
        "workout_type": workout_type,
        "amount": amount,
        "source": source,
        "notes": notes,
        "timestamp": utc_now_iso(),
        "date": today_dr()
    })

    memory[user_id] = user
    save_memory(memory)


def log_detailed_activity(
    user_id: str,
    activity_type: str,
    cardio_type: str,
    duration_min: int,
    calories: int = 0,
    steps: int = 0,
    avg_heart_rate: int = 0,
    distance: float = 0.0,
    source: str = "manual",
    notes: str = ""
):
    memory = get_memory()
    user = memory.get(user_id, {})

    user.setdefault("activity_logs", [])

    user["activity_logs"].append({
        "activity_type": activity_type,
        "cardio_type": cardio_type,
        "duration_min": duration_min,
        "calories": calories,
        "steps": steps,
        "avg_heart_rate": avg_heart_rate,
        "distance": distance,
        "source": source,
        "notes": notes,
        "timestamp": utc_now_iso(),
        "date": today_dr()
    })

    memory[user_id] = user
    save_memory(memory)


def log_detailed_sleep(user_id: str, hours: float, source: str = "manual", notes: str = ""):
    memory = get_memory()
    user = memory.get(user_id, {})

    user.setdefault("sleep_logs", [])

    user["sleep_logs"].append({
        "hours": hours,
        "source": source,
        "notes": notes,
        "timestamp": utc_now_iso(),
        "date": today_dr()
    })

    memory[user_id] = user
    save_memory(memory)


def log_detailed_recovery(user_id: str, score: int, source: str = "manual", notes: str = ""):
    memory = get_memory()
    user = memory.get(user_id, {})

    user.setdefault("recovery_logs", [])

    user["recovery_logs"].append({
        "score": score,
        "source": source,
        "notes": notes,
        "timestamp": utc_now_iso(),
        "date": today_dr()
    })

    memory[user_id] = user
    save_memory(memory)


def log_detailed_nutrition(
    user_id: str,
    calories: int,
    protein_g: int = 0,
    carbs_g: int = 0,
    fats_g: int = 0,
    source: str = "manual",
    notes: str = ""
):
    memory = get_memory()
    user = memory.get(user_id, {})

    user.setdefault("nutrition_logs", [])

    user["nutrition_logs"].append({
        "calories": calories,
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fats_g": fats_g,
        "source": source,
        "notes": notes,
        "timestamp": utc_now_iso(),
        "date": today_dr()
    })

    memory[user_id] = user
    save_memory(memory)
def has_meaningful_brief_data(user_id: str) -> bool:
    memory = get_memory()
    user_data = memory.get(user_id, {})
    context = user_data.get("context", {})
    body_baseline = user_data.get("body_baseline", {})
    body_goal = user_data.get("body_goal", {})
    fitness_profile = user_data.get("fitness_profile", {})
    transformation_goal = user_data.get("transformation_goal", {})
    activity_baseline = user_data.get("activity_baseline", {})
    workout_engine = user_data.get("user_workout_engine", {})

    has_context = any([
        context.get("week_mode"),
        context.get("week_focus"),
        context.get("training_mode"),
        context.get("nutrition_mode"),
        context.get("daily_goals"),
        context.get("watchlist"),
    ])

    has_logs = any([
        user_data.get("sleep_logs"),
        user_data.get("mood_logs"),
        user_data.get("focus_logs"),
        user_data.get("activity_logs"),
    ])

    has_profile = any([
        body_baseline,
        body_goal,
        fitness_profile,
        transformation_goal,
        activity_baseline,
        workout_engine.get("workout_phase"),
        workout_engine.get("equipment"),
    ])

    return has_context or has_logs or has_profile


def set_body_baseline(
    user_id: str,
    weight_lb: float,
    body_fat_percent: float,
    bmi: float,
    skeletal_muscle_percent: float,
    muscle_mass_lb: float,
    muscle_storage_ability_level: int,
    protein_percent: float,
    bmr_kcal: float,
    fat_free_body_weight_lb: float,
    subcutaneous_fat_percent: float,
    visceral_fat: int,
    body_water_percent: float,
    bone_mass_lb: float,
    body_type: str,
    metabolic_age: int
):
    memory, user_data = get_or_create_user_memory(user_id)
    user_data["body_baseline"] = {
        "weight_lb": weight_lb,
        "body_fat_percent": body_fat_percent,
        "bmi": bmi,
        "skeletal_muscle_percent": skeletal_muscle_percent,
        "muscle_mass_lb": muscle_mass_lb,
        "muscle_storage_ability_level": muscle_storage_ability_level,
        "protein_percent": protein_percent,
        "bmr_kcal": bmr_kcal,
        "fat_free_body_weight_lb": fat_free_body_weight_lb,
        "subcutaneous_fat_percent": subcutaneous_fat_percent,
        "visceral_fat": visceral_fat,
        "body_water_percent": body_water_percent,
        "bone_mass_lb": bone_mass_lb,
        "body_type": body_type,
        "metabolic_age": metabolic_age,
        "timestamp": utc_now_iso()
    }
    memory[user_id] = user_data
    save_memory(memory)


def build_body_baseline_report(user_id: str) -> str:
    memory = get_memory()
    user_data = memory.get(user_id, {})
    baseline = user_data.get("body_baseline", {})

    if not baseline:
        return (
            "No body baseline saved yet.\n"
            "Use:\n"
            "!architect set-body-baseline 221.6 31 32.8 44.5 145.2 3 15.8 1867 152.8 26.6 15 49.8 7.6 Heavy 45"
        )

    return (
        "Architect Body Baseline:\n"
        f"- Weight: {baseline.get('weight_lb', 0):.1f} lb\n"
        f"- Body Fat: {baseline.get('body_fat_percent', 0):.1f}%\n"
        f"- BMI: {baseline.get('bmi', 0):.1f}\n"
        f"- Skeletal Muscle: {baseline.get('skeletal_muscle_percent', 0):.1f}%\n"
        f"- Muscle Mass: {baseline.get('muscle_mass_lb', 0):.1f} lb\n"
        f"- Muscle Storage Ability Level: {baseline.get('muscle_storage_ability_level', 0)}\n"
        f"- Protein: {baseline.get('protein_percent', 0):.1f}%\n"
        f"- BMR: {baseline.get('bmr_kcal', 0):.0f} kcal\n"
        f"- Fat-Free Body Weight: {baseline.get('fat_free_body_weight_lb', 0):.1f} lb\n"
        f"- Subcutaneous Fat: {baseline.get('subcutaneous_fat_percent', 0):.1f}%\n"
        f"- Visceral Fat: {baseline.get('visceral_fat', 0)}\n"
        f"- Body Water: {baseline.get('body_water_percent', 0):.1f}%\n"
        f"- Bone Mass: {baseline.get('bone_mass_lb', 0):.1f} lb\n"
        f"- Body Type: {baseline.get('body_type', 'Not set')}\n"
        f"- Metabolic Age: {baseline.get('metabolic_age', 0)}"
    )


def set_body_goal(user_id: str, target_weight_low_lb: float, target_weight_high_lb: float, target_body_fat_percent: float):
    memory, user_data = get_or_create_user_memory(user_id)
    user_data["body_goal"] = {
        "target_weight_low_lb": target_weight_low_lb,
        "target_weight_high_lb": target_weight_high_lb,
        "target_body_fat_percent": target_body_fat_percent,
        "timestamp": utc_now_iso()
    }
    memory[user_id] = user_data
    save_memory(memory)


def build_body_goal_report(user_id: str) -> str:
    memory = get_memory()
    user_data = memory.get(user_id, {})
    goal = user_data.get("body_goal", {})

    if not goal:
        return "No body goal saved yet. Use !architect set-body-goal 190 200 11"

    return (
        "Architect Body Goal:\n"
        f"- Target weight range: {goal.get('target_weight_low_lb', 0):.1f} to {goal.get('target_weight_high_lb', 0):.1f} lb\n"
        f"- Target body fat: {goal.get('target_body_fat_percent', 0):.1f}%"
    )


def set_body_change(user_id: str, weight_change_lb: float, bmi_change: float, body_fat_change_percent: float):
    memory, user_data = get_or_create_user_memory(user_id)
    user_data["body_change"] = {
        "weight_change_lb": weight_change_lb,
        "bmi_change": bmi_change,
        "body_fat_change_percent": body_fat_change_percent,
        "timestamp": utc_now_iso()
    }
    memory[user_id] = user_data
    save_memory(memory)


def build_body_change_report(user_id: str) -> str:
    memory = get_memory()
    user_data = memory.get(user_id, {})
    change = user_data.get("body_change", {})

    if not change:
        return "No body change snapshot saved yet. Use !architect set-body-change 32.6 4.8 7.5"

    return (
        "Architect Body Change Snapshot:\n"
        f"- Weight change: +{change.get('weight_change_lb', 0):.1f} lb\n"
        f"- BMI change: +{change.get('bmi_change', 0):.1f}\n"
        f"- Body fat change: +{change.get('body_fat_change_percent', 0):.1f}%"
    )


def set_activity_baseline(
    user_id: str,
    active_calories_daily: float,
    exercise_minutes_daily: float,
    stand_hours_daily: float,
    steps_daily: int,
    workouts_per_week: int
):
    memory, user_data = get_or_create_user_memory(user_id)
    user_data["activity_baseline"] = {
        "active_calories_daily": active_calories_daily,
        "exercise_minutes_daily": exercise_minutes_daily,
        "stand_hours_daily": stand_hours_daily,
        "steps_daily": steps_daily,
        "workouts_per_week": workouts_per_week,
        "timestamp": utc_now_iso()
    }
    memory[user_id] = user_data
    save_memory(memory)


def build_activity_baseline_report(user_id: str) -> str:
    memory = get_memory()
    user_data = memory.get(user_id, {})
    baseline = user_data.get("activity_baseline", {})

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


def log_activity(user_id: str, active_calories: float, exercise_minutes: float, steps: int, activity_type: str):
    memory, user_data = get_or_create_user_memory(user_id)
    user_data["activity_logs"].append({
        "active_calories": active_calories,
        "exercise_minutes": exercise_minutes,
        "steps": steps,
        "activity_type": activity_type,
        "date": today_dr(),
        "timestamp": utc_now_iso()
    })
    memory[user_id] = user_data
    save_memory(memory)


def build_activity_report(user_id: str) -> str:
    memory = get_memory()
    user_data = memory.get(user_id, {})
    baseline = user_data.get("activity_baseline", {})
    logs = user_data.get("activity_logs", [])

    if not baseline and not logs:
        return "No activity data saved yet. Use !architect set-activity-baseline and !architect log-activity."

    today = today_dr()
    today_logs = [x for x in logs if x.get("date") == today]

    total_logs = len(logs)
    avg_active = sum(x.get("active_calories", 0) for x in logs) / total_logs if total_logs else 0
    avg_exercise = sum(x.get("exercise_minutes", 0) for x in logs) / total_logs if total_logs else 0
    avg_steps = sum(x.get("steps", 0) for x in logs) / total_logs if total_logs else 0

    today_active = sum(x.get("active_calories", 0) for x in today_logs)
    today_exercise = sum(x.get("exercise_minutes", 0) for x in today_logs)
    today_steps = sum(x.get("steps", 0) for x in today_logs)

    latest_type = today_logs[-1].get("activity_type", "No activity type logged today") if today_logs else "No activity type logged today"

    lines = ["Architect Activity Report:"]

    if baseline:
        lines.append(f"- Baseline active calories: {baseline.get('active_calories_daily', 0):.0f}")
        lines.append(f"- Baseline exercise minutes: {baseline.get('exercise_minutes_daily', 0):.0f}")
        lines.append(f"- Baseline stand hours: {baseline.get('stand_hours_daily', 0):.0f}")
        lines.append(f"- Baseline steps: {baseline.get('steps_daily', 0)}")
        lines.append(f"- Baseline workouts per week: {baseline.get('workouts_per_week', 0)}")

    lines.extend([
        f"- Activity sessions logged: {total_logs}",
        f"- Today's active calories: {today_active:.0f}",
        f"- Today's exercise minutes: {today_exercise:.0f}",
        f"- Today's steps: {today_steps}",
        f"- Today's latest activity type: {latest_type}",
        f"- Average active calories per session: {avg_active:.0f}",
        f"- Average exercise minutes per session: {avg_exercise:.0f}",
        f"- Average steps per session: {avg_steps:.0f}",
    ])

    return "\n".join(lines)


def set_profile(user_id: str, birth_date: str, birth_time: str):
    memory, user_data = get_or_create_user_memory(user_id)
    user_data["profile"]["birth_date"] = birth_date
    user_data["profile"]["birth_time"] = birth_time
    user_data["profile"]["timestamp"] = utc_now_iso()
    memory[user_id] = user_data
    save_memory(memory)


def build_profile_identity_report(user_id: str) -> str:
    memory = get_memory()
    user_data = memory.get(user_id, {})
    profile = user_data.get("profile", {})

    if not profile:
        return "No profile identity saved yet. Use !architect set-profile 12/24/1986 6:00AM"

    return (
        "Architect Profile:\n"
        f"- Birth date: {profile.get('birth_date', 'Not set')}\n"
        f"- Birth time: {profile.get('birth_time', 'Not set')}"
    )


def set_transformation_goal(
    user_id: str,
    current_weight_lb: float,
    target_weight_low_lb: float,
    target_weight_high_lb: float,
    deadline_date: str,
    goal_type: str
):
    memory, user_data = get_or_create_user_memory(user_id)
    user_data["transformation_goal"] = {
        "current_weight_lb": current_weight_lb,
        "target_weight_low_lb": target_weight_low_lb,
        "target_weight_high_lb": target_weight_high_lb,
        "deadline_date": deadline_date,
        "goal_type": goal_type,
        "timestamp": utc_now_iso()
    }
    memory[user_id] = user_data
    save_memory(memory)


def compute_transformation_status(user_id: str):
    memory = get_memory()
    user_data = memory.get(user_id, {})

    transformation = user_data.get("transformation_goal", {})
    body_baseline = user_data.get("body_baseline", {})
    body_goal = user_data.get("body_goal", {})
    fitness_profile = user_data.get("fitness_profile", {})

    if not transformation:
        return None

    current_weight = safe_float(
        transformation.get("current_weight_lb") or body_baseline.get("weight_lb"),
        0
    )
    target_low = safe_float(
        transformation.get("target_weight_low_lb") or body_goal.get("target_weight_low_lb"),
        0
    )
    target_high = safe_float(
        transformation.get("target_weight_high_lb") or body_goal.get("target_weight_high_lb"),
        0
    )
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

    pounds_per_week = 0
    if weeks_left > 0:
        pounds_per_week = pounds_to_goal / weeks_left

    training_days = safe_int(fitness_profile.get("training_days_available", 0), 0)
    current_mode = fitness_profile.get("current_training_mode", "Not set")
    current_phase = fitness_profile.get("current_phase", "Not set")
    resources = fitness_profile.get("available_resources", "Not set")

    pace_status = "On pace"
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

    recommendation_lines = []

    if days_left < 0:
        recommendation_lines.append("The deadline has already passed. Set a new transformation date and reassess the plan.")
    else:
        if pounds_per_week > 2.0:
            recommendation_lines.append("Your required pace is aggressive. You may need tighter nutrition, higher consistency, and possibly more training or cardio.")
        elif pounds_per_week > 1.25:
            recommendation_lines.append("Your pace is demanding but possible if compliance stays high across training, sleep, and nutrition.")
        elif pounds_per_week > 0:
            recommendation_lines.append("Your pace is reasonable. Focus on consistency instead of overcorrecting.")
        else:
            recommendation_lines.append("Your current target range may already be close. Reassess whether the focus should shift toward lean quality and muscle retention.")

    if training_days > 0:
        if pounds_per_week > 1.25 and training_days < 5:
            recommendation_lines.append("Given the timeframe, adding an extra training day could help if recovery and schedule allow.")
        elif training_days >= 5:
            recommendation_lines.append("Training frequency is already solid. Prioritize recovery and food precision over blindly adding more volume.")
        else:
            recommendation_lines.append("Keep training days realistic and sustainable so recovery does not collapse.")
    else:
        recommendation_lines.append("Training days are not set yet. Set your fitness profile so Architect can coach more intelligently.")

    if current_mode.lower() == "calisthenics":
        recommendation_lines.append("Calisthenics is a strong base for control and aesthetics. If resources expand, hybrid training can accelerate body recomposition.")
    elif current_mode.lower() == "hybrid":
        recommendation_lines.append("Hybrid mode gives more options for body recomposition. Make sure programming matches recovery and your actual equipment access.")

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
        "recommendation_lines": recommendation_lines
    }


def build_transformation_status_report(user_id: str) -> str:
    memory = get_memory()
    user_data = memory.get(user_id, {})
    transformation = user_data.get("transformation_goal", {})

    if not transformation:
        return "No transformation goal saved yet. Use !architect set-transformation-goal 221.6 190 200 2026-06-01 lean-aesthetic"

    status = compute_transformation_status(user_id)

    if not status:
        return "Transformation status unavailable."
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
        f"- Resources: {status.get('resources', 'Not set')}\n"
        f"\nRecommendations:\n{recommendations}"
    )


def set_fitness_profile(
    user_id: str,
    current_training_mode: str,
    current_phase: str,
    training_days_available: int,
    available_resources: str,
    current_challenge: str,
    movement_base: str,
    physique_target: str,
    starting_point_notes: str
):
    memory, user_data = get_or_create_user_memory(user_id)
    user_data["fitness_profile"] = {
        "current_training_mode": current_training_mode,
        "current_phase": current_phase,
        "training_days_available": training_days_available,
        "available_resources": available_resources,
        "current_challenge": current_challenge,
        "movement_base": movement_base,
        "physique_target": physique_target,
        "starting_point_notes": starting_point_notes,
        "timestamp": utc_now_iso()
    }
    memory[user_id] = user_data
    save_memory(memory)


def build_fitness_profile_report(user_id: str) -> str:
    memory = get_memory()
    user_data = memory.get(user_id, {})
    fp = user_data.get("fitness_profile", {})

    if not fp:
        return (
            "No fitness profile saved yet.\n"
            "Use:\n"
            "!architect set-fitness-profile hybrid base_building 5 home_bodyweight_soon_gym 300_pushups_daily pushups_situps_squats_lunges_fullbody bodyweight_aesthetics_to_lean_bulk current_starting_phase"
        )

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


def update_resources(user_id: str, available_resources: str):
    memory, user_data = get_or_create_user_memory(user_id)
    fitness_profile = user_data.get("fitness_profile", {})
    fitness_profile["available_resources"] = available_resources
    fitness_profile["timestamp"] = utc_now_iso()
    user_data["fitness_profile"] = fitness_profile
    memory[user_id] = user_data
    save_memory(memory)


def update_training_days(user_id: str, training_days_available: int):
    memory, user_data = get_or_create_user_memory(user_id)
    fitness_profile = user_data.get("fitness_profile", {})
    fitness_profile["training_days_available"] = training_days_available
    fitness_profile["timestamp"] = utc_now_iso()
    user_data["fitness_profile"] = fitness_profile
    memory[user_id] = user_data
    save_memory(memory)


def update_fitness_mode(user_id: str, current_training_mode: str, current_phase: str):
    memory, user_data = get_or_create_user_memory(user_id)
    fitness_profile = user_data.get("fitness_profile", {})
    fitness_profile["current_training_mode"] = current_training_mode
    fitness_profile["current_phase"] = current_phase
    fitness_profile["timestamp"] = utc_now_iso()
    user_data["fitness_profile"] = fitness_profile
    memory[user_id] = user_data
    save_memory(memory)


def adjust_goal_timeline(user_id: str, deadline_date: str):
    memory, user_data = get_or_create_user_memory(user_id)
    transformation_goal = user_data.get("transformation_goal", {})
    transformation_goal["deadline_date"] = deadline_date
    transformation_goal["timestamp"] = utc_now_iso()
    user_data["transformation_goal"] = transformation_goal
    memory[user_id] = user_data
    save_memory(memory)


def build_fitness_adjustment_report(user_id: str) -> str:
    memory = get_memory()
    user_data = memory.get(user_id, {})

    fitness_profile = user_data.get("fitness_profile", {})
    transformation_goal = user_data.get("transformation_goal", {})
    activity_baseline = user_data.get("activity_baseline", {})
    status = compute_transformation_status(user_id)

    if not fitness_profile:
        return "No fitness profile saved yet. Use !architect set-fitness-profile ... first."
    if not transformation_goal:
        return "No transformation goal saved yet. Use !architect set-transformation-goal ... first."
    if not status or not status.get("valid", False):
        return f"Fitness adjustment unavailable: {status.get('error', 'Missing valid transformation data') if status else 'Missing transformation data'}"

    mode = fitness_profile.get("current_training_mode", "Not set")
    phase = fitness_profile.get("current_phase", "Not set")
    days = safe_int(fitness_profile.get("training_days_available", 0), 0)
    resources = fitness_profile.get("available_resources", "Not set")
    challenge = fitness_profile.get("current_challenge", "Not set")

    pace = status.get("pace_status", "Not set")
    pounds_per_week = status.get("pounds_per_week", 0.0)

    options = []

    if pace == "Aggressive":
        options.append("Option A: Keep the deadline and tighten execution hard across nutrition, steps, recovery, and training consistency.")
        if days < 6:
            options.append("Option B: Add 1 extra training day if recovery, schedule, and nutrition can actually support it.")
        options.append("Option C: Keep current training days but increase weekly calorie expenditure through structured cardio or higher daily movement.")
        options.append("Option D: Extend the deadline slightly so the cut is more realistic and muscle retention improves.")
    elif pace == "Demanding":
        options.append("Option A: Stay at current days and improve compliance before increasing volume.")
        if days < 6:
            options.append("Option B: Add 1 training day only if sleep and soreness remain controlled.")
        options.append("Option C: Tighten nutrition and keep daily activity more consistent.")
    elif pace == "Reasonable":
        options.append("Option A: Do not overcorrect. Keep the plan simple and sustainable.")
        options.append("Option B: Use current structure and refine execution quality first.")
        options.append("Option C: Increase output only if progress stalls for multiple weeks.")
    else:
        options.append("Option A: Reassess goal range and timeline together.")
        options.append("Option B: Focus on body quality, strength, and consistency first.")

    intelligent_notes = []

    if "gym" in resources.lower():
        intelligent_notes.append("You now have gym access in your resource picture, so hybrid training has more upside.")
    else:
        intelligent_notes.append("Your current resource profile still looks limited, so bodyweight and hybrid efficiency matter more than complexity.")

    if mode.lower() == "calisthenics":
        intelligent_notes.append("Calisthenics remains excellent for body control and aesthetics, but gym access can increase progression options once ready.")
    elif mode.lower() == "hybrid":
        intelligent_notes.append("Hybrid mode gives you the most flexibility right now, especially if your goal includes leaning out while preserving or rebuilding muscle.")

    if days >= 6:
        intelligent_notes.append("You already have a high training frequency. More is not automatically better; recovery quality now matters a lot.")
    elif days <= 4:
        intelligent_notes.append("Your current training frequency is modest. If the timeline is tight, an additional day may help if recovery is stable.")

    if activity_baseline:
        intelligent_notes.append(
            f"Your current activity target is around {activity_baseline.get('active_calories_daily', 0):.0f} active calories and {activity_baseline.get('exercise_minutes_daily', 0):.0f} exercise minutes per day."
        )

    intelligent_notes.append(f"Current challenge in system: {challenge}.")
    intelligent_notes.append(f"Current pace requirement: {pounds_per_week:.2f} lb/week.")

    options_text = "\n".join([f"- {x}" for x in options])
    notes_text = "\n".join([f"- {x}" for x in intelligent_notes])

    return (
        "Architect Fitness Adjustment:\n"
        f"- Current mode: {mode}\n"
        f"- Current phase: {phase}\n"
        f"- Training days available: {days}\n"
        f"- Resources: {resources}\n"
        f"- Pace status: {pace}\n"
        f"- Required weekly pace: {pounds_per_week:.2f} lb/week\n"
        f"\nAdjustment options:\n{options_text}\n"
        f"\nIntelligent notes:\n{notes_text}"
    )


def set_workout_phase(user_id: str, workout_phase: str, phase_duration_weeks: int):
    memory, user_data = get_or_create_user_memory(user_id)
    user_data["user_workout_engine"]["workout_phase"] = workout_phase
    user_data["user_workout_engine"]["phase_duration_weeks"] = phase_duration_weeks
    memory[user_id] = user_data
    save_memory(memory)


def update_equipment(user_id: str, equipment_items):
    memory, user_data = get_or_create_user_memory(user_id)
    user_data["user_workout_engine"]["equipment"] = equipment_items
    memory[user_id] = user_data
    save_memory(memory)


def get_equipment_list(user_id: str):
    memory = get_memory()
    user_data = memory.get(user_id, {})
    engine = user_data.get("user_workout_engine", {})
    return engine.get("equipment", [])


def get_workout_phase_data(user_id: str):
    memory = get_memory()
    user_data = memory.get(user_id, {})
    return user_data.get("user_workout_engine", {})


def has_gym_access(user_id: str) -> bool:
    memory = get_memory()
    user_data = memory.get(user_id, {})
    fitness_profile = user_data.get("fitness_profile", {})
    resources = str(fitness_profile.get("available_resources", "")).lower()
    equipment = [x.lower() for x in get_equipment_list(user_id)]

    if "gym" in resources or "full_gym" in resources:
        return True
    if "barbell" in equipment or "machine" in equipment or "cable" in equipment:
        return True
    return False


def build_equipment_modifier_text(user_id: str) -> str:
    equipment = get_equipment_list(user_id)
    if not equipment:
        return "No extra equipment updated yet."
    return ", ".join(equipment)


def build_weekly_workout_plan(user_id: str) -> str:
    phase_data = get_workout_phase_data(user_id)
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
        ""
    ]

    for day_name in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
        block = WEEKLY_WORKOUT_LIBRARY[day_name]
        exercise_list = block["gym"] if gym_mode else block["home"]

        lines.append(f"{day_name.title()} - {block['title']}")
        for exercise in exercise_list:
            lines.append(f"- {exercise}")
        lines.append("")

    return "\n".join(lines).strip()


def build_today_workout(user_id: str) -> str:
    today_name = dr_now().strftime("%A").lower()
    block = WEEKLY_WORKOUT_LIBRARY.get(today_name)

    if not block:
        return "I couldn't determine today's workout."

    phase_data = get_workout_phase_data(user_id)
    workout_phase = phase_data.get("workout_phase", "not set")
    phase_duration_weeks = phase_data.get("phase_duration_weeks", 0)

    gym_mode = has_gym_access(user_id)
    exercise_list = block["gym"] if gym_mode else block["home"]
    mode_label = "gym/hybrid" if gym_mode else "home/bodyweight"

    lines = [
        "Architect Today Workout:",
        f"- Day: {today_name.title()}",
        f"- Session: {block['title']}",
        f"- Focus: {block['focus']}",
        f"- Workout phase: {workout_phase}",
        f"- Phase duration: {phase_duration_weeks} week(s)",
        f"- Build mode used: {mode_label}",
        f"- Extra equipment: {build_equipment_modifier_text(user_id)}",
        "",
        "Today's exercises:"
    ]

    for exercise in exercise_list:
        lines.append(f"- {exercise}")

    lines.extend([
        "",
        "Why this session:",
        "- It matches your weekly structure from the hybrid manual.",
        "- It keeps daily intention high instead of guessing what to train.",
        "- It lets Architect adapt the session around your current access and tools."
    ])

    return "\n".join(lines)


def build_pushup_plan(user_id: str, total_target: int = 300, max_set: int = 25) -> str:
    if max_set <= 0:
        max_set = 25
    if total_target <= 0:
        total_target = 300

    option_25_sets = total_target // 25
    remainder_25 = total_target % 25

    lines = [
        "Architect Push-Up Plan:",
        f"- Daily target: {total_target}",
        f"- Current max set: {max_set}",
        "",
        "Recommended options:",
        "- Option 1: 15 sets of 20 = 300 total",
        f"- Option 2: 12 sets of 25 = 300 total" if remainder_25 == 0 else f"- Option 2: {option_25_sets} sets of 25 + 1 finisher set of {remainder_25}",
        "- Option 3: EMOM style — 10 to 15 reps every hour across the day until target is complete",
        "",
        "Rest guidance:",
        "- On 20-rep sets: rest 45 to 75 sec",
        "- On 25-rep sets: rest 75 to 120 sec",
        "",
        "Reasoning:",
        "- Frequent submaximal sets let you accumulate volume without frying your shoulders or triceps too early.",
        "- This builds work capacity, muscular endurance, movement quality, and consistency.",
        "- The goal is to dominate total daily volume while staying fresh enough to repeat it."
    ]

    equipment = [x.lower() for x in get_equipment_list(user_id)]
    if "weighted_vest" in equipment or "vest" in equipment:
        lines.append("- Weighted vest note: use the vest only on a smaller portion of the total volume, not all 300.")
    if "kettlebell" in equipment or "kettlebells" in equipment:
        lines.append("- Kettlebell note: use kettlebell floor press or swings as accessory work, not as a replacement for the daily push-up target.")

    return "\n".join(lines)


def log_weight(user_id: str, value: str):
    memory, user_data = get_or_create_user_memory(user_id)
    user_data["weights"].append({
        "value": value,
        "timestamp": utc_now_iso()
    })
    memory[user_id] = user_data
    save_memory(memory)


def log_goal(user_id: str, goal: str):
    memory, user_data = get_or_create_user_memory(user_id)
    user_data["goals"].append({
        "text": goal,
        "timestamp": utc_now_iso()
    })
    memory[user_id] = user_data
    save_memory(memory)


def log_habit(user_id: str, habit_text: str):
    memory, user_data = get_or_create_user_memory(user_id)
    user_data["habits"].append({
        "text": habit_text,
        "timestamp": utc_now_iso()
    })
    memory[user_id] = user_data
    save_memory(memory)


def log_checkin(user_id: str, energy: str, motivation: str, focus: str):
    memory, user_data = get_or_create_user_memory(user_id)
    user_data["checkins"].append({
        "energy": energy,
        "motivation": motivation,
        "focus": focus,
        "timestamp": utc_now_iso()
    })
    memory[user_id] = user_data
    save_memory(memory)


def log_note(user_id: str, note: str):
    memory, user_data = get_or_create_user_memory(user_id)
    user_data["notes"].append({
        "text": note,
        "timestamp": utc_now_iso()
    })
    memory[user_id] = user_data
    save_memory(memory)


def log_idea(user_id: str, idea: str):
    memory, user_data = get_or_create_user_memory(user_id)
    user_data["ideas"].append({
        "text": idea,
        "timestamp": utc_now_iso()
    })
    memory[user_id] = user_data
    save_memory(memory)


def log_pnl(user_id: str, pnl_value: float):
    memory, user_data = get_or_create_user_memory(user_id)
    user_data["pnl_logs"].append({
        "value": pnl_value,
        "date": today_dr(),
        "timestamp": utc_now_iso()
    })
    memory[user_id] = user_data
    save_memory(memory)


def log_win(user_id: str, text: str):
    memory, user_data = get_or_create_user_memory(user_id)
    user_data["wins"].append({
        "text": text,
        "date": today_dr(),
        "timestamp": utc_now_iso()
    })
    memory[user_id] = user_data
    save_memory(memory)


def log_mistake(user_id: str, text: str):
    memory, user_data = get_or_create_user_memory(user_id)
    user_data["mistakes"].append({
        "text": text,
        "date": today_dr(),
        "timestamp": utc_now_iso()
    })
    memory[user_id] = user_data
    save_memory(memory)


def log_sleep(user_id: str, hours: float):
    memory, user_data = get_or_create_user_memory(user_id)
    user_data["sleep_logs"].append({
        "hours": hours,
        "date": today_dr(),
        "timestamp": utc_now_iso()
    })
    memory[user_id] = user_data
    save_memory(memory)


def log_mood(user_id: str, score: float):
    memory, user_data = get_or_create_user_memory(user_id)
    user_data["mood_logs"].append({
        "score": score,
        "date": today_dr(),
        "timestamp": utc_now_iso()
    })
    memory[user_id] = user_data
    save_memory(memory)


def log_focus_score(user_id: str, score: float):
    memory, user_data = get_or_create_user_memory(user_id)
    user_data["focus_logs"].append({
        "score": score,
        "date": today_dr(),
        "timestamp": utc_now_iso()
    })
    memory[user_id] = user_data
    save_memory(memory)


def log_workout(user_id: str, workout_text: str):
    memory, user_data = get_or_create_user_memory(user_id)
    user_data["workouts"].append({
        "text": workout_text,
        "date": today_dr(),
        "timestamp": utc_now_iso()
    })
    memory[user_id] = user_data
    save_memory(memory)


def set_week_mode(user_id: str, mode: str):
    memory, user_data = get_or_create_user_memory(user_id)
    user_data["context"]["week_mode"] = mode
    memory[user_id] = user_data
    save_memory(memory)


def set_week_focus(user_id: str, focus_items):
    memory, user_data = get_or_create_user_memory(user_id)
    user_data["context"]["week_focus"] = focus_items
    memory[user_id] = user_data
    save_memory(memory)


def set_training_mode(user_id: str, mode: str):
    memory, user_data = get_or_create_user_memory(user_id)
    user_data["context"]["training_mode"] = mode
    memory[user_id] = user_data
    save_memory(memory)


def set_nutrition_mode(user_id: str, mode: str):
    memory, user_data = get_or_create_user_memory(user_id)
    user_data["context"]["nutrition_mode"] = mode
    memory[user_id] = user_data
    save_memory(memory)


def set_daily_goal(user_id: str, goal_text: str):
    memory, user_data = get_or_create_user_memory(user_id)
    user_data["context"]["daily_goals"].append({
        "text": goal_text,
        "timestamp": utc_now_iso()
    })
    memory[user_id] = user_data
    save_memory(memory)


def set_watchlist(user_id: str, tickers):
    memory, user_data = get_or_create_user_memory(user_id)
    user_data["context"]["watchlist"] = tickers
    memory[user_id] = user_data
    save_memory(memory)


def show_notes(user_id: str):
    memory = get_memory()
    user_data = memory.get(user_id, {})
    notes = user_data.get("notes", [])

    if not notes:
        return "No notes saved yet."

    text = "Saved notes:\n"
    for note in notes[-10:]:
        text += f"- {note['text']}\n"
    return text


def show_ideas(user_id: str):
    memory = get_memory()
    user_data = memory.get(user_id, {})
    ideas = user_data.get("ideas", [])

    if not ideas:
        return "No ideas saved yet."

    text = "Saved ideas:\n"
    for idea in ideas[-10:]:
        text += f"- {idea['text']}\n"
    return text


def build_knowledge_report(user_id: str):
    memory = get_memory()
    user_data = memory.get(user_id, {})
    notes = user_data.get("notes", [])
    ideas = user_data.get("ideas", [])

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
    memory = get_memory()
    user_data = memory.get(user_id, {})
    pnl_logs = user_data.get("pnl_logs", [])

    if not pnl_logs:
        return "No PnL logs saved yet. Use !architect log-pnl 250"

    total = sum(x["value"] for x in pnl_logs)
    avg_day = total / len(pnl_logs)
    green_days = sum(1 for x in pnl_logs if x["value"] > 0)
    red_days = sum(1 for x in pnl_logs if x["value"] < 0)
    flat_days = sum(1 for x in pnl_logs if x["value"] == 0)

    best_day = max(pnl_logs, key=lambda x: x["value"])
    worst_day = min(pnl_logs, key=lambda x: x["value"])

    today = today_dr()
    today_total = sum(x["value"] for x in pnl_logs if x["date"] == today)

    return (
        "PnL Report:\n"
        f"- Days logged: {len(pnl_logs)}\n"
        f"- Today: {today_total:.2f}\n"
        f"- Total PnL: {total:.2f}\n"
        f"- Average day: {avg_day:.2f}\n"
        f"- Green days: {green_days}\n"
        f"- Red days: {red_days}\n"
        f"- Flat days: {flat_days}\n"
        f"- Best day: {best_day['value']:.2f} ({best_day['date']})\n"
        f"- Worst day: {worst_day['value']:.2f} ({worst_day['date']})"
    )


def build_daily_report(user_id: str):
    memory = get_memory()
    trades = get_trades()

    user_memory = memory.get(user_id, {})
    user_trades = trades.get(user_id, [])
    today = today_dr()

    habits_today = [x for x in user_memory.get("habits", []) if x["timestamp"][:10] == today]
    checkins_today = [x for x in user_memory.get("checkins", []) if x["timestamp"][:10] == today]
    notes_today = [x for x in user_memory.get("notes", []) if x["timestamp"][:10] == today]
    ideas_today = [x for x in user_memory.get("ideas", []) if x["timestamp"][:10] == today]
    pnl_today = [x for x in user_memory.get("pnl_logs", []) if x["date"] == today]
    wins_today = [x for x in user_memory.get("wins", []) if x["date"] == today]
    mistakes_today = [x for x in user_memory.get("mistakes", []) if x["date"] == today]
    trades_today = [x for x in user_trades if x["timestamp"][:10] == today]
    sleep_today = [x for x in user_memory.get("sleep_logs", []) if x["date"] == today]
    mood_today = [x for x in user_memory.get("mood_logs", []) if x["date"] == today]
    focus_today = [x for x in user_memory.get("focus_logs", []) if x["date"] == today]
    workouts_today = [x for x in user_memory.get("workouts", []) if x["date"] == today]
    activity_today = [x for x in user_memory.get("activity_logs", []) if x["date"] == today]

    today_pnl_total = sum(x["value"] for x in pnl_today)
    today_activity_cals = sum(x.get("active_calories", 0) for x in activity_today)
    today_activity_minutes = sum(x.get("exercise_minutes", 0) for x in activity_today)

    latest_checkin_text = "No check-in today"
    if checkins_today:
        latest = checkins_today[-1]
        latest_checkin_text = (
            f"Energy {latest['energy']} | "
            f"Motivation {latest['motivation']} | "
            f"Focus {latest['focus']}"
        )

    sleep_text = f"{sleep_today[-1]['hours']} hrs" if sleep_today else "No sleep logged"
    mood_text = f"{mood_today[-1]['score']}" if mood_today else "No mood logged"
    focus_text = f"{focus_today[-1]['score']}" if focus_today else "No focus logged"

    return (
        "Architect Daily System Report:\n"
        f"- Date: {today}\n"
        f"- Sleep: {sleep_text}\n"
        f"- Mood: {mood_text}\n"
        f"- Focus: {focus_text}\n"
        f"- Check-in: {latest_checkin_text}\n"
        f"- Habits logged today: {len(habits_today)}\n"
        f"- Workouts logged today: {len(workouts_today)}\n"
        f"- Activity sessions today: {len(activity_today)}\n"
        f"- Activity calories today: {today_activity_cals:.0f}\n"
        f"- Activity minutes today: {today_activity_minutes:.0f}\n"
        f"- Notes saved today: {len(notes_today)}\n"
        f"- Ideas saved today: {len(ideas_today)}\n"
        f"- Wins logged today: {len(wins_today)}\n"
        f"- Mistakes logged today: {len(mistakes_today)}\n"
        f"- Trades logged today: {len(trades_today)}\n"
        f"- PnL today: {today_pnl_total:.2f}"
    )


def build_life_report(user_id: str):
    memory = get_memory()
    user_data = memory.get(user_id, {})

    sleep_logs = user_data.get("sleep_logs", [])
    mood_logs = user_data.get("mood_logs", [])
    focus_logs = user_data.get("focus_logs", [])
    workouts = user_data.get("workouts", [])
    habits = user_data.get("habits", [])
    notes = user_data.get("notes", [])
    ideas = user_data.get("ideas", [])
    body_baseline = user_data.get("body_baseline", {})
    body_goal = user_data.get("body_goal", {})
    transformation = user_data.get("transformation_goal", {})
    fitness_profile = user_data.get("fitness_profile", {})
    activity_baseline = user_data.get("activity_baseline", {})
    activity_logs = user_data.get("activity_logs", [])

    if not sleep_logs and not mood_logs and not focus_logs and not workouts and not body_baseline and not body_goal and not transformation and not fitness_profile and not activity_baseline and not activity_logs:
        return "No life performance logs yet. Use !architect log-sleep, !architect log-mood, !architect log-focus, !architect log-workout, !architect set-body-baseline, !architect set-body-goal, !architect set-fitness-profile, and !architect set-activity-baseline."

    avg_sleep = sum(x["hours"] for x in sleep_logs) / len(sleep_logs) if sleep_logs else 0
    avg_mood = sum(x["score"] for x in mood_logs) / len(mood_logs) if mood_logs else 0
    avg_focus = sum(x["score"] for x in focus_logs) / len(focus_logs) if focus_logs else 0
    avg_activity_cals = sum(x["active_calories"] for x in activity_logs) / len(activity_logs) if activity_logs else 0
    avg_activity_minutes = sum(x["exercise_minutes"] for x in activity_logs) / len(activity_logs) if activity_logs else 0

    lines = ["Architect Life Performance Report:"]

    if body_baseline:
        lines.append(f"- Baseline weight: {body_baseline.get('weight_lb', 0):.1f} lb")
        lines.append(f"- Baseline body fat: {body_baseline.get('body_fat_percent', 0):.1f}%")
        lines.append(f"- Baseline BMI: {body_baseline.get('bmi', 0):.1f}")

    if body_goal:
        lines.append(
            f"- Body goal: {body_goal.get('target_weight_low_lb', 0):.1f} to {body_goal.get('target_weight_high_lb', 0):.1f} lb | BF {body_goal.get('target_body_fat_percent', 0):.1f}%"
        )

    if fitness_profile:
        lines.append(f"- Current training mode: {fitness_profile.get('current_training_mode', 'Not set')}")
        lines.append(f"- Current phase: {fitness_profile.get('current_phase', 'Not set')}")
        lines.append(f"- Training days available: {fitness_profile.get('training_days_available', 0)}")

    if activity_baseline:
        lines.append(f"- Activity baseline calories: {activity_baseline.get('active_calories_daily', 0):.0f}")
        lines.append(f"- Activity baseline exercise minutes: {activity_baseline.get('exercise_minutes_daily', 0):.0f}")
        lines.append(f"- Activity baseline steps: {activity_baseline.get('steps_daily', 0)}")

    lines.extend([
        f"- Sleep logs: {len(sleep_logs)}",
        f"- Average sleep: {avg_sleep:.2f} hrs",
        f"- Mood logs: {len(mood_logs)}",
        f"- Average mood: {avg_mood:.2f}",
        f"- Focus logs: {len(focus_logs)}",
        f"- Average focus: {avg_focus:.2f}",
        f"- Workouts logged: {len(workouts)}",
        f"- Activity sessions logged: {len(activity_logs)}",
        f"- Average activity calories: {avg_activity_cals:.0f}",
        f"- Average activity minutes: {avg_activity_minutes:.0f}",
        f"- Habits logged: {len(habits)}",
        f"- Notes captured: {len(notes)}",
        f"- Ideas captured: {len(ideas)}",
    ])

    return "\n".join(lines)


def build_week_plan(user_id: str):
    memory = get_memory()
    user_data = memory.get(user_id, {})
    context = user_data.get("context", {})
    fitness_profile = user_data.get("fitness_profile", {})
    activity_baseline = user_data.get("activity_baseline", {})

    week_mode = context.get("week_mode", "Not set")
    week_focus = context.get("week_focus", [])
    training_mode = context.get("training_mode", "Not set")
    nutrition_mode = context.get("nutrition_mode", "Not set")
    watchlist = context.get("watchlist", [])
    daily_goals = context.get("daily_goals", [])

    latest_goal = daily_goals[-1]["text"] if daily_goals else "No daily goal set"
    focus_text = ", ".join(week_focus) if week_focus else "Not set"
    watchlist_text = ", ".join(watchlist) if watchlist else "Not set"

    fitness_lines = ""
    if fitness_profile:
        fitness_lines += (
            f"- Current phase: {fitness_profile.get('current_phase', 'Not set')}\n"
            f"- Training days available: {fitness_profile.get('training_days_available', 0)}\n"
            f"- Current challenge: {fitness_profile.get('current_challenge', 'Not set')}\n"
        )

    if activity_baseline:
        fitness_lines += (
            f"- Activity target calories: {activity_baseline.get('active_calories_daily', 0):.0f}\n"
            f"- Activity target exercise minutes: {activity_baseline.get('exercise_minutes_daily', 0):.0f}\n"
        )

    return (
        "Architect Week Plan:\n"
        f"- Week mode: {week_mode}\n"
        f"- Week focus: {focus_text}\n"
        f"- Training mode: {training_mode}\n"
        f"- Nutrition mode: {nutrition_mode}\n"
        f"{fitness_lines}"
        f"- Watchlist: {watchlist_text}\n"
        f"- Latest daily goal: {latest_goal}"
    )


def build_morning_brief(user_id: str):
    memory = get_memory()
    user_data = memory.get(user_id, {})
    context = user_data.get("context", {})
    body_baseline = user_data.get("body_baseline", {})
    body_goal = user_data.get("body_goal", {})
    fitness_profile = user_data.get("fitness_profile", {})
    transformation_goal = user_data.get("transformation_goal", {})
    activity_baseline = user_data.get("activity_baseline", {})

    today = today_dr()
    today_pretty = dr_now().strftime("%A, %B %d, %Y")

    sleep_today = [x for x in user_data.get("sleep_logs", []) if x["date"] == today]
    mood_today = [x for x in user_data.get("mood_logs", []) if x["date"] == today]
    focus_today = [x for x in user_data.get("focus_logs", []) if x["date"] == today]
    activity_today = [x for x in user_data.get("activity_logs", []) if x["date"] == today]

    if not sleep_today:
        sleep_today = user_data.get("sleep_logs", [])[-1:]
    if not mood_today:
        mood_today = user_data.get("mood_logs", [])[-1:]
    if not focus_today:
        focus_today = user_data.get("focus_logs", [])[-1:]

    week_mode = context.get("week_mode", "Not set")
    week_focus = context.get("week_focus", [])
    training_mode = context.get("training_mode", "Not set")
    nutrition_mode = context.get("nutrition_mode", "Not set")
    watchlist = context.get("watchlist", [])
    daily_goals = context.get("daily_goals", [])

    sleep_text = f"{sleep_today[-1]['hours']} hrs" if sleep_today else "Not logged"
    mood_text = f"{mood_today[-1]['score']}" if mood_today else "Not logged"
    focus_text = f"{focus_today[-1]['score']}" if focus_today else "Not logged"
    focus_area_text = ", ".join(week_focus) if week_focus else "Not set"
    watchlist_text = ", ".join(watchlist) if watchlist else "Not set"
    latest_goal = daily_goals[-1]["text"] if daily_goals else "No daily goal set"

    recommendation = "Stay disciplined, execute the plan, and log your data."
    if str(training_mode).lower() == "calisthenics":
        recommendation = "Training mode is calisthenics. Get your volume done early and keep nutrition aligned with recovery."
    elif str(training_mode).lower() == "hybrid":
        recommendation = "Training mode is hybrid. Balance strength, conditioning, and recovery without losing consistency."

    lines = [
        "Architect Morning Brief:",
        f"- Date: {today_pretty}",
    ]

    if body_baseline:
        lines.append(
            f"- Body baseline: {body_baseline.get('weight_lb', 0):.1f} lb | BF {body_baseline.get('body_fat_percent', 0):.1f}% | BMI {body_baseline.get('bmi', 0):.1f}"
        )

    if body_goal:
        lines.append(
            f"- Body goal: {body_goal.get('target_weight_low_lb', 0):.1f} to {body_goal.get('target_weight_high_lb', 0):.1f} lb | BF {body_goal.get('target_body_fat_percent', 0):.1f}%"
        )

    if fitness_profile:
        lines.append(f"- Current phase: {fitness_profile.get('current_phase', 'Not set')}")
        lines.append(f"- Fitness mode: {fitness_profile.get('current_training_mode', 'Not set')}")
        lines.append(f"- Current challenge: {fitness_profile.get('current_challenge', 'Not set')}")

    if transformation_goal:
        lines.append(f"- Transformation deadline: {transformation_goal.get('deadline_date', 'Not set')}")

    if activity_baseline:
        lines.append(
            f"- Activity baseline: {activity_baseline.get('active_calories_daily', 0):.0f} cal | {activity_baseline.get('exercise_minutes_daily', 0):.0f} min | {activity_baseline.get('steps_daily', 0)} steps"
        )

    if activity_today:
        today_cals = sum(x.get("active_calories", 0) for x in activity_today)
        today_minutes = sum(x.get("exercise_minutes", 0) for x in activity_today)
        today_steps = sum(x.get("steps", 0) for x in activity_today)
        lines.append(f"- Activity today: {today_cals:.0f} cal | {today_minutes:.0f} min | {today_steps} steps")

    phase_data = get_workout_phase_data(user_id)
    workout_phase = phase_data.get("workout_phase", "")
    if workout_phase:
        lines.append(f"- Workout engine phase: {workout_phase}")

    today_name = dr_now().strftime("%A").lower()
    today_block = WEEKLY_WORKOUT_LIBRARY.get(today_name)
    if today_block:
        lines.append(f"- Today's workout: {today_block['title']}")

    lines.extend([
        f"- Week mode: {week_mode}",
        f"- Week focus: {focus_area_text}",
        f"- Training mode: {training_mode}",
        f"- Nutrition mode: {nutrition_mode}",
        f"- Daily goal: {latest_goal}",
        f"- Watchlist: {watchlist_text}",
        f"- Sleep: {sleep_text}",
        f"- Mood: {mood_text}",
        f"- Focus: {focus_text}",
        f"- Recommendation: {recommendation}"
    ])

    return "\n".join(lines)


def log_trade_raw(user_id: str, raw_trade: str):
    trades = get_trades()
    user_trades = trades.get(user_id, [])
    user_trades.append({
        "type": "raw_review",
        "raw": raw_trade,
        "timestamp": utc_now_iso()
    })
    trades[user_id] = user_trades
    save_trades(trades)


def log_trade_structured(
    user_id: str,
    instrument: str,
    entry: float,
    stop: float,
    target: float,
    setup: str,
    exit_price: float
):
    risk_pts = abs(entry - stop)
    target_pts = abs(target - entry)
    result_pts = exit_price - entry
    planned_r = target_pts / risk_pts if risk_pts != 0 else 0
    realized_r = result_pts / risk_pts if risk_pts != 0 else 0

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
        "timestamp": utc_now_iso()
    })

    trades[user_id] = user_trades
    save_trades(trades)

    return {
        "risk_pts": risk_pts,
        "target_pts": target_pts,
        "result_pts": result_pts,
        "planned_r": planned_r,
        "realized_r": realized_r
    }


def get_structured_trades(user_id: str):
    trades = get_trades()
    user_trades = trades.get(user_id, [])
    return [t for t in user_trades if t.get("type") == "structured"]


def build_profile_text(user_id: str) -> str:
    memory = get_memory()
    trades = get_trades()

    user_memory = memory.get(user_id, {})
    user_trades = trades.get(user_id, [])

    weights = user_memory.get("weights", [])
    goals = user_memory.get("goals", [])
    habits = user_memory.get("habits", [])
    checkins = user_memory.get("checkins", [])
    body_baseline = user_memory.get("body_baseline", {})
    body_goal = user_memory.get("body_goal", {})
    profile = user_memory.get("profile", {})
    transformation_goal = user_memory.get("transformation_goal", {})
    fitness_profile = user_memory.get("fitness_profile", {})
    activity_baseline = user_memory.get("activity_baseline", {})
    workout_engine = user_memory.get("user_workout_engine", {})

    latest_weight = weights[-1]["value"] if weights else "No weight logged yet"
    latest_goal = goals[-1]["text"] if goals else "No goal logged yet"
    latest_habit = habits[-1]["text"] if habits else "No habits logged yet"

    if checkins:
        latest_checkin = checkins[-1]
        latest_checkin_text = (
            f"Energy {latest_checkin['energy']} | Motivation {latest_checkin['motivation']} | Focus {latest_checkin['focus']}"
        )
    else:
        latest_checkin_text = "No check-in logged yet"

    lines = ["Profile snapshot:"]

    if profile:
        lines.append(f"- Birth date: {profile.get('birth_date', 'Not set')}")
        lines.append(f"- Birth time: {profile.get('birth_time', 'Not set')}")

    if body_baseline:
        lines.append(
            f"- Body baseline: {body_baseline.get('weight_lb', 0):.1f} lb | BF {body_baseline.get('body_fat_percent', 0):.1f}% | BMI {body_baseline.get('bmi', 0):.1f}"
        )

    if body_goal:
        lines.append(
            f"- Body goal: {body_goal.get('target_weight_low_lb', 0):.1f} to {body_goal.get('target_weight_high_lb', 0):.1f} lb | BF {body_goal.get('target_body_fat_percent', 0):.1f}%"
        )

    if transformation_goal:
        lines.append(
            f"- Transformation goal: {transformation_goal.get('goal_type', 'Not set')} by {transformation_goal.get('deadline_date', 'Not set')}"
        )

    if fitness_profile:
        lines.append(f"- Current training mode: {fitness_profile.get('current_training_mode', 'Not set')}")
        lines.append(f"- Current phase: {fitness_profile.get('current_phase', 'Not set')}")

    if activity_baseline:
        lines.append(
            f"- Activity baseline: {activity_baseline.get('active_calories_daily', 0):.0f} cal | {activity_baseline.get('exercise_minutes_daily', 0):.0f} min | {activity_baseline.get('steps_daily', 0)} steps"
        )

    if workout_engine.get("workout_phase"):
        lines.append(f"- Workout engine phase: {workout_engine.get('workout_phase', 'Not set')}")
        lines.append(f"- Workout phase duration: {workout_engine.get('phase_duration_weeks', 0)} week(s)")

    if workout_engine.get("equipment"):
        lines.append(f"- Extra equipment: {', '.join(workout_engine.get('equipment', []))}")

    lines.extend([
        f"- Latest weight: {latest_weight}",
        f"- Latest goal: {latest_goal}",
        f"- Latest habit: {latest_habit}",
        f"- Latest check-in: {latest_checkin_text}",
        f"- Total trades logged: {len(user_trades)}"
    ])

    return "\n".join(lines)


def build_weekly_report(user_id: str) -> str:
    memory = get_memory()
    trades = get_trades()

    user_memory = memory.get(user_id, {})
    user_trades = trades.get(user_id, [])

    weights = user_memory.get("weights", [])
    goals = user_memory.get("goals", [])
    habits = user_memory.get("habits", [])
    checkins = user_memory.get("checkins", [])
    pnl_logs = user_memory.get("pnl_logs", [])
    wins = user_memory.get("wins", [])
    mistakes = user_memory.get("mistakes", [])
    sleep_logs = user_memory.get("sleep_logs", [])
    mood_logs = user_memory.get("mood_logs", [])
    focus_logs = user_memory.get("focus_logs", [])
    workouts = user_memory.get("workouts", [])
    activity_logs = user_memory.get("activity_logs", [])
    body_baseline = user_memory.get("body_baseline", {})
    body_goal = user_memory.get("body_goal", {})
    transformation_goal = user_memory.get("transformation_goal", {})
    fitness_profile = user_memory.get("fitness_profile", {})
    activity_baseline = user_memory.get("activity_baseline", {})
    workout_engine = user_memory.get("user_workout_engine", {})

    report_lines = [
        "Weekly performance snapshot:",
        f"- Weight logs: {len(weights)}",
        f"- Goals logged: {len(goals)}",
        f"- Habits logged: {len(habits)}",
        f"- Check-ins logged: {len(checkins)}",
        f"- Sleep logs: {len(sleep_logs)}",
        f"- Mood logs: {len(mood_logs)}",
        f"- Focus logs: {len(focus_logs)}",
        f"- Workout logs: {len(workouts)}",
        f"- Activity logs: {len(activity_logs)}",
        f"- PnL logs: {len(pnl_logs)}",
        f"- Wins logged: {len(wins)}",
        f"- Mistakes logged: {len(mistakes)}",
        f"- Trades logged: {len(user_trades)}",
    ]

    if body_baseline:
        report_lines.append(
            f"- Body baseline: {body_baseline.get('weight_lb', 0):.1f} lb | BF {body_baseline.get('body_fat_percent', 0):.1f}% | BMI {body_baseline.get('bmi', 0):.1f}"
        )
    if body_goal:
        report_lines.append(
            f"- Body goal: {body_goal.get('target_weight_low_lb', 0):.1f} to {body_goal.get('target_weight_high_lb', 0):.1f} lb | BF {body_goal.get('target_body_fat_percent', 0):.1f}%"
        )
    if transformation_goal:
        report_lines.append(
            f"- Transformation goal: {transformation_goal.get('goal_type', 'Not set')} by {transformation_goal.get('deadline_date', 'Not set')}"
        )
    if fitness_profile:
        report_lines.append(
            f"- Fitness profile: {fitness_profile.get('current_training_mode', 'Not set')} | phase {fitness_profile.get('current_phase', 'Not set')} | days {fitness_profile.get('training_days_available', 0)}"
        )
    if activity_baseline:
        report_lines.append(
            f"- Activity baseline: {activity_baseline.get('active_calories_daily', 0):.0f} cal | {activity_baseline.get('exercise_minutes_daily', 0):.0f} min | {activity_baseline.get('steps_daily', 0)} steps"
        )
    if workout_engine.get("workout_phase"):
        report_lines.append(
            f"- Workout engine: {workout_engine.get('workout_phase', 'Not set')} | duration {workout_engine.get('phase_duration_weeks', 0)} week(s)"
        )
    if workout_engine.get("equipment"):
        report_lines.append(
            f"- Extra equipment: {', '.join(workout_engine.get('equipment', []))}"
        )
    if weights:
        report_lines.append(f"- Latest weight: {weights[-1]['value']}")
    if goals:
        report_lines.append(f"- Latest goal: {goals[-1]['text']}")
    if habits:
        report_lines.append(f"- Latest habit: {habits[-1]['text']}")
    if checkins:
        latest_checkin = checkins[-1]
        report_lines.append(
            f"- Latest check-in: Energy {latest_checkin['energy']} | Motivation {latest_checkin['motivation']} | Focus {latest_checkin['focus']}"
        )

    return "\n".join(report_lines)


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

    setup_counts = {}
    for trade in structured:
        setup = trade.get("setup", "unknown")
        setup_counts[setup] = setup_counts.get(setup, 0) + 1

    best_setup = max(setup_counts, key=setup_counts.get) if setup_counts else "N/A"
    win_rate = (wins / total) * 100 if total > 0 else 0

    return (
        "Trading stats:\n"
        f"- Total structured trades: {total}\n"
        f"- Wins: {wins}\n"
        f"- Losses: {losses}\n"
        f"- Breakeven: {breakeven}\n"
        f"- Win rate: {win_rate:.1f}%\n"
        f"- Average result (pts): {avg_result:.2f}\n"
        f"- Average realized R: {avg_realized_r:.2f}\n"
        f"- Average planned R: {avg_planned_r:.2f}\n"
        f"- Most used setup: {best_setup}"
    )


def build_dashboard(user_id: str) -> str:
    structured = get_structured_trades(user_id)

    if not structured:
        return "No structured trades logged yet. Use !architect trade-log MNQ 18450 18420 18520 breakout_retest 18515"

    total = len(structured)
    wins = sum(1 for t in structured if t.get("result_pts", 0) > 0)
    losses = sum(1 for t in structured if t.get("result_pts", 0) < 0)
    breakeven = sum(1 for t in structured if t.get("result_pts", 0) == 0)

    total_points = sum(t.get("result_pts", 0) for t in structured)
    total_realized_r = sum(t.get("realized_r", 0) for t in structured)

    avg_result = total_points / total if total > 0 else 0
    avg_realized_r = total_realized_r / total if total > 0 else 0
    avg_planned_r = sum(t.get("planned_r", 0) for t in structured) / total if total > 0 else 0
    win_rate = (wins / total) * 100 if total > 0 else 0

    best_trade = max(structured, key=lambda t: t.get("result_pts", 0))
    worst_trade = min(structured, key=lambda t: t.get("result_pts", 0))

    setup_counts = {}
    for trade in structured:
        setup = trade.get("setup", "unknown")
        setup_counts[setup] = setup_counts.get(setup, 0) + 1

    best_setup = max(setup_counts, key=setup_counts.get) if setup_counts else "N/A"

    return (
        "Architect Trading Dashboard:\n"
        f"- Total structured trades: {total}\n"
        f"- Wins: {wins}\n"
        f"- Losses: {losses}\n"
        f"- Breakeven: {breakeven}\n"
        f"- Win rate: {win_rate:.1f}%\n"
        f"- Total points: {total_points:.2f}\n"
        f"- Total realized R: {total_realized_r:.2f}\n"
        f"- Average result (pts): {avg_result:.2f}\n"
        f"- Average realized R: {avg_realized_r:.2f}\n"
        f"- Average planned R: {avg_planned_r:.2f}\n"
        f"- Most used setup: {best_setup}\n"
        f"- Best trade: {best_trade.get('instrument', 'N/A')} | {best_trade.get('setup', 'N/A')} | {best_trade.get('result_pts', 0):.2f} pts | {best_trade.get('realized_r', 0):.2f}R\n"
        f"- Worst trade: {worst_trade.get('instrument', 'N/A')} | {worst_trade.get('setup', 'N/A')} | {worst_trade.get('result_pts', 0):.2f} pts | {worst_trade.get('realized_r', 0):.2f}R"
    )


def build_coach_report(user_id: str) -> str:
    structured = get_structured_trades(user_id)

    if not structured:
        return "No structured trades logged yet. Use !architect trade-log MNQ 18450 18420 18520 breakout_retest 18515"

    total = len(structured)
    wins = [t for t in structured if t.get("result_pts", 0) > 0]
    losses = [t for t in structured if t.get("result_pts", 0) < 0]

    avg_planned_r = sum(t.get("planned_r", 0) for t in structured) / total
    avg_realized_r = sum(t.get("realized_r", 0) for t in structured) / total
    capture_ratio = (avg_realized_r / avg_planned_r) if avg_planned_r != 0 else 0

    setup_stats = {}
    for trade in structured:
        setup = trade.get("setup", "unknown")
        if setup not in setup_stats:
            setup_stats[setup] = {"count": 0, "wins": 0, "total_r": 0.0}

        setup_stats[setup]["count"] += 1
        setup_stats[setup]["total_r"] += trade.get("realized_r", 0)

        if trade.get("result_pts", 0) > 0:
            setup_stats[setup]["wins"] += 1

    best_setup_text = "Not enough data"
    if setup_stats:
        best_setup = max(
            setup_stats.items(),
            key=lambda item: (
                (item[1]["wins"] / item[1]["count"]) if item[1]["count"] > 0 else 0,
                item[1]["total_r"]
            )
        )

        setup_name = best_setup[0]
        setup_count = best_setup[1]["count"]
        setup_win_rate = (best_setup[1]["wins"] / setup_count) * 100 if setup_count > 0 else 0
        setup_avg_r = best_setup[1]["total_r"] / setup_count if setup_count > 0 else 0

        best_setup_text = f"{setup_name} | Trades: {setup_count} | Win rate: {setup_win_rate:.1f}% | Avg R: {setup_avg_r:.2f}"

    coaching_points = []

    if capture_ratio < 0.7:
        coaching_points.append("You may be cutting winners early. Your average realized R is much lower than your average planned R.")
    elif capture_ratio < 0.9:
        coaching_points.append("You are capturing a decent portion of your planned reward, but there is still room to improve trade management.")
    else:
        coaching_points.append("You are capturing most of your planned reward well. That suggests solid follow-through on trade management.")

    if len(losses) > len(wins):
        coaching_points.append("Losses currently outnumber wins. Tighten selectivity and make sure you are only taking your best setups.")
    elif len(wins) > len(losses):
        coaching_points.append("Wins currently outnumber losses. Keep protecting discipline so good execution does not get diluted by random trades.")

    if total < 5:
        coaching_points.append("Sample size is still small. Focus on logging trades consistently before making big strategic conclusions.")
    else:
        coaching_points.append("You now have enough data to start identifying behavior patterns instead of judging yourself off one trade.")

    biggest_win = max(structured, key=lambda t: t.get("realized_r", 0))
    biggest_loss = min(structured, key=lambda t: t.get("realized_r", 0))

    return (
        "Architect Coach Report:\n"
        f"- Total structured trades reviewed: {total}\n"
        f"- Average planned R: {avg_planned_r:.2f}\n"
        f"- Average realized R: {avg_realized_r:.2f}\n"
        f"- Reward capture ratio: {capture_ratio:.2f}\n"
        f"- Best setup so far: {best_setup_text}\n"
        f"- Biggest winner: {biggest_win.get('instrument', 'N/A')} | {biggest_win.get('setup', 'N/A')} | {biggest_win.get('realized_r', 0):.2f}R\n"
        f"- Biggest loser: {biggest_loss.get('instrument', 'N/A')} | {biggest_loss.get('setup', 'N/A')} | {biggest_loss.get('realized_r', 0):.2f}R\n"
        "\nKey coaching notes:\n"
        + "\n".join([f"- {point}" for point in coaching_points]) +
        "\n\nNext focus:\n"
        "- Keep logging every trade.\n"
        "- Compare your best setup against all others after 10+ trades.\n"
        "- Watch whether realized R keeps lagging planned R."
    )


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


async def send_automatic_morning_brief(guild: discord.Guild):
    guild_id = str(guild.id)
    guild_state = get_guild_state()
    state = guild_state.get(guild_id, {})

    primary_user_id = state.get("primary_user_id", "").strip()
    last_sent_date = state.get("last_morning_brief_date", "").strip()
    today = today_dr()

    if not primary_user_id:
        return
    if last_sent_date == today:
        return
    if not has_meaningful_brief_data(primary_user_id):
        print(f"Morning brief skipped for guild {guild.id}: primary user has no meaningful brief data.")
        return

    channel = get_system_channel(guild, "mission_brief")
    if channel is None:
        return

    brief = build_morning_brief(primary_user_id)
    await channel.send(brief)

    state["last_morning_brief_date"] = today
    guild_state[guild_id] = state
    save_guild_state(guild_state)


async def post_morning_brief_to_system_channel(guild: discord.Guild, user_id: str):
    channel = get_system_channel(guild, "mission_brief")
    if channel is None:
        return False, "I couldn’t find #mission-brief in this server."

    register_guild_user(str(guild.id), user_id)

    if not has_meaningful_brief_data(user_id):
        return False, "I found #mission-brief, but your Architect profile for this user is blank right now. I stopped the post so it wouldn’t publish empty defaults."

    brief = build_morning_brief(user_id)
    await channel.send(brief)

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

    reply = response.output_text

    if not reply or not reply.strip():
        reply = "I understood you, but I didn’t get usable text back. Try rewording that."

    if len(reply) > 1900:
        chunks = [reply[i:i + 1900] for i in range(0, len(reply), 1900)]
        for chunk in chunks:
            await message.channel.send(chunk)
    else:
        await message.channel.send(reply)


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
        if command == "save-book":
            if not body:
                await message.channel.send("Usage: !architect save-book Atomic_Habits James_Clear")
                return

            entry = f"📘 BOOK LOGGED\n{body}"
            await message.channel.send(entry)

            guild = message.guild
            if guild is not None:
                await route_department_report(guild, "knowledge_vault", entry)

            return


        if command == "save-lesson":
            if not body:
                await message.channel.send("Usage: !architect save-lesson Identity_based_habits_are_stronger_than_motivation")
                return

            entry = f"🧠 LESSON SAVED\n{body}"
            await message.channel.send(entry)

            guild = message.guild
            if guild is not None:
                await route_department_report(guild, "knowledge_vault", entry)

            return


        if command == "save-note":
            if not body:
                await message.channel.send("Usage: !architect save-note Review_market_structure_before_entering")
                return
    
            entry = f"📝 NOTE SAVED\n{body}"
            await message.channel.send(entry)
    
            guild = message.guild
            if guild is not None:
                await route_department_report(guild, "knowledge_vault", entry)
    
            return

        if command == "set-body-baseline":
            parts = body.split()
    
            if len(parts) < 15:
                await message.channel.send(
                    "Usage: !architect set-body-baseline 221.6 31 32.8 44.5 145.2 3 15.8 1867 152.8 26.6 15 49.8 7.6 Heavy 45"
                )
                return
    
            set_body_baseline(
                user_id=user_id,
                weight_lb=float(parts[0]),
                body_fat_percent=float(parts[1]),
                bmi=float(parts[2]),
                skeletal_muscle_percent=float(parts[3]),
                muscle_mass_lb=float(parts[4]),
                muscle_storage_ability_level=int(float(parts[5])),
                protein_percent=float(parts[6]),
                bmr_kcal=float(parts[7]),
                fat_free_body_weight_lb=float(parts[8]),
                subcutaneous_fat_percent=float(parts[9]),
                visceral_fat=int(float(parts[10])),
                body_water_percent=float(parts[11]),
                bone_mass_lb=float(parts[12]),
                body_type=parts[13],
                metabolic_age=int(float(parts[14]))
            )
    
            await message.channel.send(
                "Body baseline saved:\n"
                f"- Weight: {float(parts[0]):.1f} lb\n"
                f"- Body Fat: {float(parts[1]):.1f}%\n"
                f"- BMI: {float(parts[2]):.1f}\n"
                f"- Skeletal Muscle: {float(parts[3]):.1f}%\n"
                f"- Muscle Mass: {float(parts[4]):.1f} lb\n"
                f"- BMR: {float(parts[7]):.0f} kcal\n"
                f"- Body Type: {parts[13]}\n"
                f"- Metabolic Age: {int(float(parts[14]))}"
            )
            return
    
        if command == "body-baseline":
            await message.channel.send(build_body_baseline_report(user_id))
            return        
            if command == "set-body-goal":
                parts = body.split()
                if len(parts) < 3:
                    await message.channel.send("Usage: !architect set-body-goal 190 200 11")
                    return
    
                target_low = float(parts[0])
                target_high = float(parts[1])
                target_bf = float(parts[2])
    
                set_body_goal(user_id, target_low, target_high, target_bf)
                await message.channel.send(
                    "Body goal saved:\n"
                    f"- Target weight range: {target_low:.1f} to {target_high:.1f} lb\n"
                    f"- Target body fat: {target_bf:.1f}%"
                )
                return

        if command == "body-goal":
            await message.channel.send(build_body_goal_report(user_id))
            return

        if command == "set-body-change":
            parts = body.split()
            if len(parts) < 3:
                await message.channel.send("Usage: !architect set-body-change 32.6 4.8 7.5")
                return

            weight_change_lb = float(parts[0])
            bmi_change = float(parts[1])
            body_fat_change_percent = float(parts[2])

            set_body_change(user_id, weight_change_lb, bmi_change, body_fat_change_percent)
            await message.channel.send(
                "Body change snapshot saved:\n"
                f"- Weight change: +{weight_change_lb:.1f} lb\n"
                f"- BMI change: +{bmi_change:.1f}\n"
                f"- Body fat change: +{body_fat_change_percent:.1f}%"
            )
            return

        if command == "body-change":
            await message.channel.send(build_body_change_report(user_id))
            return

        if command == "set-activity-baseline":
            parts = body.split()
            if len(parts) < 5:
                await message.channel.send("Usage: !architect set-activity-baseline 900 60 12 10000 5")
                return

            active_calories_daily = float(parts[0])
            exercise_minutes_daily = float(parts[1])
            stand_hours_daily = float(parts[2])
            steps_daily = int(float(parts[3]))
            workouts_per_week = int(float(parts[4]))

            set_activity_baseline(
                user_id=user_id,
                active_calories_daily=active_calories_daily,
                exercise_minutes_daily=exercise_minutes_daily,
                stand_hours_daily=stand_hours_daily,
                steps_daily=steps_daily,
                workouts_per_week=workouts_per_week
            )

            await message.channel.send(
                "Activity baseline saved:\n"
                f"- Active calories daily: {active_calories_daily:.0f}\n"
                f"- Exercise minutes daily: {exercise_minutes_daily:.0f}\n"
                f"- Stand hours daily: {stand_hours_daily:.0f}\n"
                f"- Steps daily: {steps_daily}\n"
                f"- Workouts per week: {workouts_per_week}"
            )
            return

        if command == "activity-baseline":
            await message.channel.send(build_activity_baseline_report(user_id))
            return

        if command == "log-activity":
            parts = body.split()
            if len(parts) < 4:
                await message.channel.send("Usage: !architect log-activity 650 52 9800 lifting_and_incline_walk")
                return

            active_calories = float(parts[0])
            exercise_minutes = float(parts[1])
            steps = int(float(parts[2]))
            activity_type = parts[3]

            log_activity(user_id, active_calories, exercise_minutes, steps, activity_type)
            await message.channel.send(
                "Activity logged:\n"
                f"- Active calories: {active_calories:.0f}\n"
                f"- Exercise minutes: {exercise_minutes:.0f}\n"
                f"- Steps: {steps}\n"
                f"- Activity type: {activity_type}"
            )
            return

        if command == "activity-report":
            await message.channel.send(build_activity_report(user_id))
            return

        if command == "set-profile":
            parts = body.split()
            if len(parts) < 2:
                await message.channel.send("Usage: !architect set-profile 12/24/1986 6:00AM")
                return
       
            set_profile(user_id, parts[0], parts[1])
            await message.channel.send(
                "Profile saved:\n"
                f"- Birth date: {parts[0]}\n"
                f"- Birth time: {parts[1]}"
            )
            return

        if command == "profile":
            await message.channel.send(build_profile_identity_report(user_id))
            return

        if command == "set-transformation-goal":
            parts = body.split()
            if len(parts) < 5:
                await message.channel.send(
                    "Usage: !architect set-transformation-goal 221.6 190 200 2026-06-01 lean-aesthetic"
                )
                return

            set_transformation_goal(
                user_id=user_id,
                current_weight_lb=float(parts[0]),
                target_weight_low_lb=float(parts[1]),
                target_weight_high_lb=float(parts[2]),
                deadline_date=parts[3],
                goal_type=parts[4]
            )

            await message.channel.send(
                "Transformation goal saved:\n"
                f"- Current weight: {float(parts[0]):.1f} lb\n"
                f"- Target range: {float(parts[1]):.1f} to {float(parts[2]):.1f} lb\n"
                f"- Deadline: {parts[3]}\n"
                f"- Goal type: {parts[4]}"
            )
            return

        if command == "transformation-status":
            await message.channel.send(build_transformation_status_report(user_id))
            return

        if command == "set-fitness-profile":
            parts = body.split()
            if len(parts) < 8:
                await message.channel.send(
                    "Usage: !architect set-fitness-profile hybrid base_building 5 home_bodyweight_soon_gym 300_pushups_daily pushups_situps_squats_lunges_fullbody bodyweight_aesthetics_to_lean_bulk current_starting_phase"
                )
                return

            set_fitness_profile(
                user_id=user_id,
                current_training_mode=parts[0],
                current_phase=parts[1],
                training_days_available=int(float(parts[2])),
                available_resources=parts[3],
                current_challenge=parts[4],
                movement_base=parts[5],
                physique_target=parts[6],
                starting_point_notes=parts[7]
            )

            await message.channel.send(
                "Fitness profile saved:\n"
                f"- Current training mode: {parts[0]}\n"
                f"- Current phase: {parts[1]}\n"
                f"- Training days available: {int(float(parts[2]))}\n"
                f"- Available resources: {parts[3]}\n"
                f"- Current challenge: {parts[4]}\n"
                f"- Movement base: {parts[5]}\n"
                f"- Physique target: {parts[6]}\n"
                f"- Starting point notes: {parts[7]}"
            )
            return

        if command == "show-fitness-profile":
            await message.channel.send(build_fitness_profile_report(user_id))
            return

        if command == "update-resources":
            if not body:
                await message.channel.send("Usage: !architect update-resources full_gym_home_cardio")
                return
            update_resources(user_id, body)
            await message.channel.send(f"Resources updated: {body}")
            return

        if command == "update-training-days":
            if not body:
                await message.channel.send("Usage: !architect update-training-days 6")
                return
            training_days = int(float(body))
            update_training_days(user_id, training_days)
            await message.channel.send(f"Training days updated: {training_days}")
            return

        if command == "update-fitness-mode":
            parts = body.split()
            if len(parts) < 2:
                await message.channel.send("Usage: !architect update-fitness-mode hybrid strength_recomp")
                return
            update_fitness_mode(user_id, parts[0], parts[1])
            await message.channel.send(
                "Fitness mode updated:\n"
                f"- Training mode: {parts[0]}\n"
                f"- Phase: {parts[1]}"
            )
            return

        if command == "adjust-goal-timeline":
            if not body:
                await message.channel.send("Usage: !architect adjust-goal-timeline 2026-06-15")
                return
            adjust_goal_timeline(user_id, body)
            await message.channel.send(f"Transformation deadline updated: {body}")
            return

        if command == "fitness-adjustment":
            report = build_fitness_adjustment_report(user_id)

            await message.channel.send(report)

            guild = message.guild
            await send_to_department(guild, "fitness_lab", report)

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

            workout_phase = parts[0]
            phase_duration_weeks = int(float(parts[1]))
            set_workout_phase(user_id, workout_phase, phase_duration_weeks)

            await message.channel.send(
                "Workout phase saved:\n"
                f"- Phase: {workout_phase}\n"
                f"- Duration: {phase_duration_weeks} week(s)"
            )
            return

        if command == "update-equipment":
            if not body:
                await message.channel.send("Usage: !architect update-equipment kettlebell weighted_vest bands")
                return

            equipment_items = body.split()
            update_equipment(user_id, equipment_items)

            await message.channel.send(
                "Equipment updated:\n"
                f"- {', '.join(equipment_items)}"
            )
            return

        if command == "weekly-workout-plan":
            await message.channel.send(build_weekly_workout_plan(user_id))
            return

        if command == "today-workout":
            await message.channel.send(build_today_workout(user_id))
            return

        if command == "pushup-plan":
            parts = body.split()
            total_target = 300
            max_set = 25

            if len(parts) >= 1:
                total_target = int(float(parts[0]))
            if len(parts) >= 2:
                max_set = int(float(parts[1]))

            await message.channel.send(build_pushup_plan(user_id, total_target, max_set))
            return

        if command == "log-weight":
            if not body:
                await message.channel.send("Usage: !architect log-weight 186.4")
                return
            log_weight(user_id, body)
            await message.channel.send(f"Logged weight: {body}")
            return

        if command == "log-goal":
            if not body:
                await message.channel.send("Usage: !architect log-goal Stay disciplined this week")
                return
            log_goal(user_id, body)
            await message.channel.send(f"Logged goal: {body}")
            return

        if command == "log-habit":
            if not body:
                await message.channel.send("Usage: !architect log-habit cardio complete")
                return
            log_habit(user_id, body)
            await message.channel.send(f"Logged habit: {body}")
            return

        if command == "checkin":
            parts = body.split()
            if len(parts) < 6:
                await message.channel.send("Usage: !architect checkin energy 8 motivation 7 focus 9")
                return
            try:
                energy_value = parts[1]
                motivation_value = parts[3]
                focus_value = parts[5]
            except Exception:
                await message.channel.send("Usage: !architect checkin energy 8 motivation 7 focus 9")
                return

            log_checkin(user_id, energy_value, motivation_value, focus_value)
            await message.channel.send(
                f"Check-in logged: Energy {energy_value} | Motivation {motivation_value} | Focus {focus_value}"
            )
            return

        if command == "log-sleep":
            if not body:
                await message.channel.send("Usage: !architect log-sleep 7.5")
                return
            sleep_hours = float(body)
            log_sleep(user_id, sleep_hours)
            await message.channel.send(f"Sleep logged: {sleep_hours:.2f} hours")
            return

        if command == "log-mood":
            if not body:
                await message.channel.send("Usage: !architect log-mood 8")
                return
            mood_score = float(body)
            log_mood(user_id, mood_score)
            await message.channel.send(f"Mood logged: {mood_score:.2f}")
            return

        if command == "log-focus":
            if not body:
                await message.channel.send("Usage: !architect log-focus 7")
                return
            focus_score = float(body)
            log_focus_score(user_id, focus_score)
            await message.channel.send(f"Focus logged: {focus_score:.2f}")
            return

        if command == "log-workout":
            if not body:
                await message.channel.send("Usage: !architect log-workout pushups 300")
                return
            log_workout(user_id, body)
            await message.channel.send(f"Workout logged: {body}")
            return

        if command == "life-report":
            await message.channel.send(build_life_report(user_id))
            return

        if command == "set-week-mode":
            if not body:
                await message.channel.send("Usage: !architect set-week-mode trading")
                return
            set_week_mode(user_id, body)
            await message.channel.send(f"Week mode set: {body}")
            return

        if command == "set-week-focus":
            if not body:
                await message.channel.send("Usage: !architect set-week-focus trading fitness knowledge")
                return
            focus_items = body.split()
            set_week_focus(user_id, focus_items)
            await message.channel.send(f"Week focus set: {', '.join(focus_items)}")
            return

        if command == "set-training-mode":
            if not body:
                await message.channel.send("Usage: !architect set-training-mode calisthenics")
                return
            set_training_mode(user_id, body)
            await message.channel.send(f"Training mode set: {body}")
            return

        if command == "set-nutrition":
            if not body:
                await message.channel.send("Usage: !architect set-nutrition lean-bulk")
                return
            set_nutrition_mode(user_id, body)
            await message.channel.send(f"Nutrition mode set: {body}")
            return

        if command == "set-daily-goal":
            if not body:
                await message.channel.send("Usage: !architect set-daily-goal pushups 300")
                return
            set_daily_goal(user_id, body)
            await message.channel.send(f"Daily goal set: {body}")
            return

        if command == "watchlist":
            if not body:
                await message.channel.send("Usage: !architect watchlist MNQ US30 TSLA")
                return
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
            if not body:
                await message.channel.send("Usage: !architect save-note your note")
                return
            log_note(user_id, body)
            await message.channel.send(f"Note saved: {body}")
            return

        if command == "save-idea":
            if not body:
                await message.channel.send("Usage: !architect save-idea your idea")
                return
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
            if not body:
                await message.channel.send("Usage: !architect log-pnl 250")
                return
            pnl_value = float(body)
            log_pnl(user_id, pnl_value)
            await message.channel.send(f"PnL logged: {pnl_value:.2f}")
            return

        if command == "pnl-report":
            await message.channel.send(build_pnl_report(user_id))
            return

        if command == "win":
            if not body:
                await message.channel.send("Usage: !architect win Executed with patience")
                return
            log_win(user_id, body)
            await message.channel.send(f"Win logged: {body}")
            return

        if command == "mistake":
            if not body:
                await message.channel.send("Usage: !architect mistake Entered before confirmation")
                return
            log_mistake(user_id, body)
            await message.channel.send(f"Mistake logged: {body}")
            return

        if command == "daily-report":
            await message.channel.send(build_daily_report(user_id))
            return

        if command == "show-profile":
            profile = build_profile_text(user_id)
            await message.channel.send(profile)
            return

        if command == "weekly-report":
            report = build_weekly_report(user_id)
            await message.channel.send(report)
            return

        if command == "trade-review":
            if not body:
                await message.channel.send(
                    "Usage: !architect trade-review Instrument: MNQ | Entry: 18450 | Stop: 18420 | Target: 18520 | Reason: breakout retest | Result: +65 pts"
                )
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
                await message.channel.send(
                    "Usage: !architect trade-log MNQ 18450 18420 18520 breakout_retest 18515"
                )
                return

            instrument = parts[0]
            entry = float(parts[1])
            stop = float(parts[2])
            target = float(parts[3])
            setup = parts[4]
            exit_price = float(parts[5])

            calc = log_trade_structured(
                user_id=user_id,
                instrument=instrument,
                entry=entry,
                stop=stop,
                target=target,
                setup=setup,
                exit_price=exit_price
            )

            await message.channel.send(
                "Trade logged:\n"
                f"{instrument} | Entry {entry} | Stop {stop} | Target {target} | Exit {exit_price}\n"
                f"Setup: {setup}\n"
                f"Risk: {calc['risk_pts']:.2f} pts\n"
                f"Target distance: {calc['target_pts']:.2f} pts\n"
                f"Result: {calc['result_pts']:.2f} pts\n"
                f"Planned R: {calc['planned_r']:.2f}\n"
                f"Realized R: {calc['realized_r']:.2f}"
            )
            return

        if command == "stats":
            stats = build_trade_stats(user_id)
            await message.channel.send(stats)
            return

        if command == "dashboard":
            dashboard = build_dashboard(user_id)
            await message.channel.send(dashboard)
            return

        if command == "coach":
            coach_report = build_coach_report(user_id)
            await message.channel.send(coach_report)
            return
        if command == "set-watchlist":
            watchlist = body.strip()
            if not watchlist:
                await message.channel.send("Usage: !architect set-watchlist MNQ US30 NAS100 TSLA")
                return
    
            save_note(user_id, f"WATCHLIST::{watchlist}")
            await message.channel.send(
                f" ARTEMIS WATCHLIST SET\n\nTracking:\n{watchlist}\n\nArtemis is now locked into your market focus."
            )
            return
    
        if command == "artemis-brief":
            await message.channel.send(
                " ARTEMIS BRIEF\n\n"
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
    
        if command == "artemis-talk":
            await message.channel.send(
                " ARTEMIS CHECK-IN\n\n"
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
        await run_ai_reply(message, prompt)

    except Exception as e:
        print(f"Error in on_message: {e}")
        await message.channel.send(
            f"Something went wrong while processing that request.\n\nError: {str(e)[:180]}"
        )


bot.run(DISCORD_TOKEN)
