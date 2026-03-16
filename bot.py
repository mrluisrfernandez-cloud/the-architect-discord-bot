import os
import discord
from openai import OpenAI

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)


def get_channel_mode(channel_name: str) -> str:
    name = (channel_name or "").lower()

    if "trading" in name:
        return (
            "You are Architect in Trading Desk mode. "
            "Help with trading psychology, futures, options, risk, structure, journaling, and execution. "
            "Be practical, clear, and disciplined. Do not be reckless."
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
    if "builder" in name:
        return (
            "You are Architect in Builder Lab mode. "
            "Help with business ideas, coding, systems, workflows, ecommerce, and building projects. "
            "Be strategic, structured, and creative."
        )
    if "cosmic" in name:
        return (
            "You are Architect in Cosmic Reflection mode. "
            "Help with reflection, mindset, journaling, spiritual perspective, and thoughtful motivation. "
            "Be poetic but grounded."
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


def extract_user_prompt(message: discord.Message) -> str:
    content = message.content.strip()

    if content.startswith("!architect"):
        return content.replace("!architect", "", 1).strip()

    if bot.user and bot.user.mentioned_in(message):
        mention_1 = f"<@{bot.user.id}>"
        mention_2 = f"<@!{bot.user.id}>"
        content = content.replace(mention_1, "").replace(mention_2, "").strip()
        return content

    return ""


@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")


@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return

    is_command = message.content.strip().startswith("!architect")
    is_mention = bot.user is not None and bot.user.mentioned_in(message)

    if not is_command and not is_mention:
        return

    prompt = extract_user_prompt(message)

    if not prompt:
        await message.channel.send(
            "Give me something after `!architect` or mention me with a question."
        )
        return

    system_prompt = get_channel_mode(message.channel.name)

    try:
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

    except Exception as e:
        print(f"Error in on_message: {e}")
        await message.channel.send(
            f"Something went wrong while processing that request.\n\nError: `{str(e)[:180]}`"
        )


bot.run(DISCORD_TOKEN)
