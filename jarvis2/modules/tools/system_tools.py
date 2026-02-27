# modules/tools/system_tools.py
"""
System-level tools for OS control.
Uses pyautogui, psutil, and subprocess for cross-platform support.
"""

import subprocess
import platform
import os
import shutil
import psutil
import pyautogui
import pyperclip
from datetime import datetime
from typing import Optional
from langchain_core.tools import tool


@tool
def open_application(app_name: str) -> str:
    """
    Open an application by name on the local machine.
    Works on Windows, macOS, and Linux.
    
    Args:
        app_name: Name of the application to open (e.g., 'chrome', 'notepad', 'spotify')
    
    Returns:
        Status message indicating success or failure.
    """
    system = platform.system()
    app_lower = app_name.lower().strip()

    # App name mappings per OS
    app_map = {
        "windows": {
            "chrome": "chrome",
            "firefox": "firefox",
            "notepad": "notepad",
            "calculator": "calc",
            "explorer": "explorer",
            "spotify": "spotify",
            "vscode": "code",
            "terminal": "cmd",
            "paint": "mspaint",
            "word": "winword",
            "excel": "excel",
            "powerpoint": "powerpnt",
        },
        "darwin": {
            "chrome": "open -a 'Google Chrome'",
            "firefox": "open -a Firefox",
            "safari": "open -a Safari",
            "terminal": "open -a Terminal",
            "finder": "open -a Finder",
            "spotify": "open -a Spotify",
            "vscode": "open -a 'Visual Studio Code'",
            "calculator": "open -a Calculator",
            "notes": "open -a Notes",
        },
        "linux": {
            "chrome": "google-chrome",
            "firefox": "firefox",
            "terminal": "gnome-terminal",
            "spotify": "spotify",
            "vscode": "code",
            "calculator": "gnome-calculator",
            "files": "nautilus",
            "text-editor": "gedit",
        }
    }

    os_key = system.lower() if system.lower() in ["windows", "darwin", "linux"] else "linux"
    command = app_map.get(os_key, {}).get(app_lower, app_lower)

    try:
        if system == "Windows":
            subprocess.Popen(command, shell=True)
        elif system == "Darwin":
            subprocess.Popen(command, shell=True)
        else:
            subprocess.Popen([command], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return f"✅ Opened {app_name} successfully."
    except FileNotFoundError:
        return f"❌ Could not find application: {app_name}. Make sure it's installed."
    except Exception as e:
        return f"❌ Failed to open {app_name}: {str(e)}"


@tool
def close_application(app_name: str) -> str:
    """
    Close a running application by name.
    
    Args:
        app_name: Process name to kill (e.g., 'chrome', 'spotify')
    
    Returns:
        Status message.
    """
    killed = []
    app_lower = app_name.lower().strip()

    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if app_lower in proc.info['name'].lower():
                proc.terminate()
                killed.append(proc.info['name'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    if killed:
        return f"✅ Closed: {', '.join(set(killed))}"
    return f"❌ No running process found matching: {app_name}"


@tool
def get_running_processes() -> str:
    """
    Get a list of all currently running processes.
    
    Returns:
        Formatted list of top running processes with CPU and memory usage.
    """
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            info = proc.info
            if info['cpu_percent'] > 0.1 or info['memory_percent'] > 0.1:
                processes.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
    top = processes[:15]

    lines = ["PID      | Name                          | CPU%   | MEM%"]
    lines.append("-" * 55)
    for p in top:
        lines.append(
            f"{p['pid']:<8} | {p['name']:<30} | {p['cpu_percent']:<6.1f} | {p['memory_percent']:.1f}"
        )
    return "\n".join(lines)


@tool
def take_screenshot(filename: Optional[str] = None) -> str:
    """
    Take a screenshot of the current screen and save it.
    
    Args:
        filename: Optional filename to save as. Defaults to timestamped file.
    
    Returns:
        Path where screenshot was saved.
    """
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"jarvis_screenshot_{timestamp}.png"

    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    save_dir = desktop if os.path.exists(desktop) else os.path.expanduser("~")
    save_path = os.path.join(save_dir, filename)

    try:
        screenshot = pyautogui.screenshot()
        screenshot.save(save_path)
        return f"✅ Screenshot saved to: {save_path}"
    except Exception as e:
        return f"❌ Screenshot failed: {str(e)}"


@tool
def type_text(text: str, interval: float = 0.05) -> str:
    """
    Type text using the keyboard at the current cursor position.
    
    Args:
        text: Text to type
        interval: Delay between keystrokes in seconds
    
    Returns:
        Status message.
    """
    try:
        import time
        time.sleep(0.5)  # Small delay so user can click target window
        pyautogui.write(text, interval=interval)
        return f"✅ Typed: '{text[:50]}{'...' if len(text) > 50 else ''}'"
    except Exception as e:
        return f"❌ Failed to type text: {str(e)}"


@tool
def press_key(key: str) -> str:
    """
    Press a keyboard key or key combination.
    Examples: 'enter', 'ctrl+c', 'alt+tab', 'win'
    
    Args:
        key: Key or key combination to press
    
    Returns:
        Status message.
    """
    try:
        if "+" in key:
            keys = [k.strip() for k in key.split("+")]
            pyautogui.hotkey(*keys)
        else:
            pyautogui.press(key)
        return f"✅ Pressed: {key}"
    except Exception as e:
        return f"❌ Failed to press key '{key}': {str(e)}"


@tool
def get_clipboard() -> str:
    """
    Get the current content of the clipboard.
    
    Returns:
        Clipboard content as string.
    """
    try:
        content = pyperclip.paste()
        return content if content else "Clipboard is empty."
    except Exception as e:
        return f"❌ Failed to get clipboard: {str(e)}"


@tool
def set_clipboard(text: str) -> str:
    """
    Set text to the clipboard.
    
    Args:
        text: Text to copy to clipboard
    
    Returns:
        Status message.
    """
    try:
        pyperclip.copy(text)
        return f"✅ Copied to clipboard: '{text[:60]}{'...' if len(text) > 60 else ''}'"
    except Exception as e:
        return f"❌ Failed to set clipboard: {str(e)}"


@tool
def get_system_info() -> str:
    """
    Get comprehensive system information including CPU, RAM, disk, and battery.
    
    Returns:
        Formatted system information report.
    """
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    lines = [
        "═══════════════ SYSTEM STATUS ═══════════════",
        f"🖥  OS:          {platform.system()} {platform.release()}",
        f"⚙️  CPU:         {cpu_percent}% ({cpu_count} cores)",
        f"🧠 RAM:         {ram.percent}% used ({ram.used / 1e9:.1f}GB / {ram.total / 1e9:.1f}GB)",
        f"💾 Disk:        {disk.percent}% used ({disk.used / 1e9:.1f}GB / {disk.total / 1e9:.1f}GB)",
    ]
    
    try:
        battery = psutil.sensors_battery()
        if battery:
            status = "⚡ Charging" if battery.power_plugged else "🔋 On Battery"
            lines.append(f"🔋 Battery:     {battery.percent:.0f}% ({status})")
    except Exception:
        pass

    lines.append("═" * 46)
    return "\n".join(lines)


@tool
def lock_screen() -> str:
    """Lock the computer screen."""
    system = platform.system()
    try:
        if system == "Windows":
            subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
        elif system == "Darwin":
            subprocess.run(["pmset", "displaysleepnow"])
        else:
            subprocess.run(["xdg-screensaver", "lock"])
        return "✅ Screen locked."
    except Exception as e:
        return f"❌ Could not lock screen: {str(e)}"


@tool
def shutdown_system(delay_seconds: int = 30) -> str:
    """
    Schedule a system shutdown.
    
    Args:
        delay_seconds: Seconds to wait before shutdown (default 30, min 10)
    
    Returns:
        Status message.
    """
    delay_seconds = max(10, delay_seconds)
    system = platform.system()
    
    confirm_msg = f"⚠️ System will shut down in {delay_seconds} seconds."
    
    try:
        if system == "Windows":
            subprocess.run(["shutdown", "/s", "/t", str(delay_seconds)])
        elif system == "Darwin":
            subprocess.run(["sudo", "shutdown", "-h", f"+{delay_seconds // 60}"])
        else:
            subprocess.run(["shutdown", "-h", f"+{delay_seconds // 60}"])
        return confirm_msg
    except Exception as e:
        return f"❌ Shutdown failed: {str(e)}"


@tool
def restart_system(delay_seconds: int = 30) -> str:
    """
    Schedule a system restart.
    
    Args:
        delay_seconds: Seconds before restart (default 30)
    
    Returns:
        Status message.
    """
    delay_seconds = max(10, delay_seconds)
    system = platform.system()
    
    try:
        if system == "Windows":
            subprocess.run(["shutdown", "/r", "/t", str(delay_seconds)])
        elif system == "Darwin":
            subprocess.run(["sudo", "shutdown", "-r", f"+{delay_seconds // 60}"])
        else:
            subprocess.run(["shutdown", "-r", f"+{delay_seconds // 60}"])
        return f"⚠️ System will restart in {delay_seconds} seconds."
    except Exception as e:
        return f"❌ Restart failed: {str(e)}"
