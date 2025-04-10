"""
Radio commands cog for NTS Discord bot.
Contains all commands related to streaming radio channels.
"""
import discord
import asyncio
from discord.ext import commands
import logging
from src.utils.nts_api import fetch_nts_info
from src.utils.cleanup import kill_ffmpeg_processes
from src.config.settings import (
    NTS_STREAM_URL_1, 
    NTS_STREAM_URL_2, 
    BOT_DEFAULT_VOLUME_1, 
    BOT_DEFAULT_VOLUME_2,
    BOT_HEADER,
    FFMPEG_OPTIONS
)

logger = logging.getLogger("nts_bot.radio")

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

        # Clean up any existing connection first
        if voice_client:
            if voice_client.is_playing() or voice_client.is_paused():
                # Clean up the current audio source properly
                audio_source = voice_client.source
                if audio_source:
                    audio_source.cleanup()
                    logger.info("Existing audio source cleaned up")
                voice_client.stop()
            if voice_client.is_connected() and voice_client.channel != channel:
                await voice_client.disconnect(force=True)
                voice_client = None
        
        # Connect if needed
        if not voice_client or not voice_client.is_connected():
            try:
                voice_client = await channel.connect(timeout=10.0)
                logger.info(f"Connected to voice channel: {channel.name}")
            except Exception as e:
                logger.error(f"Error connecting to voice channel: {e}")
                await ctx.send("Error connecting to voice channel. Please try again.")
                return

        # Set volume and play the stream
        voice_client.volume = BOT_DEFAULT_VOLUME_1
        
        try:
            audio = discord.FFmpegOpusAudio(
                source=NTS_STREAM_URL_1,
                before_options=FFMPEG_OPTIONS.get("before_options"),
                options=FFMPEG_OPTIONS.get("options")
            )
            voice_client.play(audio)
            logger.info(f"Started streaming NTS Radio 1 in {channel.name}")
        except Exception as e:
            logger.error(f"Error playing audio stream: {e}")
            await ctx.send("Error playing audio stream. Please try again.")
            return

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

        # Clean up any existing connection first
        if voice_client:
            if voice_client.is_playing() or voice_client.is_paused():
                # Clean up the current audio source properly
                audio_source = voice_client.source
                if audio_source:
                    audio_source.cleanup()
                    logger.info("Existing audio source cleaned up")
                voice_client.stop()
            if voice_client.is_connected() and voice_client.channel != channel:
                await voice_client.disconnect(force=True)
                voice_client = None
        
        # Connect if needed
        if not voice_client or not voice_client.is_connected():
            try:
                voice_client = await channel.connect(timeout=10.0)
                logger.info(f"Connected to voice channel: {channel.name}")
            except Exception as e:
                logger.error(f"Error connecting to voice channel: {e}")
                await ctx.send("Error connecting to voice channel. Please try again.")
                return

        # Set volume and play the stream
        voice_client.volume = BOT_DEFAULT_VOLUME_2
        
        try:
            audio = discord.FFmpegOpusAudio(
                NTS_STREAM_URL_2,
                before_options=FFMPEG_OPTIONS.get("before_options"),
                options=FFMPEG_OPTIONS.get("options")
            )
            voice_client.play(audio)
            logger.info(f"Started streaming NTS Radio 2 in {channel.name}")
        except Exception as e:
            logger.error(f"Error playing audio stream: {e}")
            await ctx.send("Error playing audio stream. Please try again.")
            return

        await self.bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.listening, name="NTS 2"))
        await ctx.defer()
        info = await fetch_nts_info(channel=2)
        await ctx.send(info, ephemeral=False)

    @commands.hybrid_command(
        name="stop",
        help="Stop the streaming and disconnect",
        description="Stop and disconnect from voice channel"
    )
    async def stop(self, ctx):
        """Stop playback and disconnect from the voice channel."""
        voice_client = ctx.voice_client

        if not voice_client:
            await ctx.send("Bot is not in a voice channel.")
            return

        # Acknowledge the command immediately to prevent interaction timeout
        try:
            await ctx.defer()  # This will acknowledge the interaction
            
            # Now perform the cleanup which might take some time
            if voice_client.is_playing() or voice_client.is_paused():
                # Get the source that's currently playing
                audio_source = voice_client.source
                if audio_source:
                    # Use our new method to terminate the FFmpeg process properly
                    logger.info(f"Cleaning up audio source: {audio_source}")
                    kill_ffmpeg_processes()
                    await asyncio.sleep(0.5)  # Wait for cleanup to complete
                    logger.info("FFmpeg process terminated properly")
                
                # Now stop the playback
                voice_client.stop()
                logger.info("Playback stopped")
                await ctx.send("Playback stopped.")
            
            # Then disconnect
            await voice_client.disconnect(force=True)
            logger.info("Disconnected from voice channel")
            await ctx.send("Disconnected from the voice channel.")
            
            await self.bot.change_presence(activity=None)
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
            try:
                await ctx.send("Error during disconnect. Please try again.")
            except:
                logger.error("Failed to send error message to user")

    @commands.hybrid_command(
        name="pause",
        help="Pause the current playback",
        description="Pause streaming"
    )
    async def pause(self, ctx):
        """Pause the current radio stream."""
        voice_client = ctx.voice_client

        if voice_client is None:
            await ctx.send("I'm not in a voice channel.")
            return

        if voice_client.is_playing():
            voice_client.pause()
            logger.info("Playback paused")
            await ctx.send("Paused playback.")
        else:
            await ctx.send("There's nothing playing to pause.")

    @commands.hybrid_command(
        name="resume",
        help="Resume the paused playback",
        description="Resume streaming"
    )
    async def resume_now(self, ctx):
        """Resume the paused radio stream."""
        voice_client = ctx.voice_client

        if voice_client is None:
            await ctx.send("I'm not in a voice channel.")
            return

        if voice_client.is_paused():
            voice_client.resume()
            logger.info("Playback resumed")
            await ctx.send("Resumed playback.")
        else:
            await ctx.send("Playback is not paused.")

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