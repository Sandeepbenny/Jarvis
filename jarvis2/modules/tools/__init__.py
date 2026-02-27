# modules/tools/__init__.py
from .system_tools import (
    open_application,
    close_application,
    get_running_processes,
    take_screenshot,
    type_text,
    press_key,
    get_clipboard,
    set_clipboard,
    get_system_info,
    lock_screen,
    shutdown_system,
    restart_system,
)
from .file_tools import (
    read_file,
    write_file,
    list_directory,
    create_directory,
    delete_file,
    move_file,
    copy_file,
    search_files,
    get_file_info,
    zip_files,
)
from .web_tools import (
    web_search,
    fetch_webpage,
    get_weather,
    get_news,
)
from .media_tools import (
    play_music,
    pause_music,
    stop_music,
    set_volume,
    get_volume,
)
from .productivity_tools import (
    get_calendar_events,
    create_calendar_event,
    send_email,
    get_emails,
    create_note,
    get_notes,
    set_reminder,
    get_reminders,
)
from .code_tools import (
    run_python_code,
    run_shell_command,
    install_package,
)

__all__ = [
    "open_application", "close_application", "get_running_processes",
    "take_screenshot", "type_text", "press_key",
    "get_clipboard", "set_clipboard", "get_system_info",
    "lock_screen", "shutdown_system", "restart_system",
    "read_file", "write_file", "list_directory", "create_directory",
    "delete_file", "move_file", "copy_file", "search_files",
    "get_file_info", "zip_files",
    "web_search", "fetch_webpage", "get_weather", "get_news",
    "play_music", "pause_music", "stop_music", "set_volume", "get_volume",
    "get_calendar_events", "create_calendar_event",
    "send_email", "get_emails",
    "create_note", "get_notes", "set_reminder", "get_reminders",
    "run_python_code", "run_shell_command", "install_package",
]
