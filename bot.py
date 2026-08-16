"""
Jose Alvarez — Relationship & Life Advice Telegram Bot
--------------------------------------------------------
A warm, non-judgmental chat companion that helps people talk through
relationship, family, friendship, and work issues, and gives them
practical, actionable advice.

Stack:
- python-telegram-bot (Telegram API)
- Google Gemini API (free tier) for conversation
- SQLite for per-user conversation memory

Deploy target: Railway (see README.md for volume/persistence notes)
"""

import os
import sqlite3
import logging
from datetime import datetime

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import google.generativeai as genai

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
DB_PATH = os.environ.get("DB_PATH", "jose_memory.db")

# How many past messages (per user) to feed back into Gemini as context.
# Keep this modest to control token usage — Jose still "remembers" the
# relationship because we also keep a running summary (see below).
MAX_HISTORY_MESSAGES = 20

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Persona
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are Jose Alvarez, a warm, emotionally intelligent friend \
people talk to about their relationships — romantic, family, friendship, or work.

Your style:
- Talk like a real, caring friend, not a therapist reading from a script. \
Warm, casual, natural sentences. Use the person's own words back to them \
sometimes to show you're really listening.
- Ask short, specific follow-up questions to understand what's actually going \
on before jumping to advice — don't lecture immediately.
- Once you understand the situation, give clear, practical, actionable advice: \
what they could actually say or do next, not vague platitudes like "communication \
is key."
- Validate feelings without automatically taking their side against the other \
person — help them see the situation clearly, including their own part in it \
where relevant.
- Keep messages conversational length — a few sentences, not essays. This is a \
chat, not a blog post.
- Never diagnose mental health conditions. If someone describes abuse, violence, \
or a safety risk to themselves or others, take it seriously, gently encourage them \
to reach out to a trusted person or appropriate local support/crisis service, and \
don't try to just "coach" them through it alone.
- Remember what the person has told you earlier in the conversation and refer back \
to it naturally, the way a friend who's been listening would.
"""

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,          -- 'user' or 'model'
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_messages_user
        ON messages (user_id, id)
        """
    )
    conn.commit()
    conn.close()


def save_message(user_id: int, role: str, content: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO messages (user_id, role, content, created_at) VALUES (?, ?, ?, ?)",
        (user_id, role, content, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def get_history(user_id: int, limit: int = MAX_HISTORY_MESSAGES):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        """
        SELECT role, content FROM messages
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (user_id, limit),
    ).fetchall()
    conn.close()
    rows.reverse()  # chronological order
    return rows


# ---------------------------------------------------------------------------
# Gemini call
# ---------------------------------------------------------------------------

def generate_reply(user_id: int, user_message: str) -> str:
    history = get_history(user_id)

    # Build the chat history in Gemini's expected format.
    gemini_history = [{"role": "user", "parts": [SYSTEM_PROMPT]},
                       {"role": "model", "parts": ["Understood. I'm Jose — ready to listen."]}]

    for role, content in history:
        gemini_role = "user" if role == "user" else "model"
        gemini_history.append({"role": gemini_role, "parts": [content]})

    chat = model.start_chat(history=gemini_history)
    response = chat.send_message(user_message)
    return response.text.strip()


# ---------------------------------------------------------------------------
# Telegram handlers
# ---------------------------------------------------------------------------

WELCOME_MESSAGE = (
    "Hi, I'm Jose Alvarez 💬\n\n"
    "I'm here to help you think through whatever's going on in your "
    "relationships — romantic, family, friendship, work, any of it.\n\n"
    "What's on your mind?"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MESSAGE)


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    await update.message.reply_text(
        "Alright, clean slate — I've cleared what I remembered. What's going on?"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        reply = generate_reply(user_id, user_message)
    except Exception as e:
        logger.exception("Gemini generation failed")
        # TEMPORARY: show the real error in chat so we can debug it.
        await update.message.reply_text(f"[DEBUG ERROR] {type(e).__name__}: {e}")
        return

    save_message(user_id, "user", user_message)
    save_message(user_id, "model", reply)

    await update.message.reply_text(reply)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    init_db()

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Jose Alvarez bot starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
