# 🤖 Jarvis — Personal AI Assistant

A production-ready, agentic personal AI assistant inspired by Iron Man's Jarvis.
Built with LangGraph, FastAPI, NVIDIA/OpenAI LLMs, and 30+ tools for real computer control.

---

## 📁 Project Structure

```
jarvis/
├── backend/
│   ├── api.py                  # FastAPI routes
│   └── orchestrator.py         # Thread-safe request controller
│
├── modules/
│   ├── agent.py                # LangGraph ReAct agent (CORE)
│   ├── llm_handler.py          # LLM backend abstraction
│   ├── state_manager.py        # Agent state machine
│   │
│   ├── memory/
│   │   └── persistent_memory.py  # SQLite memory (facts, history, episodes)
│   │
│   └── tools/
│       ├── system_tools.py     # OS control (apps, keyboard, screenshots)
│       ├── file_tools.py       # File system operations
│       ├── web_tools.py        # Web search, weather, news
│       ├── media_tools.py      # Spotify, volume control
│       ├── productivity_tools.py  # Calendar, Gmail, notes, reminders
│       └── code_tools.py       # Python execution, shell commands
│
├── frontend/
│   └── index.html              # Chat UI with sidebar & quick commands
│
├── config/
│   └── prompts.yaml            # System prompts
│
├── main.py                     # Terminal interface
├── requirements.txt
└── .env                        # API keys (create this)
```

---

## ⚡ Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Create `.env` file
```env
# Required: at least one LLM backend
NVIDIA_API_KEY=your_nvidia_api_key_here
OPENAI_API_KEY=your_openai_api_key_here   # optional

# Optional: Telegram bot
TELEGRAM_BOT_TOKEN=your_telegram_token
```

### 3. Run the server
```bash
uvicorn backend.api:app --reload --host 127.0.0.1 --port 8000
```

### 4. Open the UI
Go to: http://127.0.0.1:8000

### 5. Or use the terminal
```bash
python main.py
```

---

## 🛠️ Available Tools (30+)

| Category | Tools |
|---|---|
| 🖥️ System | open_app, close_app, screenshot, type_text, press_key, clipboard, sys_info, lock, shutdown |
| 📁 Files | read, write, list, create_dir, delete, move, copy, search, zip |
| 🌐 Web | web_search, fetch_page, weather, news |
| 🎵 Media | play_music, pause, stop, set_volume, get_volume |
| 📅 Calendar | get_events, create_event (requires Google auth) |
| 📧 Email | send_email, get_emails (requires Gmail auth) |
| 📝 Notes | create_note, get_notes |
| ⏰ Reminders | set_reminder, get_reminders |
| 💻 Code | run_python, run_shell, install_package |

---

## 🧠 Memory System

Jarvis has 3 types of memory:

1. **Conversation History** — Last N turns, stored in SQLite, persists across restarts
2. **User Facts** — Long-term facts: `name`, `location`, `preferences`, etc.
3. **Episodic Memory** — Important events Jarvis should remember

```python
# Store facts
POST /remember  {"key": "name", "value": "Tony"}

# View memory
GET /memory
```

---

## 🔌 Setting Up Google APIs (Calendar + Gmail)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → Enable Calendar API + Gmail API
3. Create OAuth 2.0 credentials → Download as `credentials.json`
4. Place in `~/.jarvis/google_creds.json` (Calendar) and `~/.jarvis/gmail_creds.json` (Gmail)
5. On first use, a browser window will open for OAuth authorization

---

## 🏗️ Architecture

```
User Input (text/voice)
       │
       ▼
  Orchestrator (thread-safe, lock-based)
       │
       ▼
  JarvisAgent (LangGraph ReAct loop)
       │
  ┌────▼─────────────────────────────────┐
  │  System Prompt + Memory Context      │
  │         +                           │
  │  Conversation History               │
  │         +                           │
  │  User Input                         │
  └────┬─────────────────────────────────┘
       │
       ▼
   LLM Node ──── wants tools? ──► Tool Node ──┐
       │                                       │
       │◄──────────────────────────────────────┘
       │                    (loop up to 10x)
       ▼
   Final Response
       │
       ▼
  Persistent Memory ← stores turn
       │
       ▼
  Response → API → Frontend / Voice
```

---

## 🔜 Roadmap / What to Add Next

- [ ] **Browser automation** (Playwright/Selenium) — control Chrome
- [ ] **Image understanding** — analyze screenshots with vision models
- [ ] **Long-term learning** — auto-extract facts from conversations
- [ ] **Multi-agent** — delegate subtasks to specialized agents
- [ ] **Plugin system** — hot-load new tools without restart
- [ ] **Wake word** — always-on "Hey Jarvis" activation
- [ ] **Docker** — containerized deployment
- [ ] **WebSocket streaming** — stream responses token by token
- [ ] **Authentication** — API keys for multi-user deployment

---

## 🐛 Bug Fixes from Original Code

1. **Memory pollution** — Fixed: AI messages only added after successful LLM call
2. **Race condition** — Fixed: `threading.Lock()` replaces boolean `_busy` flag
3. **Datetime serialization** — Fixed: State history uses ISO strings, not datetime objects
4. **OpenAI double mapping** — Fixed: Messages formatted once, not twice
5. **Telegram API version** — Updated to python-telegram-bot v20+ async API
