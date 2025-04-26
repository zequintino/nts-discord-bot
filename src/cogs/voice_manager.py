"""
Voice state management for the NTS Discord bot.
Handles auto-pause and disconnect for bandwidth saving.
"""
import asyncio
from discord.ext import commands, tasks
from src.utils.cleanup import end_ffmpeg_processes

class VoiceManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.inactive_since = {}
        self.timeout = 60  # 1 minute timeout
        self.last_command_channels = {}
        self.check_activity.start()
    
    def cog_unload(self):
        """Clean up when cog is unloaded."""
        self.check_activity.cancel()
    
    @tasks.loop(seconds=10)
    async def check_activity(self):
        """Check for inactive voice connections every 10 seconds."""
        current_time = asyncio.get_event_loop().time()
        
        for guild in self.bot.guilds:
            voice_client = guild.voice_client
            if not voice_client or not voice_client.is_connected():
                continue
                
            guild_id = guild.id
            should_disconnect = False
            
            # Case 1: No users in voice channel
            channel_members = voice_client.channel.members
            non_bot_users = [m for m in channel_members if not m.bot]
            if len(non_bot_users) == 0:
                key = f"{guild_id}_empty"
                
                if key not in self.inactive_since:
                    self.inactive_since[key] = current_time
                    if voice_client.is_playing():
                        # Stop playback and kill FFMPEG before pausing
                        await self.clean_audio(voice_client)
                        voice_client.pause()
                elif current_time - self.inactive_since[key] >= self.timeout:
                    should_disconnect = True
            else:
                if f"{guild_id}_empty" in self.inactive_since:
                    self.inactive_since.pop(f"{guild_id}_empty", None)
            
            # Case 2: Stream paused
            if voice_client.is_paused():
                key = f"{guild_id}_paused"
                
                if key not in self.inactive_since:
                    self.inactive_since[key] = current_time
                elif current_time - self.inactive_since[key] >= self.timeout:
                    should_disconnect = True
            else:
                if f"{guild_id}_paused" in self.inactive_since:
                    self.inactive_since.pop(f"{guild_id}_paused", None)
            
            # Disconnect if needed
            if should_disconnect:
                await self.clean_disconnect(voice_client)
    
    async def clean_audio(self, voice_client):
        """Properly clean up audio resources."""
        try:
            if voice_client.is_playing() or voice_client.is_paused():
                # First kill FFMPEG processes
                end_ffmpeg_processes()
                await asyncio.sleep(1.0)  # Increased wait time for cleanup
                # Then stop the voice client
                voice_client.stop()
                await asyncio.sleep(0.5)  # Additional wait after stopping
        except Exception:
            # If cleanup fails, force stop
            try:
                voice_client.stop()
            except Exception:
                pass
    
    async def clean_disconnect(self, voice_client):
        """Perform a clean disconnect with proper resource cleanup."""
        if not voice_client:
            return
            
        guild = voice_client.guild
        guild_id = guild.id
        
        try:
            # Clean up audio first
            await self.clean_audio(voice_client)
            
            # Find suitable text channel
            text_channel = None
            if guild_id in self.last_command_channels:
                channel_id = self.last_command_channels[guild_id]
                text_channel = guild.get_channel(channel_id)
            
            if not text_channel:
                for channel in guild.text_channels:
                    if channel.permissions_for(guild.me).send_messages:
                        text_channel = channel
                        self.last_command_channels[guild_id] = channel.id
                        break
            
            # Send disconnect messages
            if text_channel:
                try:
                    await text_channel.send("🔌 Disconnecting due to inactivity")
                    await text_channel.send("Use `/live_on_1` or `/live_on_2` to start streaming again!")
                except Exception:
                    pass
            
            # Update presence and disconnect
            await self.bot.change_presence(activity=None)
            
            # Wait a moment before disconnecting to ensure cleanup is complete
            await asyncio.sleep(0.5)
            await voice_client.disconnect(force=True)
            
            # Clear states
            self.inactive_since.pop(f"{guild_id}_empty", None)
            self.inactive_since.pop(f"{guild_id}_paused", None)
            
        except Exception:
            # Last resort - force disconnect
            try:
                if voice_client.is_connected():
                    await voice_client.disconnect(force=True)
            except Exception:
                pass
    
    @check_activity.before_loop
    async def before_check_activity(self):
        """Wait for bot to be ready before starting the loop."""
        await self.bot.wait_until_ready()
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Handle voice state changes."""
        if member.id == self.bot.user.id:
            return
            
        if after and after.channel:
            voice_client = after.channel.guild.voice_client
            if voice_client and voice_client.channel.id == after.channel.id:
                guild_id = after.channel.guild.id
                
                if f"{guild_id}_empty" in self.inactive_since:
                    self.inactive_since.pop(f"{guild_id}_empty", None)
                
                if voice_client.is_paused() and f"{guild_id}_paused" in self.inactive_since:
                    voice_client.resume()
                    self.inactive_since.pop(f"{guild_id}_paused", None)
    
    @commands.Cog.listener()
    async def on_command(self, ctx):
        """Track which channel commands are used in."""
        if ctx.guild:
            self.last_command_channels[ctx.guild.id] = ctx.channel.id


async def setup(bot):
    """Add the Voice Manager cog to the bot."""
    await bot.add_cog(VoiceManager(bot))