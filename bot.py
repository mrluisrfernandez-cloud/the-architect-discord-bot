import os
import json
from datetime import datetime
import discord
from openai import OpenAI

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)

MEMORY_FILE = "memory.json"
TRADES_FILE = "trades.json"


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


def get_channel_mode(channel_name: str) -> str:
    name = (channel_name or "").lower()

    if "trading" in name:
        return (
            "You are Architect in Trading Desk mode. "
            "Help with trading psychology, futures, options, risk, structure, journaling, and execution. "
            "Be practical, clear, and disciplined."
        )
    if "fitness" in name:
        return (
            "You are Architect in Fitness Lab mode. "
            "Help with workouts, recovery, performance, consistency, and body recomposition. "
            "Be motivating, structured, and practical."
        )
    if "nutrition" in name:
        return (
            "You are Architect in Nutrition Lab mode. "
            "Help with meals, macros, simple meal prep, healthy food choices, and consistency. "
            "Be practical and easy to follow."
        )
    if "performance" in name:
        return (
            "You are Architect in Performance Report mode. "
            "Help review progress, patterns, discipline, wins, mistakes, and next steps. "
            "Be honest, sharp, and constructive."
        )

    return (
        "You are Architect, a sharp personal AI assistant inside Discord. "
        "You help with strategy, productivity, mindset, fitness, trading, learning, and building a better life. "
        "Keep responses clear, useful, and motivating."
    )


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


def get_or_create_user_memory(user_id: str):
    memory = get_memory()
    user_data = memory.get(user_id, {
        "weights": [],
        "goals": [],
        "notes": [],
        "ideas": [],
        "habits": [],
        "checkins": []
    })

    user_data.setdefault("weights", [])
    user_data.setdefault("goals", [])
    user_data.setdefault("notes", [])
    user_data.setdefault("ideas", [])
    user_data.setdefault("habits", [])
    user_data.setdefault("checkins", [])

    return memory, user_data


def log_weight(user_id: str, value: str):
    memory, user_data = get_or_create_user_memory(user_id)

    user_data["weights"].append({
        "value": value,
        "timestamp": datetime.utcnow().isoformat()
    })

    memory[user_id] = user_data
    save_memory(memory)


def log_goal(user_id: str, goal: str):
    memory, user_data = get_or_create_user_memory(user_id)

    user_data["goals"].append({
        "text": goal,
        "timestamp": datetime.utcnow().isoformat()
    })

    memory[user_id] = user_data
    save_memory(memory)


def log_habit(user_id: str, habit_text: str):
    memory, user_data = get_or_create_user_memory(user_id)

    user_data["habits"].append({
        "text": habit_text,
        "timestamp": datetime.utcnow().isoformat()
    })

    memory[user_id] = user_data
    save_memory(memory)


def log_checkin(user_id: str, energy: str, motivation: str, focus: str):
    memory, user_data = get_or_create_user_memory(user_id)

    user_data["checkins"].append({
        "energy": energy,
        "motivation": motivation,
        "focus": focus,
        "timestamp": datetime.utcnow().isoformat()
    })

    memory[user_id] = user_data
    save_memory(memory)


def log_note(user_id: str, note: str):
    memory, user_data = get_or_create_user_memory(user_id)

    user_data["notes"].append({
        "text": note,
        "timestamp": datetime.utcnow().isoformat()
    })

    memory[user_id] = user_data
    save_memory(memory)


def log_idea(user_id: str, idea: str):
    memory, user_data = get_or_create_user_memory(user_id)

    user_data["ideas"].append({
        "text": idea,
        "timestamp": datetime.utcnow().isoformat()
    })

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


def log_trade_raw(user_id: str, raw_trade: str):
    trades = get_trades()
    user_trades = trades.get(user_id, [])

    user_trades.append({
        "type": "raw_review",
        "raw": raw_trade,
        "timestamp": datetime.utcnow().isoformat()
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
        "timestamp": datetime.utcnow().isoformat()
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

    report_lines = [
        "Weekly performance snapshot:",
        f"- Weight logs: {len(weights)}",
        f"- Goals logged: {len(goals)}",
        f"- Habits logged: {len(habits)}",
        f"- Check-ins logged: {len(checkins)}",
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


@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")


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

    try:
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
