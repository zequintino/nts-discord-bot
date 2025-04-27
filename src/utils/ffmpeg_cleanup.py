"""
FFMPEG process cleanup utility.
Discord.py FFMPEG process cleanup is not always effective.
"""
import psutil
import platform
import subprocess


def end_ffmpeg_processes():
    try:
        current_process = psutil.Process()

        def terminate_process(pid):
            try:
                process = psutil.Process(pid)
                process.terminate()
                try:
                    process.wait(timeout=2)
                except psutil.TimeoutExpired:
                    process.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        if platform.system() == "Windows":
            # Windows - use tasklist to find ffmpeg processes
            cmd = ["tasklist", "/FI", "IMAGENAME eq ffmpeg.exe", "/FO", "CSV"]
            output = subprocess.check_output(cmd).decode()

            for line in output.strip().split('\n')[1:]:  # Skip header
                try:
                    pid = int(line.split(',')[1].strip('"'))
                    terminate_process(pid)
                except (IndexError, ValueError):
                    continue

        else:
            # Unix systems - use process tree approach
            children = current_process.children(recursive=True)
            ffmpeg_processes = [
                process for process in children if process.name().lower().startswith('ffmpeg')]

            for process in ffmpeg_processes:
                terminate_process(process.pid)

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
