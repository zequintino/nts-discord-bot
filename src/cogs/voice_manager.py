"""
Voice state management for the NTS Discord bot.
Handles auto-pause and disconnect for bandwidth saving.
"""
import asyncio
import discord
import logging
from discord.ext import commands, tasks
from src.utils.cleanup import kill_ffmpeg_processes

# Get a logger with the correct name and add a console handler to ensure visibility
logger = logging.getLogger("nts_bot.voice_manager")
logger.setLevel(logging.INFO)

class VoiceManager(commands.Cog):
    """
    Simple voice state manager that:
    1. Pauses and disconnects when channel is empty
    2. Disconnects when stream is paused for too long
    3. Auto-resumes when users return
    """
    def __init__(self, bot):
        self.bot = bot
        # Track inactivity timestamps by guild_id
        self.inactive_since = {}
        self.timeout = 60  # 1 minute timeout
        self.last_command_channels = {}  # Track where commands were last used
        self.check_activity.start()
        logger.info("Voice manager initialized - monitoring voice channels")
    
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
                
                # Start tracking if this is the first check
                if key not in self.inactive_since:
                    self.inactive_since[key] = current_time
                    # Pause immediately to save bandwidth
                    if voice_client.is_playing():
                        voice_client.pause()
                        logger.info(f"Channel empty: Paused playback in {guild.name}")
                
                # Check if timeout exceeded
                elif current_time - self.inactive_since[key] >= self.timeout:
                    should_disconnect = True
            else:
                # Users present, clear empty status if it exists
                if f"{guild_id}_empty" in self.inactive_since:
                    logger.info(f"Users present in {guild.name} - canceling empty timeout")
                    self.inactive_since.pop(f"{guild_id}_empty", None)
            
            # Case 2: Stream paused
            if voice_client.is_paused():
                key = f"{guild_id}_paused"
                
                # Start tracking if this is the first check
                if key not in self.inactive_since:
                    self.inactive_since[key] = current_time
                    logger.info(f"Stream paused in {guild.name} - will disconnect in {self.timeout} seconds")
                
                # Check if timeout exceeded
                elif current_time - self.inactive_since[key] >= self.timeout:
                    should_disconnect = True
            else:
                # Not paused, clear paused status if it exists
                if f"{guild_id}_paused" in self.inactive_since:
                    logger.info(f"Stream no longer paused in {guild.name} - canceling paused timeout")
                    self.inactive_since.pop(f"{guild_id}_paused", None)
            
            # Disconnect if needed
            if should_disconnect:
                logger.info(f"Timeout reached for {guild.name} - disconnecting")
                await self.disconnect_with_message(voice_client)
    
    async def disconnect_with_message(self, voice_client):
        """Send a message and disconnect from voice."""
        guild = voice_client.guild
        
        try:
            # Find a suitable text channel to send the message
            text_channel = None
            guild_id = guild.id
            
            # First try the channel where commands were last used
            if guild_id in self.last_command_channels:
                channel_id = self.last_command_channels[guild_id]
                channel = guild.get_channel(channel_id)
                if channel and channel.permissions_for(guild.me).send_messages:
                    text_channel = channel
            
            # Fallback options if no last-used channel
            if not text_channel:
                # Try system channel
                if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:
                    text_channel = guild.system_channel
                else:
                    # Try to find any suitable channel
                    for channel in guild.text_channels:
                        if channel.permissions_for(guild.me).send_messages:
                            text_channel = channel
                            break
            
            # Send the generic disconnect message if we have a channel
            if text_channel:
                message = "🔌 Disconnecting due to inactivity. Use `/live_on_1` or `/live_on_2` to start streaming again."
                
                await text_channel.send(message)
                await asyncio.sleep(0.25)  # Brief wait for message to send
            
            # Clean disconnect process
            if voice_client.is_playing() or voice_client.is_paused():
                # First clean up the audio source properly
                # audio_source = voice_client.source
                # if audio_source:
                #     audio_source.cleanup()
                #     logger.info("Audio source cleaned up properly")
                kill_ffmpeg_processes()
                await asyncio.sleep(0.5)  # Wait for cleanup to complete
                voice_client.stop()
                
            # Update presence before disconnecting
            await self.bot.change_presence(activity=None)
            
            # Disconnect with force=True to ensure clean termination
            await voice_client.disconnect(force=True)
            logger.info(f"Disconnected from {guild.name}")
            
            # Clear states
            self.inactive_since.pop(f"{guild.id}_empty", None)
            self.inactive_since.pop(f"{guild.id}_paused", None)
            
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
            # Last resort - try again with force=True if first attempt failed
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
        # Skip bot's own state changes
        if member.id == self.bot.user.id:
            return
            
        # Handle user joining a voice channel with the bot
        if after and after.channel:
            voice_client = after.channel.guild.voice_client
            if voice_client and voice_client.channel.id == after.channel.id:
                guild_id = after.channel.guild.id
                
                # Clear empty status since a user joined
                if f"{guild_id}_empty" in self.inactive_since:
                    logger.info(f"User {member.display_name} joined voice channel - canceling auto-disconnect")
                    self.inactive_since.pop(f"{guild_id}_empty", None)
                
                # Auto-resume if was paused due to being empty
                if voice_client.is_paused() and f"{guild_id}_paused" in self.inactive_since:
                    logger.info(f"Resuming playback as {member.display_name} joined")
                    voice_client.resume()
                    self.inactive_since.pop(f"{guild_id}_paused", None)
    
    @commands.Cog.listener()
    async def on_command(self, ctx):
        """Track which channel commands are used in."""
        # Store the channel where commands are used
        if ctx.guild:
            self.last_command_channels[ctx.guild.id] = ctx.channel.id
            logger.info(f"Command used in #{ctx.channel.name} - updating last_command_channel")


async def setup(bot):
    """Add the Voice Manager cog to the bot."""
    logger.info("Setting up Voice Manager cog")
    await bot.add_cog(VoiceManager(bot))