"""
Jose Alvarez — Relationship & Life Advice Telegram Bot (Simple Version)
------------------------------------------------------------------------
No external AI API — just the Telegram bot token. Uses an inline button
menu: the person picks a topic, and Jose replies with warm, practical,
pre-written advice for that topic. They can go back and pick another
topic any time.

Stack:
- python-telegram-bot only (no Gemini, no OpenAI, no database)

Deploy target: Railway
"""

import os
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

WELCOME_MESSAGE = (
    "Hi, I'm Jose Alvarez 💬\n\n"
    "I'm here to help you think through whatever's going on in your "
    "relationships — romantic, family, friendship, work, any of it.\n\n"
    "What's on your mind?"
)

# ---------------------------------------------------------------------------
# Topics and their advice content
# ---------------------------------------------------------------------------

TOPICS = {
    "romance": {
        "label": "❤️ Romance",
        "situations": {
            "arguing": {
                "label": "We keep arguing",
                "text": (
                    "Repeated arguments are usually about an unmet need, not "
                    "the surface topic. Try this: next time it comes up, "
                    "pause and ask each other \"what do you actually need "
                    "from me here?\" instead of restating the complaint. "
                    "Pick a calm moment to have that conversation — not "
                    "mid-argument."
                ),
            },
            "trust": {
                "label": "Trust issues",
                "text": (
                    "Trust rebuilds through consistency, not promises. Be "
                    "specific about what would help you feel secure — vague "
                    "reassurance doesn't land the same way concrete actions "
                    "do. And check in with yourself: is this about something "
                    "they did, or a pattern from before them?"
                ),
            },
            "distance": {
                "label": "Feeling distant",
                "text": (
                    "Emotional distance often creeps in quietly. Try naming "
                    "it directly and gently: \"I've been feeling a bit far "
                    "from you lately, can we talk about it?\" That's much "
                    "easier to hear than silence followed by a blow-up."
                ),
            },
            "breakup": {
                "label": "Considering a breakup",
                "text": (
                    "This is a big one — take your time with it. Ask "
                    "yourself: is this a bad season, or a pattern that keeps "
                    "repeating no matter what changes? If you haven't had a "
                    "direct, honest conversation about the specific problem "
                    "yet, that's usually worth doing before deciding."
                ),
            },
        },
    },
    "family": {
        "label": "👪 Family",
        "situations": {
            "parents": {
                "label": "Conflict with parents",
                "text": (
                    "Family conflict often comes from old roles that don't "
                    "fit anymore — they may still see you as younger than "
                    "you are. Try stating your position calmly and once, "
                    "without over-explaining or asking for permission. You "
                    "can respect someone and still disagree with them."
                ),
            },
            "siblings": {
                "label": "Sibling tension",
                "text": (
                    "Sibling rivalry usually has deep roots — old comparisons "
                    "or unequal treatment growing up. Naming that pattern out "
                    "loud (\"I think we've been comparing ourselves since we "
                    "were kids\") can defuse a lot of tension that otherwise "
                    "plays out sideways."
                ),
            },
            "boundaries": {
                "label": "Setting boundaries",
                "text": (
                    "A boundary is just a clear statement of what you will "
                    "and won't do — it doesn't need justification or "
                    "permission. Keep it short: \"I won't be able to do X "
                    "anymore.\" Expect some pushback the first few times; "
                    "that's normal, not a sign you're wrong."
                ),
            },
        },
    },
    "friendship": {
        "label": "🤝 Friendship",
        "situations": {
            "drifting": {
                "label": "Drifting apart",
                "text": (
                    "Friendships often fade from neglect, not conflict. If "
                    "it still matters to you, be the one who reaches out "
                    "first — a simple \"I miss talking, can we catch up?\" "
                    "goes further than waiting to see if they will."
                ),
            },
            "betrayal": {
                "label": "Feeling betrayed",
                "text": (
                    "Give yourself permission to be upset — that's valid. "
                    "When you're ready, a direct conversation (not a group "
                    "chat callout) about what happened and how it affected "
                    "you usually gets further than silence or gossip."
                ),
            },
            "toxic": {
                "label": "A draining friendship",
                "text": (
                    "Notice how you feel after spending time with them — "
                    "energized or depleted? You don't need a dramatic exit; "
                    "you can just spend less time there and invest more "
                    "where it feels mutual."
                ),
            },
        },
    },
    "work": {
        "label": "💼 Work",
        "situations": {
            "coworker": {
                "label": "Coworker conflict",
                "text": (
                    "Keep it about the specific behavior, not the person: "
                    "\"When X happens, it affects Y\" lands better than "
                    "general complaints. If it's a pattern and not a one-off, "
                    "it may be worth involving a manager rather than "
                    "handling it alone indefinitely."
                ),
            },
            "boss": {
                "label": "Issues with my boss",
                "text": (
                    "Document specifics (dates, what was said) before any "
                    "confrontation — it keeps the conversation factual. "
                    "Approach it as solving a problem together rather than "
                    "an accusation, even if you're frustrated."
                ),
            },
            "burnout": {
                "label": "Feeling burned out",
                "text": (
                    "Burnout is a signal, not a personal failing. Look at "
                    "what's actually driving it — workload, lack of control, "
                    "or lack of recognition are the three most common causes "
                    "— and address that specific thing rather than just "
                    "\"pushing through.\""
                ),
            },
        },
    },
}

CLOSING_NOTE = (
    "\n\nWant to talk through something else? Send /start anytime."
)

# ---------------------------------------------------------------------------
# Keyboard builders
# ---------------------------------------------------------------------------

def main_menu_keyboard():
    buttons = [
        [InlineKeyboardButton(topic["label"], callback_data=f"topic:{key}")]
        for key, topic in TOPICS.items()
    ]
    return InlineKeyboardMarkup(buttons)


def topic_menu_keyboard(topic_key: str):
    situations = TOPICS[topic_key]["situations"]
    buttons = [
        [InlineKeyboardButton(sit["label"], callback_data=f"situation:{topic_key}:{sit_key}")]
        for sit_key, sit in situations.items()
    ]
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="menu:main")])
    return InlineKeyboardMarkup(buttons)


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MESSAGE, reply_markup=main_menu_keyboard())


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "menu:main":
        await query.edit_message_text(WELCOME_MESSAGE, reply_markup=main_menu_keyboard())
        return

    if data.startswith("topic:"):
        topic_key = data.split(":", 1)[1]
        topic = TOPICS.get(topic_key)
        if not topic:
            await query.edit_message_text(WELCOME_MESSAGE, reply_markup=main_menu_keyboard())
            return
        await query.edit_message_text(
            f"{topic['label']} — what's going on?",
            reply_markup=topic_menu_keyboard(topic_key),
        )
        return

    if data.startswith("situation:"):
        _, topic_key, sit_key = data.split(":", 2)
        topic = TOPICS.get(topic_key)
        situation = topic["situations"].get(sit_key) if topic else None
        if not situation:
            await query.edit_message_text(WELCOME_MESSAGE, reply_markup=main_menu_keyboard())
            return
        text = situation["text"] + CLOSING_NOTE
        await query.edit_message_text(text, reply_markup=topic_menu_keyboard(topic_key))
        return


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Jose Alvarez bot (simple, button-based) starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
