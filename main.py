import os
import discord
import logging
from dotenv import load_dotenv
from discord.ext import commands
from src.utils.opus_loader import load_opus

load_dotenv()
load_opus()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler()])

@bot.event
async def on_ready():
    logging.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    
    try:
        await bot.load_extension('src.cogs.radio')
        logging.info("Radio commands cog loaded successfully.")
    except Exception as e:
        logging.error(f"Error loading Radio cog: {e}")

    try:
        await bot.load_extension('src.cogs.voice_manager')
        logging.info("Voice manager cog loaded successfully.")
    except Exception as e:
        logging.error(f"Error loading Voice Manager cog: {e}")
    
    try:
        await bot.tree.sync()
        logging.info("Commands synced successfully.")
    except Exception as e:
        logging.error(f"Error syncing commands: {e}")
    
    invite_url = f"https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=3145728&scope=bot%20applications.commands"
    logging.info(f"Invite URL: {invite_url}")

if __name__ == "__main__":
    token = os.getenv("DISCORD_API_TOKEN")
    if not token:
        raise Exception("No Discord API Token available. Please set the DISCORD_API_TOKEN environment variable.")
    else:
        bot.run(token)
