"""
Radio commands cog for NTS Discord bot.
Contains all commands related to streaming radio channels.
"""
import discord
from discord.ext import commands
import logging
from src.utils.nts_api import NTSRadioInfo
from src.utils.cleanup import end_ffmpeg_processes
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

        # Get and display show information using the new NTSRadioInfo class
        formatted_info = await NTSRadioInfo.get_formatted_display(channel=1)
        await ctx.send(formatted_info, ephemeral=False)

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

        # Get and display show information using the new NTSRadioInfo class
        formatted_info = await NTSRadioInfo.get_formatted_display(channel=2)
        await ctx.send(formatted_info, ephemeral=False)

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

        await ctx.defer()
        text_channel = ctx.channel

        try:
            if voice_client.is_playing() or voice_client.is_paused():
                end_ffmpeg_processes()
                voice_client.stop()
                await ctx.send("◼︎ Playback stopped")

            await self.bot.change_presence(activity=None)
            await voice_client.disconnect(force=True)
            await text_channel.send(
                "Disconnected from voice channel\nUse `/live_on_1` or `/live_on_2` to start streaming again!")

        except Exception as e:
            await ctx.send("Error during disconnect. Please try again.")

    @commands.hybrid_command(name="pause",
                             help="Pause the current playback",
                             description="Pause streaming")
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

    @commands.hybrid_command(name="resume",
                             help="Resume the paused playback",
                             description="Resume streaming")
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

    @commands.hybrid_command(name="live_now",
                             help="Display currently playing shows",
                             description="Show what's playing on both NTS channels")
    async def live_now(self, ctx):
        """Display what's currently playing on both NTS channels."""
        await ctx.defer()

        # Get detailed show information for both channels
        channel1_details = await NTSRadioInfo.get_show_details(channel=1)
        channel2_details = await NTSRadioInfo.get_show_details(channel=2)

        # Create formatted messages
        if channel1_details:
            channel1_msg = f"１ ▶︎  {channel1_details['show_name']}  －  {channel1_details['location']}"
        else:
            channel1_msg = "１ ▶︎  Unable to retrieve show information"

        if channel2_details:
            channel2_msg = f"２ ▶︎  {channel2_details['show_name']}  －  {channel2_details['location']}"
        else:
            channel2_msg = "２ ▶︎  Unable to retrieve show information"

        # Send the combined message
        await ctx.send(f"{BOT_HEADER}\n{channel1_msg}\n{channel2_msg}", ephemeral=False)

    @commands.hybrid_command(name="show_details",
                             help="Display detailed information about the currently playing show",
                             description="Show detailed information about the current broadcast")
    async def show_details(self, ctx, channel: int = 1):
        """Display detailed information about the currently playing show on the specified channel.

        Args:
            channel: The NTS channel number (1 or 2, defaults to 1)
        """
        # Validate channel input
        if channel not in [1, 2]:
            await ctx.send("Channel must be either 1 or 2.")
            return

        await ctx.defer()

        # Get rich channel information
        rich_info = await NTSRadioInfo.get_rich_channel_info(channel=channel)

        if not rich_info:
            await ctx.send(f"Could not retrieve information for NTS {channel}.")
            return

        # Create an embed with the rich information
        embed = discord.Embed(
            title=f"NTS Radio {channel} - Now Playing",
            description=rich_info['show_name'],
            color=discord.Color.dark_purple()
        )

        # Add location info
        embed.add_field(name="Location",
                        value=rich_info['location'], inline=True)

        # Add timestamps if available
        if rich_info.get('start_timestamp') and rich_info.get('end_timestamp'):
            start_time = rich_info['start_timestamp'].split('T')[
                1].split('+')[0]
            end_time = rich_info['end_timestamp'].split('T')[1].split('+')[0]
            embed.add_field(name="Show Time",
                            value=f"{start_time} - {end_time}", inline=True)

        # Add genre if available
        if rich_info.get('details', {}).get('genre'):
            embed.add_field(
                name="Genre", value=rich_info['details']['genre'], inline=True)

        # Add description if available
        if rich_info.get('details', {}).get('description'):
            # Truncate description if too long
            description = rich_info['details']['description']
            if len(description) > 1024:
                description = description[:1021] + "..."
            embed.add_field(name="Description",
                            value=description, inline=False)

        # Add links if available
        links = []
        if rich_info.get('media', {}).get('mixcloud_url'):
            links.append(f"[Mixcloud]({rich_info['media']['mixcloud_url']})")
        if rich_info.get('media', {}).get('soundcloud_url'):
            links.append(
                f"[SoundCloud]({rich_info['media']['soundcloud_url']})")

        if links:
            embed.add_field(name="Listen Again",
                            value=" | ".join(links), inline=False)

        # Set footer with episode ID if available
        if rich_info.get('episode_id'):
            embed.set_footer(text=f"Episode ID: {rich_info['episode_id']}")

        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="live_now_rich",
        help="Display detailed information about currently playing shows",
        description="Show rich details about what's playing on both NTS channels"
    )
    async def live_now_rich(self, ctx):
        """Display detailed information about currently playing shows on both NTS channels."""
        await ctx.defer()

        # Get both channels' information in a single API call
        channel1_info, channel2_info = await NTSRadioInfo.get_both_channels_info()

        # Create an embed for the response
        embed = discord.Embed(
            title="NTS Radio - Now Playing",
            description="Currently broadcasting on NTS Radio channels",
            color=discord.Color.dark_purple()
        )

        # Channel 1 info
        if channel1_info:
            embed.add_field(
                name="Channel 1",
                value=f"**{channel1_info['show_name']}**\n{channel1_info['location']}",
                inline=False
            )
        else:
            embed.add_field(
                name="Channel 1",
                value="Information unavailable",
                inline=False
            )

        # Channel 2 info
        if channel2_info:
            embed.add_field(
                name="Channel 2",
                value=f"**{channel2_info['show_name']}**\n{channel2_info['location']}",
                inline=False
            )
        else:
            embed.add_field(
                name="Channel 2",
                value="Information unavailable",
                inline=False
            )

        # Add links to listen to the channels
        embed.add_field(
            name="Listen Live",
            value="Use `/live_on_1` or `/live_on_2` commands to stream in voice channel",
            inline=False
        )

        # Send the embed
        await ctx.send(embed=embed)


async def setup(bot):
    """Add the Radio Commands cog to the bot."""
    await bot.add_cog(RadioCommands(bot))
