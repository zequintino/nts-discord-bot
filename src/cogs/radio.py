"""
Radio commands cog for NTS Discord bot.
Contains all commands related to streaming radio channels.
"""
import discord
from discord.ext import commands
from src.utils.nts_api import fetch_nts_info
from src.config.settings import (
    NTS_STREAM_URL_1, 
    NTS_STREAM_URL_2, 
    BOT_DEFAULT_VOLUME_1, 
    BOT_DEFAULT_VOLUME_2,
    BOT_HEADER
)


class RadioCommands(commands.Cog):
    """Commands for streaming NTS Radio channels in Discord voice channels."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(
        name="live_on_1",
        help="Stream NTS Radio Channel 1",
        description="Connect to voice and stream NTS Radio Channel 1"
    )
    async def live_on_1(self, ctx):
        """Stream NTS Radio Channel 1 in the user's current voice channel."""
        if ctx.author.voice is None:
            await ctx.send("You're not in a voice channel.")
            return

        channel = ctx.author.voice.channel
        voice_client = ctx.voice_client

        if voice_client and voice_client.is_connected():
            await voice_client.move_to(channel)
        else:
            voice_client = await channel.connect()

        if voice_client and voice_client.is_playing():
            voice_client.pause()

        voice_client.volume = BOT_DEFAULT_VOLUME_1
        voice_client.play(
            discord.FFmpegPCMAudio(
                executable="ffmpeg", source=NTS_STREAM_URL_1))

        await self.bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.listening, name="NTS 1"))
        await ctx.defer()
        info = await fetch_nts_info(channel=1)
        await ctx.send(info, ephemeral=False)

    @commands.hybrid_command(
        name="live_on_2",
        help="Stream NTS Radio Channel 2",
        description="Connect to voice and stream NTS Radio Channel 2"
    )
    async def live_on_2(self, ctx):
        """Stream NTS Radio Channel 2 in the user's current voice channel."""
        if ctx.author.voice is None:
            await ctx.send("You're not in a voice channel.")
            return

        channel = ctx.author.voice.channel
        voice_client = ctx.voice_client

        if voice_client and voice_client.is_connected():
            await voice_client.move_to(channel)
        else:
            voice_client = await channel.connect()

        if voice_client and voice_client.is_playing():
            voice_client.pause()

        voice_client.volume = BOT_DEFAULT_VOLUME_2
        voice_client.play(
            discord.FFmpegPCMAudio(
                executable="ffmpeg", source=NTS_STREAM_URL_2))

        await ctx.defer()
        info = await fetch_nts_info(channel=2)
        await ctx.send(info, ephemeral=False)

    @commands.hybrid_command(
        name="stop_now",
        help="Stop the streaming and disconnect",
        description="Stop and disconnect from voice channel"
    )
    async def stop_now(self, ctx):
        """Stop playback and disconnect from the voice channel."""
        voice_client = ctx.voice_client

        if voice_client and voice_client.is_playing():
            voice_client.stop()
            await ctx.send("Playback stopped.")

        if voice_client:
            await voice_client.disconnect()
            await ctx.send("Disconnected from the voice channel.")
        else:
            await ctx.send("Bot is not in a voice channel.")

        await self.bot.change_presence(activity=None)

    @commands.hybrid_command(
        name="pause_now",
        help="Pause the current playback",
        description="Pause streaming"
    )
    async def pause_now(self, ctx):
        """Pause the current radio stream."""
        voice_client = ctx.voice_client

        if voice_client is None:
            await ctx.send("I'm not in a voice channel.")
            return

        if voice_client.is_playing():
            voice_client.pause()
            await ctx.send("Paused playback.")
        else:
            await ctx.send("There's nothing playing to pause.")

    @commands.hybrid_command(
        name="live_now",
        help="Display currently playing shows",
        description="Show what's playing on both NTS channels"
    )
    async def live_now(self, ctx):
        """Display what's currently playing on both NTS channels."""
        await ctx.defer()
        live_now_1 = await fetch_nts_info(channel=1)
        live_now_2 = await fetch_nts_info(channel=2)
        await ctx.send(f"{BOT_HEADER}\n{live_now_1}\n{live_now_2}", ephemeral=False)


async def setup(bot):
    """Add the Radio Commands cog to the bot."""
    await bot.add_cog(RadioCommands(bot))