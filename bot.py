import discord
import os
from openai import OpenAI

# Load tokens from environment
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")

@bot.event
async def on_message(message):

    if message.author == bot.user:
        return

    if message.content.startswith("!architect"):

        prompt = message.content.replace("!architect", "")

        response = client.responses.create(
            model="gpt-5-mini",
            input=prompt
        )

        reply = response.output_text

        await message.channel.send(reply)

bot.run(DISCORD_TOKEN)
