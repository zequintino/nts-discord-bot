"""
Opus library loader for Discord voice support.
"""
import os
import discord


def load_opus():
    """
    Attempts to load the Opus library required for voice functionality.
    
    Returns:
        bool: True if Opus was loaded successfully, False otherwise
    """
    if discord.opus.is_loaded():
        print("Opus library is already loaded")
        return True
        
    # Try to find the opus library
    opus_library_paths = [
        # Check environment variable first
        os.getenv('OPUS_LIBRARY_PATH'),
        # Linux paths
        '/usr/lib/x86_64-linux-gnu/libopus.so.0',
        '/usr/lib/libopus.so.0',
        '/usr/local/lib/libopus.so.0',
        # macOS Homebrew path
        '/opt/homebrew/Cellar/opus/1.5.2/lib/libopus.dylib',
        # macOS paths
        '/usr/local/lib/libopus.dylib',
        # Windows paths
        'opus.dll',
        # Railway nixpacks paths
        '/nix/store/libopus/lib/libopus.so.0',
        '/root/.nix-profile/lib/libopus.so.0'
    ]
    
    opus_loaded = False
    for path in opus_library_paths:
        if path is not None:
            try:
                discord.opus.load_opus(path)
                print(f"Successfully loaded Opus from: {path}")
                opus_loaded = True
                break
            except (OSError, TypeError) as e:
                print(f"Failed to load Opus from {path}: {e}")
    
    if not opus_loaded:
        print("Warning: Could not load Opus library. Voice functionality will be unavailable.")
        
    return opus_loaded