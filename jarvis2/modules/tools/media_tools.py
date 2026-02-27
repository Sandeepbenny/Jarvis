# modules/tools/media_tools.py
"""
Media control tools: volume, music playback.
Uses platform-specific methods for cross-platform support.
"""

import platform
import subprocess
from langchain_core.tools import tool


def _get_os() -> str:
    return platform.system()


@tool
def set_volume(level: int) -> str:
    """
    Set the system volume level.
    
    Args:
        level: Volume percentage from 0 to 100
    
    Returns:
        Status message.
    """
    level = max(0, min(100, level))
    system = _get_os()
    
    try:
        if system == "Windows":
            # Uses nircmd (must be installed) or PowerShell
            script = f"(New-Object -com Shell.Application).Windows().Volume = {level}"
            subprocess.run(["powershell", "-Command", script], check=True, capture_output=True)
        
        elif system == "Darwin":
            subprocess.run(["osascript", "-e", f"set volume output volume {level}"], check=True)
        
        else:  # Linux
            # Try pactl first (PulseAudio), then amixer
            try:
                subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{level}%"],
                               check=True, capture_output=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                subprocess.run(["amixer", "sset", "Master", f"{level}%"], check=True, capture_output=True)
        
        volume_bar = "█" * (level // 10) + "░" * (10 - level // 10)
        return f"🔊 Volume set to {level}%\n[{volume_bar}]"
    except Exception as e:
        return f"❌ Failed to set volume: {str(e)}"


@tool
def get_volume() -> str:
    """
    Get the current system volume level.
    
    Returns:
        Current volume as a percentage.
    """
    system = _get_os()
    
    try:
        if system == "Darwin":
            result = subprocess.run(
                ["osascript", "-e", "output volume of (get volume settings)"],
                capture_output=True, text=True
            )
            level = int(result.stdout.strip())
            volume_bar = "█" * (level // 10) + "░" * (10 - level // 10)
            return f"🔊 Current volume: {level}%\n[{volume_bar}]"
        
        elif system == "Linux":
            result = subprocess.run(
                ["pactl", "get-sink-volume", "@DEFAULT_SINK@"],
                capture_output=True, text=True
            )
            for part in result.stdout.split():
                if "%" in part:
                    return f"🔊 Current volume: {part}"
        
        elif system == "Windows":
            return "⚠️ Volume detection not yet supported on Windows via CLI."
        
        return "⚠️ Could not determine current volume."
    except Exception as e:
        return f"❌ Failed to get volume: {str(e)}"


@tool
def play_music(song_name: str = "", service: str = "spotify") -> str:
    """
    Play music via Spotify or system media.
    
    Args:
        song_name: Name of the song or playlist to play (optional)
        service: Music service to use ('spotify', 'youtube')
    
    Returns:
        Status message.
    """
    system = _get_os()
    
    try:
        if service == "spotify":
            if system == "Darwin":
                if song_name:
                    script = f'tell application "Spotify" to play track "spotify:search:{song_name}"'
                else:
                    script = 'tell application "Spotify" to play'
                subprocess.run(["osascript", "-e", script])
                return f"▶️ Playing on Spotify: {song_name or 'current track'}"
            
            elif system == "Linux":
                # Uses playerctl which controls any MPRIS player including Spotify
                if song_name:
                    subprocess.Popen(["spotify", "--uri", f"spotify:search:{song_name}"],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    subprocess.run(["playerctl", "play"], capture_output=True)
                return f"▶️ Playing: {song_name or 'current track'}"
            
            elif system == "Windows":
                subprocess.Popen(["spotify"], shell=True)
                return "▶️ Spotify opened. Use the app to select music."
        
        elif service == "youtube" and song_name:
            import webbrowser
            query = song_name.replace(" ", "+")
            webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
            return f"▶️ Opened YouTube search for: {song_name}"
        
        return f"⚠️ Could not play music with service: {service}"
    except Exception as e:
        return f"❌ Play music failed: {str(e)}"


@tool
def pause_music() -> str:
    """
    Pause the currently playing music.
    
    Returns:
        Status message.
    """
    system = _get_os()
    
    try:
        if system == "Darwin":
            subprocess.run(["osascript", "-e", 'tell application "Spotify" to pause'])
        elif system == "Linux":
            subprocess.run(["playerctl", "pause"], capture_output=True)
        elif system == "Windows":
            import pyautogui
            pyautogui.press("playpause")
        
        return "⏸️ Music paused."
    except Exception as e:
        return f"❌ Could not pause music: {str(e)}"


@tool
def stop_music() -> str:
    """
    Stop the currently playing music.
    
    Returns:
        Status message.
    """
    system = _get_os()
    
    try:
        if system == "Darwin":
            subprocess.run(["osascript", "-e", 'tell application "Spotify" to stop'])
        elif system == "Linux":
            subprocess.run(["playerctl", "stop"], capture_output=True)
        elif system == "Windows":
            import pyautogui
            pyautogui.press("playpause")
        
        return "⏹️ Music stopped."
    except Exception as e:
        return f"❌ Could not stop music: {str(e)}"
