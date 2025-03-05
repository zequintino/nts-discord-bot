import os
import discord
from dotenv import load_dotenv
from discord.ext import commands
import aiohttp
import json

# Load Opus library for voice support
if not discord.opus.is_loaded():
    discord.opus.load_opus('/opt/homebrew/Cellar/opus/1.5.2/lib/libopus.dylib')
else:
    print("Opus library is already loaded")

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        await bot.tree.sync()
        print("Commands synced successfully.")
    except Exception as e:
        print(f"Error syncing commands: {e}")



@bot.hybrid_command(name="live_on_1", help="live on 1", description="live on 1")
async def live_on_1(ctx):
    if ctx.author.voice is None:
        await ctx.send("malhuco! you are not in a voice channel.")
        return

    channel = ctx.author.voice.channel
    voice_client = ctx.voice_client

    if voice_client and voice_client.is_connected():
        await voice_client.move_to(channel)
    else:
        voice_client = await channel.connect()

    if voice_client and voice_client.is_playing():
        voice_client.pause()

    voice_client.volume = 0.45
    voice_client.play(
        discord.FFmpegPCMAudio(
            executable="ffmpeg", source="https://stream-relay-geo.ntslive.net/stream"))

    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.listening, name="NTS 1"))
    await ctx.defer()
    info = await fetch_nts_info(channel=1)
    await ctx.send(info, ephemeral=False)


@bot.hybrid_command(name="live_on_2", help="live on 2", description="live on 2")
async def live_on_2(ctx):
    if ctx.author.voice is None:
        await ctx.send("malhuco! you are not in a voice channel.")
        return

    channel = ctx.author.voice.channel
    voice_client = ctx.voice_client

    if voice_client and voice_client.is_connected():
        await voice_client.move_to(channel)
    else:
        voice_client = await channel.connect()

    if voice_client and voice_client.is_playing():
        voice_client.pause()

    voice_client.volume = 0.5
    voice_client.play(
        discord.FFmpegPCMAudio(
            executable="ffmpeg", source="https://stream-relay-geo.ntslive.net/stream2"))

    await ctx.defer()
    info = await fetch_nts_info(channel=2)
    await ctx.send(info, ephemeral=False)


@bot.hybrid_command(name="stop_now", help="Stop the streaming and disconnect", description="Stop and disconnect")
async def stop_now(ctx):
    voice_client = ctx.voice_client

    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await ctx.send("Playback stopped.")

    if voice_client:
        await voice_client.disconnect()
        await ctx.send("Disconnected from the voice channel.")
    else:
        await ctx.send("Bot is not in a voice channel.")

    await bot.change_presence(activity=None)


@bot.hybrid_command(name="pause_now", help="Pause the current playback", description="Pause streaming")
async def pause_now(ctx):
    voice_client = ctx.voice_client

    if voice_client is None:
        await ctx.send("I'm not in a voice channel.")
        return

    if voice_client.is_playing():
        voice_client.pause()
        await ctx.send("Paused playback.")
    else:
        await ctx.send("There's nothing playing to pause.")


@bot.hybrid_command(name="live_now", help="Live info", description="Live info")
async def live_now(ctx):
    await ctx.defer()
    live_now_1 = await fetch_nts_info(channel=1)
    live_now_2 = await fetch_nts_info(channel=2)
    await ctx.send(f"𝘕𝘛𝘚 ｜ Don't Assume\n{live_now_1}\n{live_now_2}", ephemeral=False)


async def fetch_nts_info(channel):
    """Fetch NTS live information from the API"""
    async with aiohttp.ClientSession() as session:
        async with session.get('https://www.nts.live/api/v2/live') as response:
            if response.status == 200:
                data = await response.json()
                try:
                    # API response has channels indexed from 0
                    channel_idx = channel - 1
                    
                    # Parse the data correctly based on the actual API structure
                    if 'results' in data and isinstance(data['results'], list) and len(data['results']) > channel_idx:
                        channel_data = data['results'][channel_idx]
                        show_name = channel_data.get('now', {}).get('broadcast_title', 'Unknown Show')
                        location_short = channel_data.get('now', {}).get('embeds', {}).get('details', {}).get('location_short')
                        location_long = channel_data.get('now', {}).get('embeds', {}).get('details', {}).get('location_long')
                        
                        # Use the short location if available, otherwise use long location
                        location = location_short or location_long or "Unknown Location"
                        
                        channel_symbol = "１ ▶︎" if channel == 1 else "２ ▶︎"
                        return f"{channel_symbol}  {show_name}  －  {location}"
                    else:
                        print(f"Unexpected API structure: {json.dumps(data, indent=2)[:500]}...")
                        return f"Could not parse NTS {channel} data (unexpected structure)"
                except (KeyError, IndexError, TypeError) as e:
                    print(f"Error parsing NTS data: {str(e)}")
                    print(f"API structure: {type(data['results'])}")
                    return f"Error retrieving NTS {channel} info: {str(e)}"
            else:
                return f"Failed to fetch NTS data. Status code: {response.status}"


if __name__ == "__main__":
    token = os.getenv("DISCORD_API_TOKEN")
    if not token:
        raise Exception("No API Token available")
    else:
        bot.run(token)
