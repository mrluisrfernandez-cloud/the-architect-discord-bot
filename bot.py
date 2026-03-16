import discord
import os
from openai import OpenAI

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

    if not message.content.startswith("!architect"):
        return

    prompt = message.content.replace("!architect", "", 1).strip()

    if not prompt:
        await message.channel.send("Please add a prompt after `!architect`.")
        return

    try:
        async with message.channel.typing():
            response = client.responses.create(
                model="gpt-5-mini",
                input=prompt
            )

        reply = response.output_text

        if not reply or not reply.strip():
            reply = "I understood your request, but I didn’t get usable text back. Try rewording it."

        # Discord message limit safety
        if len(reply) > 1900:
            chunks = [reply[i:i+1900] for i in range(0, len(reply), 1900)]
            for chunk in chunks:
                await message.channel.send(chunk)
        else:
            await message.channel.send(reply)

    except Exception as e:
        print(f"Error in on_message: {e}")
        await message.channel.send(f"Something went wrong while processing that request.\n\nError: `{str(e)[:150]}`")


bot.run(DISCORD_TOKEN)
