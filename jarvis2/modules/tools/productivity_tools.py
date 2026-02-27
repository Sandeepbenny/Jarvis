# modules/tools/productivity_tools.py
"""
Productivity tools: Calendar (Google), Email (Gmail), Notes, Reminders.
Uses Google APIs where available, with local fallbacks.
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List
from langchain_core.tools import tool


JARVIS_DATA_DIR = Path.home() / ".jarvis"
JARVIS_DATA_DIR.mkdir(exist_ok=True)
NOTES_FILE = JARVIS_DATA_DIR / "notes.json"
REMINDERS_FILE = JARVIS_DATA_DIR / "reminders.json"


def _load_json(path: Path) -> list:
    if path.exists():
        with open(path, "r") as f:
            return json.load(f)
    return []


def _save_json(path: Path, data: list) -> None:
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


# ─────────────────────────────────────────────────────────
# CALENDAR
# ─────────────────────────────────────────────────────────

@tool
def get_calendar_events(days_ahead: int = 7) -> str:
    """
    Get upcoming calendar events from Google Calendar.
    Requires GOOGLE_CALENDAR credentials configured.
    
    Args:
        days_ahead: Number of days ahead to look (default 7)
    
    Returns:
        List of upcoming events.
    """
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from google.auth.transport.requests import Request

        SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
        creds_path = JARVIS_DATA_DIR / "google_creds.json"
        token_path = JARVIS_DATA_DIR / "google_token.json"

        creds = None
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not creds_path.exists():
                    return "❌ Google Calendar not configured. Place credentials.json in ~/.jarvis/"
                flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_path, "w") as f:
                f.write(creds.to_json())

        service = build("calendar", "v3", credentials=creds)
        now = datetime.utcnow().isoformat() + "Z"
        end = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat() + "Z"

        events_result = service.events().list(
            calendarId="primary",
            timeMin=now,
            timeMax=end,
            maxResults=20,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        events = events_result.get("items", [])
        if not events:
            return f"📅 No events in the next {days_ahead} days."

        lines = [f"📅 Upcoming events (next {days_ahead} days):"]
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date", ""))
            try:
                dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                start_str = dt.strftime("%a, %b %d at %I:%M %p")
            except Exception:
                start_str = start
            
            title = event.get("summary", "Untitled")
            location = event.get("location", "")
            loc_str = f" @ {location}" if location else ""
            lines.append(f"  • {start_str}: {title}{loc_str}")

        return "\n".join(lines)
    
    except ImportError:
        return "❌ Install: pip install google-api-python-client google-auth-oauthlib"
    except Exception as e:
        return f"❌ Calendar fetch failed: {str(e)}"


@tool
def create_calendar_event(
    title: str,
    start_datetime: str,
    end_datetime: str,
    description: str = "",
    location: str = ""
) -> str:
    """
    Create a new event in Google Calendar.
    
    Args:
        title: Event title
        start_datetime: Start time (e.g., '2025-01-15 14:00:00')
        end_datetime: End time (e.g., '2025-01-15 15:00:00')
        description: Optional event description
        location: Optional event location
    
    Returns:
        Status message with event link.
    """
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from google.auth.transport.requests import Request

        SCOPES = ["https://www.googleapis.com/auth/calendar"]
        token_path = JARVIS_DATA_DIR / "google_token.json"

        if not token_path.exists():
            return "❌ Google Calendar not authenticated. Run get_calendar_events first."

        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())

        service = build("calendar", "v3", credentials=creds)

        # Parse datetime
        try:
            start_dt = datetime.fromisoformat(start_datetime)
            end_dt = datetime.fromisoformat(end_datetime)
        except ValueError:
            return f"❌ Invalid datetime format. Use: 'YYYY-MM-DD HH:MM:SS'"

        event = {
            "summary": title,
            "location": location,
            "description": description,
            "start": {
                "dateTime": start_dt.isoformat(),
                "timeZone": "UTC",
            },
            "end": {
                "dateTime": end_dt.isoformat(),
                "timeZone": "UTC",
            },
        }

        created = service.events().insert(calendarId="primary", body=event).execute()
        return f"✅ Event created: {title}\n📅 {start_datetime} → {end_datetime}\n🔗 {created.get('htmlLink', '')}"
    
    except ImportError:
        return "❌ Install: pip install google-api-python-client google-auth-oauthlib"
    except Exception as e:
        return f"❌ Failed to create event: {str(e)}"


# ─────────────────────────────────────────────────────────
# EMAIL
# ─────────────────────────────────────────────────────────

@tool
def send_email(to: str, subject: str, body: str) -> str:
    """
    Send an email via Gmail.
    Requires Gmail API credentials in ~/.jarvis/
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body text
    
    Returns:
        Status message.
    """
    try:
        import base64
        from email.mime.text import MIMEText
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from google.auth.transport.requests import Request

        SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
        token_path = JARVIS_DATA_DIR / "gmail_token.json"
        creds_path = JARVIS_DATA_DIR / "gmail_creds.json"

        creds = None
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not creds_path.exists():
                    return "❌ Gmail not configured. See docs on setting up Google credentials."
                from google_auth_oauthlib.flow import InstalledAppFlow
                flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_path, "w") as f:
                f.write(creds.to_json())

        service = build("gmail", "v1", credentials=creds)
        
        msg = MIMEText(body)
        msg["to"] = to
        msg["subject"] = subject
        
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        
        return f"✅ Email sent to {to}\n📧 Subject: {subject}"
    
    except ImportError:
        return "❌ Install: pip install google-api-python-client google-auth-oauthlib"
    except Exception as e:
        return f"❌ Failed to send email: {str(e)}"


@tool
def get_emails(max_results: int = 5, query: str = "is:unread") -> str:
    """
    Fetch emails from Gmail.
    
    Args:
        max_results: Max number of emails to fetch (default 5)
        query: Gmail search query (default 'is:unread')
    
    Returns:
        Formatted email summaries.
    """
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from google.auth.transport.requests import Request
        import base64

        SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
        token_path = JARVIS_DATA_DIR / "gmail_token.json"

        if not token_path.exists():
            return "❌ Gmail not configured."

        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())

        service = build("gmail", "v1", credentials=creds)
        result = service.users().messages().list(
            userId="me", q=query, maxResults=max_results
        ).execute()

        messages = result.get("messages", [])
        if not messages:
            return f"📭 No emails matching: {query}"

        lines = [f"📬 Emails ({query}):"]
        for msg_ref in messages:
            msg = service.users().messages().get(
                userId="me", id=msg_ref["id"], format="metadata",
                metadataHeaders=["From", "Subject", "Date"]
            ).execute()

            headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
            snippet = msg.get("snippet", "")[:120]
            
            lines.append(f"\n  📧 From: {headers.get('From', 'Unknown')}")
            lines.append(f"     Subject: {headers.get('Subject', 'No subject')}")
            lines.append(f"     Date: {headers.get('Date', '')}")
            lines.append(f"     Preview: {snippet}...")

        return "\n".join(lines)
    
    except ImportError:
        return "❌ Install: pip install google-api-python-client google-auth-oauthlib"
    except Exception as e:
        return f"❌ Failed to fetch emails: {str(e)}"


# ─────────────────────────────────────────────────────────
# NOTES (Local JSON store)
# ─────────────────────────────────────────────────────────

@tool
def create_note(title: str, content: str, tags: List[str] = []) -> str:
    """
    Create and save a local note.
    
    Args:
        title: Note title
        content: Note content
        tags: Optional list of tags for organization
    
    Returns:
        Status message.
    """
    notes = _load_json(NOTES_FILE)
    note = {
        "id": len(notes) + 1,
        "title": title,
        "content": content,
        "tags": tags,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    notes.append(note)
    _save_json(NOTES_FILE, notes)
    return f"✅ Note created: '{title}' (ID: {note['id']})"


@tool
def get_notes(search: str = "", tag: str = "") -> str:
    """
    Get saved notes, optionally filtering by search term or tag.
    
    Args:
        search: Text to search in title/content (optional)
        tag: Filter by tag (optional)
    
    Returns:
        Formatted list of notes.
    """
    notes = _load_json(NOTES_FILE)
    
    if search:
        notes = [n for n in notes if search.lower() in n["title"].lower() 
                 or search.lower() in n["content"].lower()]
    if tag:
        notes = [n for n in notes if tag.lower() in [t.lower() for t in n.get("tags", [])]]
    
    if not notes:
        return "📝 No notes found."
    
    lines = [f"📝 Notes ({len(notes)} found):"]
    for note in notes[-10:]:  # Show last 10
        lines.append(f"\n  [{note['id']}] **{note['title']}**")
        lines.append(f"  Tags: {', '.join(note.get('tags', [])) or 'none'}")
        lines.append(f"  {note['content'][:200]}{'...' if len(note['content']) > 200 else ''}")
    
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────
# REMINDERS (Local JSON store)
# ─────────────────────────────────────────────────────────

@tool
def set_reminder(message: str, remind_at: str) -> str:
    """
    Set a reminder for a specific time.
    
    Args:
        message: Reminder message
        remind_at: When to remind (e.g., '2025-01-15 14:00:00' or '30 minutes')
    
    Returns:
        Status message.
    """
    reminders = _load_json(REMINDERS_FILE)
    
    # Parse time
    try:
        remind_dt = datetime.fromisoformat(remind_at)
    except ValueError:
        # Try parsing relative time like "30 minutes", "2 hours"
        parts = remind_at.lower().split()
        if len(parts) >= 2:
            amount = int(parts[0])
            unit = parts[1]
            if "minute" in unit:
                remind_dt = datetime.now() + timedelta(minutes=amount)
            elif "hour" in unit:
                remind_dt = datetime.now() + timedelta(hours=amount)
            elif "day" in unit:
                remind_dt = datetime.now() + timedelta(days=amount)
            else:
                return f"❌ Could not parse time: {remind_at}"
        else:
            return f"❌ Invalid time format: {remind_at}"
    
    reminder = {
        "id": len(reminders) + 1,
        "message": message,
        "remind_at": remind_dt.isoformat(),
        "created_at": datetime.now().isoformat(),
        "triggered": False,
    }
    reminders.append(reminder)
    _save_json(REMINDERS_FILE, reminders)
    
    return f"⏰ Reminder set: '{message}'\n📅 At: {remind_dt.strftime('%A, %B %d at %I:%M %p')}"


@tool
def get_reminders(include_past: bool = False) -> str:
    """
    Get all pending reminders.
    
    Args:
        include_past: Whether to include already-triggered reminders
    
    Returns:
        List of reminders.
    """
    reminders = _load_json(REMINDERS_FILE)
    now = datetime.now()
    
    if not include_past:
        reminders = [r for r in reminders if not r.get("triggered", False)]
    
    if not reminders:
        return "⏰ No pending reminders."
    
    lines = ["⏰ Reminders:"]
    for r in sorted(reminders, key=lambda x: x["remind_at"]):
        remind_dt = datetime.fromisoformat(r["remind_at"])
        delta = remind_dt - now
        
        if delta.total_seconds() < 0:
            time_str = "⚠️ OVERDUE"
        elif delta.total_seconds() < 3600:
            time_str = f"in {int(delta.total_seconds() / 60)} minutes"
        elif delta.total_seconds() < 86400:
            time_str = f"in {int(delta.total_seconds() / 3600)} hours"
        else:
            time_str = remind_dt.strftime("%b %d at %I:%M %p")
        
        lines.append(f"  [{r['id']}] {r['message']} — {time_str}")
    
    return "\n".join(lines)
