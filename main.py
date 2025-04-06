"""
NTS Discord Bot - Main entry point
A Discord bot that streams NTS Radio channels in voice channels.
"""
import os
import discord
from dotenv import load_dotenv
from discord.ext import commands
from src.utils.opus_loader import load_opus

# Load environment variables
load_dotenv()

# Load Opus for voice support
load_opus()

# Set up intents for the bot
intents = discord.Intents.default()
intents.message_content = True

# Initialize the bot with command prefix and intents
bot = commands.Bot(command_prefix='/', intents=intents)


@bot.event
async def on_ready():
    """Event triggered when the bot is ready and connected to Discord."""
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    
    # Load cogs
    try:
        await bot.load_extension('src.cogs.radio')
        print("Radio commands cog loaded successfully.")
    except Exception as e:
        print(f"Error loading Radio cog: {e}")
    
    # Sync application commands
    try:
        await bot.tree.sync()
        print("Commands synced successfully.")
    except Exception as e:
        print(f"Error syncing commands: {e}")
    
    print("Bot is ready!")


if __name__ == "__main__":
    # Get Discord API token from environment variable
    token = os.getenv("DISCORD_API_TOKEN")
    if not token:
        raise Exception("No Discord API Token available. Please set the DISCORD_API_TOKEN environment variable.")
    else:
        # Start the bot
        bot.run(token)
