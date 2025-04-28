import discord
from discord.ext import commands
from src.utils.nts_api import NTSRadioInfo
from src.utils.ffmpeg_cleanup import end_ffmpeg_processes
from src.config.settings import (
    NTS_STREAM_URL_1,
    NTS_STREAM_URL_2,
    BOT_DEFAULT_VOLUME,
    BOT_HEADER,
    LIVE_ON_1_HEADER,
    LIVE_ON_2_HEADER,
    FFMPEG_OPTIONS
)


class RadioCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="live_on_1",
                             help="Stream NTS １",
                             description="Connect to voice channel and stream NTS １")
    async def live_on_1(self, ctx):
        await self._start_radio_stream(ctx, channel=1)

    @commands.hybrid_command(name="live_on_2",
                             help="Stream NTS ２",
                             description="Connect to voice channel and stream NTS ２")
    async def live_on_2(self, ctx):
        await self._start_radio_stream(ctx, channel=2)

    @commands.hybrid_command(name="pause",
                             help="Pause streaming",
                             description="Pause the playing stream")
    async def pause(self, ctx):
        voice_client = await self._get_voice_client(ctx)
        if voice_client is None:
            return

        if voice_client.is_playing():
            voice_client.pause()
            await ctx.send("Paused stream.")
        else:
            await ctx.send("Already paused.")

    @commands.hybrid_command(name="resume",
                             help="Resume streaming",
                             description="Resume the paused stream")
    async def resume(self, ctx):
        voice_client = await self._get_voice_client(ctx)
        if voice_client is None:
            return

        if voice_client.is_paused():
            voice_client.resume()
            await ctx.send("Resumed stream.")
        else:
            await ctx.send("Already playing.")

    @commands.hybrid_command(name="stop",
                             help="Stop streaming",
                             description="Stop stream and disconnect from voice channel")
    async def stop(self, ctx):
        await ctx.defer()
        voice_client = await self._get_voice_client(ctx)
        if voice_client is None:
            return

        text_channel = ctx.channel
        try:
            if voice_client.is_playing() or voice_client.is_paused():
                end_ffmpeg_processes()
                voice_client.stop()
                await ctx.send("Stopped stream.")

            await self.bot.change_presence(activity=None)
            await voice_client.disconnect(force=True)
            await text_channel.send(
                "Disconnected from voice channel.\nUse `/live_on_1` or `/live_on_2` to start streaming.")
        except Exception as e:
            await ctx.send("There was a problem stopping the stream. Please try again.")

    @commands.hybrid_command(name="about",
                             help="About the current show",
                             description="Show detailed information about the current show")
    async def about(self, ctx, channel=1):
        await ctx.defer()
        if channel not in [1, 2]:
            await ctx.send("Radio must be either １ or ２.")
            return

        radio_info = await NTSRadioInfo.get_rich_channel_info(channel=channel)

        if not radio_info:
            await ctx.send(f"Could not retrieve information for NTS {channel}.")
            return

        embed = await self._create_show_embed(radio_info, channel)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="live_now",
                             help="Information about what's live now",
                             description="Display detailed information about what's playing on both １ and ２")
    async def live_now(self, ctx):
        await ctx.defer()
        channel1_info, channel2_info = await NTSRadioInfo.get_both_channels_info()
        embed = discord.Embed(title=BOT_HEADER,
                              description="LIVE NOW ●",
                              color=discord.Color.from_rgb(0, 0, 0),)

        if channel1_info:
            embed.add_field(name=f"{LIVE_ON_1_HEADER}{channel1_info['show_name']}",
                            value=channel1_info['location'],
                            inline=False)
        else:
            embed.add_field(name=LIVE_ON_1_HEADER,
                            value="Information unavailable",
                            inline=False)

        if channel2_info:
            embed.add_field(name=f"{LIVE_ON_2_HEADER}{channel2_info['show_name']}",
                            value=channel2_info['location'],
                            inline=False)
        else:
            embed.add_field(name=LIVE_ON_2_HEADER,
                            value="Information unavailable",
                            inline=False)

        embed.add_field(name="",
                        value="_Use_ `/live_on_1` _or_ `/live_on_2` _commands to stream in voice channel_",
                        inline=False)
        await ctx.send(embed=embed)

    async def _get_voice_client(self, ctx):
        voice_client = ctx.voice_client
        if voice_client is None:
            await ctx.send("I'm not in a voice channel.")
            return None
        return voice_client

    async def _create_show_embed(self, radio_info, channel):
        embed = discord.Embed(title=f"{channel} ▶︎  {radio_info['show_name']}",
                              color=discord.Color.from_rgb(0, 0, 0),)
        embed.add_field(name="Location",
                        value=radio_info['location'], inline=True)

        if radio_info.get('start_timestamp') and radio_info.get('end_timestamp'):
            start_time = radio_info['start_timestamp'].split('T')[
                1].split('+')[0]
            end_time = radio_info['end_timestamp'].split('T')[1].split('+')[0]
            embed.add_field(
                name="Time", value=f"{start_time} - {end_time}", inline=True)

        if radio_info.get('details', {}).get('description'):
            description = radio_info['details']['description']
            if len(description) > 1024:
                description = description[:1021] + "..."
            embed.add_field(name="Description",
                            value=description, inline=False)

        return embed

    async def _start_radio_stream(self, ctx: commands.Context, channel: int):
        await ctx.defer()
        if ctx.author.voice is None:
            await ctx.send("You're not in a voice channel.")
            return

        voice_channel = ctx.author.voice.channel
        voice_client = ctx.voice_client

        if voice_client:
            if voice_client.is_playing() or voice_client.is_paused():
                audio_source = voice_client.source
                if audio_source:
                    audio_source.cleanup()
                voice_client.stop()
            if voice_client.is_connected() and voice_client.channel != voice_channel:
                await voice_client.disconnect(force=True)
                voice_client = None

        if not voice_client or not voice_client.is_connected():
            try:
                voice_client = await voice_channel.connect(timeout=10.0)
            except:
                await ctx.send("Error connecting to voice channel. Please try again.")
                return

        stream_url = NTS_STREAM_URL_1 if channel == 1 else NTS_STREAM_URL_2
        volume = BOT_DEFAULT_VOLUME
        voice_client.volume = volume

        try:
            audio = discord.FFmpegOpusAudio(
                source=stream_url,
                before_options=FFMPEG_OPTIONS.get("before_options"),
                options=FFMPEG_OPTIONS.get("options"))
            voice_client.play(audio)
        except:
            await ctx.send("Error playing audio stream. Please try again.")
            return

        await self.bot.change_presence(activity=discord.Activity(
            type=discord.ActivityType.listening,
            name=f"{channel}"))

        radio_info = await NTSRadioInfo.get_rich_channel_info(channel=channel)
        if radio_info:
            embed = await self._create_show_embed(radio_info, channel)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"Started streaming NTS {channel}")


async def setup(bot):
    await bot.add_cog(RadioCommands(bot))
