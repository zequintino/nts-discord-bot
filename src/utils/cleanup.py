"""
Utilities for properly cleaning up FFmpeg processes.
"""
import os
import signal
import subprocess
import logging
import platform
import sys
import asyncio
import time

logger = logging.getLogger('nts_bot.cleanup')

def kill_ffmpeg_processes():
    """
    Find and kill FFmpeg processes started by this bot.
    This helps prevent the -9 termination signals when voice_client.stop() is called.
    """
    try:
        # Different commands based on OS
        if platform.system() == "Windows":
            # Windows command to list processes
            cmd = ["tasklist", "/FI", "IMAGENAME eq ffmpeg.exe", "/FO", "CSV"]
            output = subprocess.check_output(cmd).decode()
            
            # Extract PIDs from the output
            lines = output.strip().split('\n')[1:]  # Skip the header line
            for line in lines:
                parts = line.split(',')
                if len(parts) >= 2:
                    # Extract PID (remove quotes)
                    pid = int(parts[1].strip('"'))
                    try:
                        # Kill process
                        os.kill(pid, signal.SIGTERM)
                        logger.info(f"Terminated FFmpeg process with PID {pid}")
                    except Exception as e:
                        logger.error(f"Error killing FFmpeg process {pid}: {e}")
                        
        else:
            # macOS/Linux command
            # Find our own process ID to exclude parent processes
            our_pid = os.getpid()
            
            # Look for FFmpeg processes started by this process or its children
            cmd = ["pgrep", "-P", str(our_pid), "ffmpeg"]
            
            try:
                output = subprocess.check_output(cmd).decode()
                pids = [int(pid) for pid in output.strip().split()]
                
                for pid in pids:
                    try:
                        # Try SIGTERM first for graceful shutdown
                        os.kill(pid, signal.SIGTERM)
                        logger.info(f"Terminated FFmpeg process with PID {pid}")
                    except Exception as e:
                        logger.error(f"Error killing FFmpeg process {pid}: {e}")
            except subprocess.CalledProcessError:
                # No matching processes found
                pass
                
    except Exception as e:
        logger.error(f"Error cleaning up FFmpeg processes: {e}")
        
    return True

async def terminate_ffmpeg_process(audio_source):
    """
    Properly terminates an FFmpeg process by accessing the _process attribute
    and waiting for it to exit cleanly.
    
    Args:
        audio_source: The Discord audio source object that contains the FFmpeg process
        
    Returns:
        bool: True if process was terminated successfully, False otherwise
    """
    if not audio_source:
        logger.warning("No audio source provided to terminate")
        return False
    
    try:
        # Access the internal process - this is using internal attributes
        if hasattr(audio_source, '_process') and audio_source._process:
            process = audio_source._process
            pid = process.pid
            logger.info(f"FFmpeg process found (PID: {pid}), terminating gracefully...")
            
            # Check if the process is still running
            if process.poll() is None:  # None means process is still running
                # On macOS/Linux use SIGTERM
                try:
                    # First send SIGTERM for graceful shutdown
                    process.terminate()
                    
                    # Instead of using process.wait() which blocks, we need a non-blocking approach
                    # Give it some time to terminate gracefully
                    for _ in range(10):  # Try for up to 1 second (10 * 0.1s)
                        if process.poll() is not None:
                            logger.info(f"FFmpeg process {pid} terminated gracefully")
                            return True
                        await asyncio.sleep(0.1)
                    
                    # If we reach here, the process didn't terminate gracefully
                    # Try a more forceful approach on Unix-like systems
                    if platform.system() != "Windows":
                        try:
                            # SIGINT is ctrl+C, sometimes more effective than SIGTERM
                            os.kill(pid, signal.SIGINT)
                            logger.info(f"Sent SIGINT to FFmpeg process {pid}")
                            
                            # Give it another moment
                            await asyncio.sleep(0.5)
                        except Exception as e:
                            logger.warning(f"Error sending SIGINT: {e}")
                    
                    # If still running, use SIGKILL as last resort
                    if process.poll() is None:
                        logger.warning(f"FFmpeg process {pid} did not terminate gracefully, using SIGKILL")
                        process.kill()  # This is SIGKILL
                        await asyncio.sleep(0.1)
                    
                    return True
                except Exception as e:
                    logger.error(f"Error during process termination: {e}")
                    return False
            else:
                logger.info(f"FFmpeg process {pid} was already terminated")
                return True
        else:
            logger.warning("Audio source has no _process attribute or process is None")
            return False
    except Exception as e:
        logger.error(f"Error accessing FFmpeg process: {e}")
        return False


# The synchronous version for cases where we can't use async
def terminate_ffmpeg_process_sync(audio_source):
    """
    Synchronous version of terminate_ffmpeg_process for contexts where async cannot be used.
    """
    if not audio_source:
        logger.warning("No audio source provided to terminate")
        return False
    
    try:
        # Access the internal process - this is using internal attributes
        if hasattr(audio_source, '_process') and audio_source._process:
            process = audio_source._process
            pid = process.pid
            logger.info(f"FFmpeg process found (PID: {pid}), terminating gracefully...")
            
            # Check if the process is still running
            if process.poll() is None:  # None means process is still running
                # On macOS/Linux use SIGTERM
                try:
                    # First send SIGTERM for graceful shutdown
                    process.terminate()
                    
                    # Use a timeout approach instead of wait
                    start_time = time.time()
                    while time.time() - start_time < 1.0:  # Wait up to 1 second
                        if process.poll() is not None:
                            logger.info(f"FFmpeg process {pid} terminated gracefully")
                            return True
                        time.sleep(0.1)
                    
                    # If we reach here, the process didn't terminate gracefully
                    # Try a more forceful approach on Unix-like systems
                    if platform.system() != "Windows":
                        try:
                            # SIGINT is ctrl+C, sometimes more effective than SIGTERM
                            os.kill(pid, signal.SIGINT)
                            logger.info(f"Sent SIGINT to FFmpeg process {pid}")
                            time.sleep(0.5)
                        except Exception as e:
                            logger.warning(f"Error sending SIGINT: {e}")
                    
                    # If still running, use SIGKILL as last resort
                    if process.poll() is None:
                        logger.warning(f"FFmpeg process {pid} did not terminate gracefully, using SIGKILL")
                        process.kill()  # This is SIGKILL
                    
                    return True
                except Exception as e:
                    logger.error(f"Error during process termination: {e}")
                    return False
            else:
                logger.info(f"FFmpeg process {pid} was already terminated")
                return True
        else:
            logger.warning("Audio source has no _process attribute or process is None")
            return False
    except Exception as e:
        logger.error(f"Error accessing FFmpeg process: {e}")
        return False