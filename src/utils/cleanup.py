"""FFMPEG process cleanup utility."""
import subprocess
import platform
import psutil

def end_ffmpeg_processes():
    """
    Find and kill FFmpeg processes started by this bot.
    Uses a more graceful approach to process termination.
    Discord.py FFMEPG process cleanup is not always effective.
    """
    try:
        current_process = psutil.Process()
        
        def terminate_process(pid):
            """Helper to gracefully terminate a process."""
            try:
                process = psutil.Process(pid)
                # First try SIGTERM
                process.terminate()
                # Give it some time to terminate gracefully
                try:
                    process.wait(timeout=2)
                except psutil.TimeoutExpired:
                    # If it doesn't terminate, force kill
                    process.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        if platform.system() == "Windows":
            # Windows - use tasklist to find ffmpeg processes
            cmd = ["tasklist", "/FI", "IMAGENAME eq ffmpeg.exe", "/FO", "CSV"]
            output = subprocess.check_output(cmd).decode()
            
            # Extract PIDs from output
            for line in output.strip().split('\n')[1:]:  # Skip header
                try:
                    pid = int(line.split(',')[1].strip('"'))
                    terminate_process(pid)
                except (IndexError, ValueError):
                    continue
                    
        else:
            # Unix systems - use process tree approach
            children = current_process.children(recursive=True)
            ffmpeg_processes = [p for p in children if p.name().lower().startswith('ffmpeg')]
            
            # Terminate each ffmpeg process gracefully
            for proc in ffmpeg_processes:
                terminate_process(proc.pid)
                
    except Exception:
        # If all else fails, try direct command
        try:
            if platform.system() == "Windows":
                subprocess.run(["taskkill", "/F", "/IM", "ffmpeg.exe"], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL)
            else:
                subprocess.run(["pkill", "-f", "ffmpeg"],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
        except Exception:
            pass

    return True