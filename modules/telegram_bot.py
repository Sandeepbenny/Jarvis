# Telegram Bot Module

from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from modules.llm_handler import LLMHandler
from modules.prompt_manager import PromptManager

# Initialize LLMHandler and PromptManager
llm_handler = LLMHandler(backend="ollama")
prompt_manager = PromptManager()

# Load prompts
SYSTEM_PROMPT = prompt_manager.get_prompt("system_prompt")
PERSONALIZATION_PROMPT = prompt_manager.get_prompt("personalization_prompt")

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Hello! I am your personal assistant. How can I help you today?")

def handle_message(update: Update, context: CallbackContext):
    user_message = update.message.text
    response = llm_handler.process(f"{SYSTEM_PROMPT} {PERSONALIZATION_PROMPT} {user_message}")
    update.message.reply_text(response)

def setup_bot(token: str):
    updater = Updater(token, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    return updater