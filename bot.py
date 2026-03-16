import os
import json
from datetime import datetime, timezone
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

MORNING_BRIEF_HOUR = 8
MORNING_BRIEF_MINUTE = 0


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
    user_data.setdefault("context", {})
    user_data["context"].setdefault("week_mode", "")
    user_data["context"].setdefault("week_focus", [])
    user_data["context"].setdefault("training_mode", "")
    user_data["context"].setdefault("nutrition_mode", "")
    user_data["context"].setdefault("daily_goals", [])
    user_data["context"].setdefault("watchlist", [])

    return memory, user_data


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
        return "No PnL logs saved yet. Use `!architect log-pnl 250`"

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

    today_pnl_total = sum(x["value"] for x in pnl_today)

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

    if not sleep_logs and not mood_logs and not focus_logs and not workouts:
        return "No life performance logs yet. Use `!architect log-sleep`, `!architect log-mood`, `!architect log-focus`, and `!architect log-workout`."

    avg_sleep = (
        sum(x["hours"] for x in sleep_logs) / len(sleep_logs) if sleep_logs else 0
    )
    avg_mood = (
        sum(x["score"] for x in mood_logs) / len(mood_logs) if mood_logs else 0
    )
    avg_focus = (
        sum(x["score"] for x in focus_logs) / len(focus_logs) if focus_logs else 0
    )

    return (
        "Architect Life Performance Report:\n"
        f"- Sleep logs: {len(sleep_logs)}\n"
        f"- Average sleep: {avg_sleep:.2f} hrs\n"
        f"- Mood logs: {len(mood_logs)}\n"
        f"- Average mood: {avg_mood:.2f}\n"
        f"- Focus logs: {len(focus_logs)}\n"
        f"- Average focus: {avg_focus:.2f}\n"
        f"- Workouts logged: {len(workouts)}\n"
        f"- Habits logged: {len(habits)}\n"
        f"- Notes captured: {len(notes)}\n"
        f"- Ideas captured: {len(ideas)}"
    )


def build_week_plan(user_id: str):
    memory = get_memory()
    user_data = memory.get(user_id, {})
    context = user_data.get("context", {})

    week_mode = context.get("week_mode", "Not set")
    week_focus = context.get("week_focus", [])
    training_mode = context.get("training_mode", "Not set")
    nutrition_mode = context.get("nutrition_mode", "Not set")
    watchlist = context.get("watchlist", [])
    daily_goals = context.get("daily_goals", [])

    latest_goal = daily_goals[-1]["text"] if daily_goals else "No daily goal set"

    focus_text = ", ".join(week_focus) if week_focus else "Not set"
    watchlist_text = ", ".join(watchlist) if watchlist else "Not set"

    return (
        "Architect Week Plan:\n"
        f"- Week mode: {week_mode}\n"
        f"- Week focus: {focus_text}\n"
        f"- Training mode: {training_mode}\n"
        f"- Nutrition mode: {nutrition_mode}\n"
        f"- Watchlist: {watchlist_text}\n"
        f"- Latest daily goal: {latest_goal}"
    )


def build_morning_brief(user_id: str):
    memory = get_memory()
    user_data = memory.get(user_id, {})
    context = user_data.get("context", {})

    today = today_dr()
    today_pretty = dr_now().strftime("%A, %B %d, %Y")

    sleep_today = [x for x in user_data.get("sleep_logs", []) if x["date"] == today]
    mood_today = [x for x in user_data.get("mood_logs", []) if x["date"] == today]
    focus_today = [x for x in user_data.get("focus_logs", []) if x["date"] == today]

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
    if str(week_mode).lower() == "no-trading":
        recommendation = "Trading mode is off this week. Focus on recovery, learning, fitness, and system refinement."
    elif str(training_mode).lower() == "calisthenics":
        recommendation = "Training mode is calisthenics. Get your volume done early and keep nutrition aligned with recovery."
    elif str(training_mode).lower() == "hybrid":
        recommendation = "Training mode is hybrid. Balance strength, conditioning, and recovery without losing consistency."

    return (
        "Architect Morning Brief:\n"
        f"- Date: {today_pretty}\n"
        f"- Week mode: {week_mode}\n"
        f"- Week focus: {focus_area_text}\n"
        f"- Training mode: {training_mode}\n"
        f"- Nutrition mode: {nutrition_mode}\n"
        f"- Daily goal: {latest_goal}\n"
        f"- Watchlist: {watchlist_text}\n"
        f"- Sleep: {sleep_text}\n"
        f"- Mood: {mood_text}\n"
        f"- Focus: {focus_text}\n"
        f"- Recommendation: {recommendation}"
    )


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

    latest_weight = weights[-1]["value"] if weights else "No weight logged yet"
    latest_goal = goals[-1]["text"] if goals else "No goal logged yet"
    latest_habit = habits[-1]["text"] if habits else "No habits logged yet"

    if checkins:
        latest_checkin = checkins[-1]
        latest_checkin_text = (
            f"Energy {latest_checkin['energy']} | "
            f"Motivation {latest_checkin['motivation']} | "
            f"Focus {latest_checkin['focus']}"
        )
    else:
        latest_checkin_text = "No check-in logged yet"

    return (
        "Profile snapshot:\n"
        f"- Latest weight: {latest_weight}\n"
        f"- Latest goal: {latest_goal}\n"
        f"- Latest habit: {latest_habit}\n"
        f"- Latest check-in: {latest_checkin_text}\n"
        f"- Total trades logged: {len(user_trades)}"
    )


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
        f"- PnL logs: {len(pnl_logs)}",
        f"- Wins logged: {len(wins)}",
        f"- Mistakes logged: {len(mistakes)}",
        f"- Trades logged: {len(user_trades)}",
    ]

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
        return "No structured trades logged yet. Use `!architect trade-log MNQ 18450 18420 18520 breakout_retest 18515`"

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
        return "No structured trades logged yet. Use `!architect trade-log MNQ 18450 18420 18520 breakout_retest 18515`"

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
        return "No structured trades logged yet. Use `!architect trade-log MNQ 18450 18420 18520 breakout_retest 18515`"

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
            setup_stats[setup] = {
                "count": 0,
                "wins": 0,
                "total_r": 0.0
            }

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

        best_setup_text = (
            f"{setup_name} | Trades: {setup_count} | Win rate: {setup_win_rate:.1f}% | Avg R: {setup_avg_r:.2f}"
        )

    coaching_points = []

    if capture_ratio < 0.7:
        coaching_points.append(
            "You may be cutting winners early. Your average realized R is much lower than your average planned R."
        )
    elif capture_ratio < 0.9:
        coaching_points.append(
            "You are capturing a decent portion of your planned reward, but there is still room to improve trade management."
        )
    else:
        coaching_points.append(
            "You are capturing most of your planned reward well. That suggests solid follow-through on trade management."
        )

    if len(losses) > len(wins):
        coaching_points.append(
            "Losses currently outnumber wins. Tighten selectivity and make sure you are only taking your best setups."
        )
    elif len(wins) > len(losses):
        coaching_points.append(
            "Wins currently outnumber losses. Keep protecting discipline so good execution does not get diluted by random trades."
        )

    if total < 5:
        coaching_points.append(
            "Sample size is still small. Focus on logging trades consistently before making big strategic conclusions."
        )
    else:
        coaching_points.append(
            "You now have enough data to start identifying behavior patterns instead of judging yourself off one trade."
        )

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
        return False, "I couldn’t find `#mission-brief` in this server."

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
        await message.channel.send("Give me something after `!architect`.")
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

        if command == "log-weight":
            if not body:
                await message.channel.send("Usage: `!architect log-weight 186.4`")
                return
            log_weight(user_id, body)
            await message.channel.send(f"Logged weight: {body}")
            return

        if command == "log-goal":
            if not body:
                await message.channel.send("Usage: `!architect log-goal Stay disciplined this week`")
                return
            log_goal(user_id, body)
            await message.channel.send(f"Logged goal: {body}")
            return

        if command == "log-habit":
            if not body:
                await message.channel.send("Usage: `!architect log-habit cardio complete`")
                return
            log_habit(user_id, body)
            await message.channel.send(f"Logged habit: {body}")
            return

        if command == "checkin":
            parts = body.split()

            if len(parts) < 6:
                await message.channel.send("Usage: `!architect checkin energy 8 motivation 7 focus 9`")
                return

            try:
                energy_value = parts[1]
                motivation_value = parts[3]
                focus_value = parts[5]
            except Exception:
                await message.channel.send("Usage: `!architect checkin energy 8 motivation 7 focus 9`")
                return

            log_checkin(user_id, energy_value, motivation_value, focus_value)
            await message.channel.send(
                f"Check-in logged: Energy {energy_value} | Motivation {motivation_value} | Focus {focus_value}"
            )
            return

        if command == "log-sleep":
            if not body:
                await message.channel.send("Usage: `!architect log-sleep 7.5`")
                return
            sleep_hours = float(body)
            log_sleep(user_id, sleep_hours)
            await message.channel.send(f"Sleep logged: {sleep_hours:.2f} hours")
            return

        if command == "log-mood":
            if not body:
                await message.channel.send("Usage: `!architect log-mood 8`")
                return
            mood_score = float(body)
            log_mood(user_id, mood_score)
            await message.channel.send(f"Mood logged: {mood_score:.2f}")
            return

        if command == "log-focus":
            if not body:
                await message.channel.send("Usage: `!architect log-focus 7`")
                return
            focus_score = float(body)
            log_focus_score(user_id, focus_score)
            await message.channel.send(f"Focus logged: {focus_score:.2f}")
            return

        if command == "log-workout":
            if not body:
                await message.channel.send("Usage: `!architect log-workout pushups 300`")
                return
            log_workout(user_id, body)
            await message.channel.send(f"Workout logged: {body}")
            return

        if command == "life-report":
            await message.channel.send(build_life_report(user_id))
            return

        if command == "set-week-mode":
            if not body:
                await message.channel.send("Usage: `!architect set-week-mode trading`")
                return
            set_week_mode(user_id, body)
            await message.channel.send(f"Week mode set: {body}")
            return

        if command == "set-week-focus":
            if not body:
                await message.channel.send("Usage: `!architect set-week-focus trading fitness knowledge`")
                return
            focus_items = body.split()
            set_week_focus(user_id, focus_items)
            await message.channel.send(f"Week focus set: {', '.join(focus_items)}")
            return

        if command == "set-training-mode":
            if not body:
                await message.channel.send("Usage: `!architect set-training-mode calisthenics`")
                return
            set_training_mode(user_id, body)
            await message.channel.send(f"Training mode set: {body}")
            return

        if command == "set-nutrition":
            if not body:
                await message.channel.send("Usage: `!architect set-nutrition lean-bulk`")
                return
            set_nutrition_mode(user_id, body)
            await message.channel.send(f"Nutrition mode set: {body}")
            return

        if command == "set-daily-goal":
            if not body:
                await message.channel.send("Usage: `!architect set-daily-goal pushups 300`")
                return
            set_daily_goal(user_id, body)
            await message.channel.send(f"Daily goal set: {body}")
            return

        if command == "watchlist":
            if not body:
                await message.channel.send("Usage: `!architect watchlist MNQ US30 TSLA`")
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
                await message.channel.send("Usage: `!architect save-note your note`")
                return
            log_note(user_id, body)
            await message.channel.send(f"Note saved: {body}")
            return

        if command == "save-idea":
            if not body:
                await message.channel.send("Usage: `!architect save-idea your idea`")
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
                await message.channel.send("Usage: `!architect log-pnl 250`")
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
                await message.channel.send("Usage: `!architect win Executed with patience`")
                return
            log_win(user_id, body)
            await message.channel.send(f"Win logged: {body}")
            return

        if command == "mistake":
            if not body:
                await message.channel.send("Usage: `!architect mistake Entered before confirmation`")
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
                    "Usage: `!architect trade-review Instrument: MNQ | Entry: 18450 | Stop: 18420 | Target: 18520 | Reason: breakout retest | Result: +65 pts`"
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
                    "Usage: `!architect trade-log MNQ 18450 18420 18520 breakout_retest 18515`"
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

        await run_ai_reply(message, prompt)

    except Exception as e:
        print(f"Error in on_message: {e}")
        await message.channel.send(
            f"Something went wrong while processing that request.\n\nError: `{str(e)[:180]}`"
        )


bot.run(DISCORD_TOKEN)
