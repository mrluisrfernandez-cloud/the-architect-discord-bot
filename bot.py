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


def log_weight(user_id: str, value: str):
    memory = get_memory()
    user_data = memory.get(user_id, {
        "weights": [],
        "goals": [],
        "notes": []
    })

    user_data["weights"].append({
        "value": value,
        "timestamp": datetime.utcnow().isoformat()
    })

    memory[user_id] = user_data
    save_memory(memory)


def log_goal(user_id: str, goal: str):
    memory = get_memory()
    user_data = memory.get(user_id, {
        "weights": [],
        "goals": [],
        "notes": []
    })

    user_data["goals"].append({
        "text": goal,
        "timestamp": datetime.utcnow().isoformat()
    })

    memory[user_id] = user_data
    save_memory(memory)


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


def build_profile_text(user_id: str) -> str:
    memory = get_memory()
    trades = get_trades()

    user_memory = memory.get(user_id, {})
    user_trades = trades.get(user_id, [])

    weights = user_memory.get("weights", [])
    goals = user_memory.get("goals", [])

    latest_weight = weights[-1]["value"] if weights else "No weight logged yet"
    latest_goal = goals[-1]["text"] if goals else "No goal logged yet"

    return (
        f"Profile snapshot:\n"
        f"- Latest weight: {latest_weight}\n"
        f"- Latest goal: {latest_goal}\n"
        f"- Total trades logged: {len(user_trades)}"
    )


def build_weekly_report(user_id: str) -> str:
    memory = get_memory()
    trades = get_trades()

    user_memory = memory.get(user_id, {})
    user_trades = trades.get(user_id, [])

    weights = user_memory.get("weights", [])
    goals = user_memory.get("goals", [])

    report_lines = [
        "Weekly performance snapshot:",
        f"- Weight logs: {len(weights)}",
        f"- Goals logged: {len(goals)}",
        f"- Trades logged: {len(user_trades)}",
    ]

    if weights:
        report_lines.append(f"- Latest weight: {weights[-1]['value']}")
    if goals:
        report_lines.append(f"- Latest goal: {goals[-1]['text']}")

    return "\n".join(report_lines)


def build_trade_stats(user_id: str) -> str:
    trades = get_trades()
    user_trades = trades.get(user_id, [])

    structured = [t for t in user_trades if t.get("type") == "structured"]

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

        await run_ai_reply(message, prompt)

    except Exception as e:
        print(f"Error in on_message: {e}")
        await message.channel.send(
            f"Something went wrong while processing that request.\n\nError: `{str(e)[:180]}`"
        )


bot.run(DISCORD_TOKEN)
