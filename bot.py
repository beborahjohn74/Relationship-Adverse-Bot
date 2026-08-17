"""
Jose Alvarez — Relationship & Life Advice Telegram Bot (Hybrid Version)
--------------------------------------------------------------------------
Flow:
1. /start shows a topic menu: Romance, Family, Friendship.
2. Person taps a topic.
3. From then on, they type normally, and Jose has a real conversation with
   them about it — asking follow-up questions, listening, and giving
   practical advice — using Google Gemini (free tier).

Conversation history is kept in memory per user for the running process
(not persisted to disk/database) so Jose remembers context within a session.

Stack:
- python-telegram-bot (Telegram integration)
- Google Gemini API (free tier) for conversation

Deploy target: Railway
"""

import os
import logging
import time

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
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

# gemini-flash-latest auto-updates to Google's current stable Flash model,
# so this shouldn't need updating every time Google retires a model version.
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-flash-latest")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

MAX_HISTORY_MESSAGES = 20

# ---------------------------------------------------------------------------
# Topics
# ---------------------------------------------------------------------------

TOPICS = {
    "romance": {"label": "❤️ Romance", "focus": "romantic relationships"},
    "family": {"label": "👪 Family", "focus": "family relationships"},
    "friendship": {"label": "🤝 Friendship", "focus": "friendships"},
}

WELCOME_MESSAGE = (
    "Hi, I'm Jose Alvarez 💬\n\n"
    "I'm here to help you think through whatever's going on in your "
    "relationships — romantic, family, or friendship.\n\n"
    "What's on your mind?"
)


def main_menu_keyboard():
    buttons = [
        [InlineKeyboardButton(topic["label"], callback_data=f"topic:{key}")]
        for key, topic in TOPICS.items()
    ]
    return InlineKeyboardMarkup(buttons)


def base_system_prompt(topic_focus: str) -> str:
    return f"""You are Jose Alvarez, a warm, emotionally intelligent friend \
people talk to about their {topic_focus}.

Your style:
- Talk like a real, caring friend, not a therapist reading from a script. \
Warm, casual, natural sentences.
- Ask short, specific follow-up questions to understand what's actually going \
on before jumping to advice — don't lecture immediately.
- Once you understand the situation, give clear, practical, actionable advice: \
what they could actually say or do next, not vague platitudes like "communication \
is key."
- Validate feelings without automatically taking their side against the other \
person — help them see the situation clearly, including their own part in it \
where relevant.
- Keep messages conversational length — a few sentences, not essays.
- Never diagnose mental health conditions. If someone describes abuse, violence, \
or a safety risk to themselves or others, take it seriously, gently encourage them \
to reach out to a trusted person or appropriate local support/crisis service, and \
don't try to just "coach" them through it alone.
- Remember what the person has told you earlier in the conversation and refer back \
to it naturally.
"""


# ---------------------------------------------------------------------------
# Gemini call
# ---------------------------------------------------------------------------

def generate_reply(topic_focus: str, history: list, user_message: str) -> str:
    gemini_history = [
        {"role": "user", "parts": [base_system_prompt(topic_focus)]},
        {"role": "model", "parts": [f"Understood. I'm Jose — ready to talk about {topic_focus}."]},
    ]
    for role, content in history[-MAX_HISTORY_MESSAGES:]:
        gemini_history.append({"role": role, "parts": [content]})

    # Free-tier APIs occasionally fail transiently (brief timeouts, rate
    # limiting). Retry a couple of times with a short delay before giving up,
    # so a single blip doesn't reach the user as an error.
    last_error = None
    for attempt in range(3):
        try:
            chat = model.start_chat(history=gemini_history)
            response = chat.send_message(user_message)
            return response.text.strip()
        except Exception as e:
            last_error = e
            error_text = str(e).lower()
            # Don't retry safety blocks — retrying won't change that outcome.
            if "safety" in error_text or "blocked" in error_text or "finish_reason" in error_text:
                raise
            logger.warning("Gemini attempt %d failed: %s", attempt + 1, e)
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))

    raise last_error


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(WELCOME_MESSAGE, reply_markup=main_menu_keyboard())


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Alright, clean slate. What would you like to talk about?",
        reply_markup=main_menu_keyboard(),
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("topic:"):
        topic_key = data.split(":", 1)[1]
        topic = TOPICS.get(topic_key)
        if not topic:
            await query.edit_message_text(WELCOME_MESSAGE, reply_markup=main_menu_keyboard())
            return

        context.user_data["topic"] = topic_key
        context.user_data["history"] = []

        await query.edit_message_text(
            f"{topic['label']} — I'm listening. Tell me what's going on."
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topic_key = context.user_data.get("topic")

    if not topic_key:
        # No topic picked yet — nudge them to the menu instead of guessing.
        await update.message.reply_text(
            "Pick what this is about first, then tell me what's going on:",
            reply_markup=main_menu_keyboard(),
        )
        return

    topic = TOPICS[topic_key]
    history = context.user_data.setdefault("history", [])
    user_message = update.message.text

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        reply = generate_reply(topic["focus"], history, user_message)
    except Exception as e:
        logger.exception("Gemini generation failed")
        # Gemini's safety filters can block a response outright for messages
        # involving violence or self-harm. Give a direct, caring reply in
        # that case instead of a generic "try again" — a vague error is the
        # wrong thing to show someone who just typed something serious.
        if "safety" in str(e).lower() or "blocked" in str(e).lower() or "finish_reason" in str(e).lower():
            await update.message.reply_text(
                "That sounds like a really heavy moment, and I want to take it "
                "seriously rather than brush past it. If you or someone else "
                "could be in danger, please reach out to a trusted person or "
                "local emergency/crisis service right now — not just me. "
                "I'm still here if you want to talk through what's actually "
                "going on."
            )
        else:
            await update.message.reply_text(
                "Sorry, I'm having trouble thinking that through right now — "
                "give me a moment and try again?"
            )
        return

    history.append(("user", user_message))
    history.append(("model", reply))

    await update.message.reply_text(reply)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Jose Alvarez bot (hybrid: menu + AI chat) starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
