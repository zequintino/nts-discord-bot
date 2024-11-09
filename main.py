import os
import discord

from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands
from playwright.async_api import async_playwright
from flask import Flask
from threading import Thread


# Initialize the Flask app
app = Flask(__name__)

# Define a simple route for Flask to confirm it's running
@app.route("/")
def home():
    return "Bot is running!"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        await bot.tree.sync()  # Ensures all hybrid commands are synced to Discord
        print("Commands synced successfully.")
    except Exception as e:
        print(f"Error syncing commands: {e}")



@bot.hybrid_command(name="play_1", help="Live now 1", description="Live now 1")
async def play_1(ctx):
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
        discord.FFmpegPCMAudio(source="https://stream-relay-geo.ntslive.net/stream"))

    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="NTS 1"))
    await ctx.defer()
    info = await fetch_nts(selected_nts="nts1")
    await ctx.send(info, ephemeral=False)


@bot.hybrid_command(name="play_2", help="Live now 2", description="Live now 2")
async def play_2(ctx):
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
        discord.FFmpegPCMAudio(source="https://stream-relay-geo.ntslive.net/stream2"))

    await ctx.defer()
    info = await fetch_nts(selected_nts="nts2")
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
    live_now_1 = await fetch_nts(selected_nts="nts1")
    live_now_2 = await fetch_nts(selected_nts="nts2")
    await ctx.send(f"𝘕𝘛𝘚 ｜ Don't Assume\n{live_now_1}\n{live_now_2}", ephemeral=False)


@bot.command()
async def nts1info(ctx):
    await ctx.send(await fetch_nts(selected_nts="nts1"))


@bot.command()
async def nts2info(ctx):
    await ctx.send(await fetch_nts(selected_nts="nts2"))


async def fetch_nts(selected_nts):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("https://nts.live")

        if selected_nts == "nts1":
            nts_1 = await page.wait_for_selector(
                "#nts-live-header > div.live-header__channels--collapsed.live-header__channels > button:nth-child(2) > div > h3")
            nts_1_show = await nts_1.text_content()
            nts_1 = await page.wait_for_selector(
                "#nts-live-header > div.live-header__channels--collapsed.live-header__channels > button:nth-child(2) > div > span > span:nth-child(2)")
            nts_1_loc = await nts_1.text_content()
            nts_1_info = "１ ▶︎  " + nts_1_show + "  －  " + nts_1_loc
            await browser.close()
            return nts_1_info

        elif selected_nts == "nts2":
            try:
                nts_2 = await page.wait_for_selector(
                    "#nts-live-header > div.live-header__channels--collapsed.live-header__channels > button.live-channel.live-channel--collapsed.channel-2 > div > h3")
            except:
                print("error")
            nts_2_show = await nts_2.text_content()
            nts_2 = await page.wait_for_selector(
                "#nts-live-header > div.live-header__channels--collapsed.live-header__channels > button.live-channel.live-channel--collapsed.channel-2 > div > span > span:nth-child(2)")
            nts_2_loc = await nts_2.text_content()
            nts_2_info = "２ ▶︎  " + nts_2_show + "  －  " + nts_2_loc
            await browser.close()
            return nts_2_info


# Main block to load the bot token, run the bot, and start Flask
if __name__ == "__main__":
    load_dotenv()
    token = os.getenv("API_TOKEN")
    if not token:
        raise Exception("No API Token available")

    # Run the bot in a separate thread
    bot_thread = Thread(target=lambda: bot.run(token))
    bot_thread.start()

    # Start the Flask app on port 9000
    custom_port = os.getenv("PORT")
    app.run(debug=True, host="0.0.0.0", port=custom_port)


# class aclient(discord.Client):
#     def __init__(self):
#         super().__init__(intents=discord.Intents.default())
#         self.synced = False  # syncs just one time

#     async def on_ready(self):
#         await self.wait_until_ready()
#         if not self.synced:
#             await tree.sync()
#             self.synced = True
#         print(f"We have logged in as {self.user}.")

# client = aclient()
# tree = app_commands.CommandTree(client)

# @tree.command(name='tester', description='testing')
# async def slash1(interaction: discord.Interaction):
#     await intera

# @bot.hybrid_command(name="test", description="testing hybrid commands")
# async def test(ctx: commands.Context):
#     await ctx.defer()
#     nts_1_info = await fetch_nts(selected_nts="nts1")
#     nts_2_info = await fetch_nts(selected_nts="nts2")
#     await ctx.send(f"{nts_1_info}\n{nts_2_info}", ephemeral=False)
    