# Jose Alvarez — Relationship Advice Bot (Simple Version)

A Telegram bot that helps people think through relationship, family,
friendship, and work problems — using a simple button menu, no external AI
API. Pick a topic, pick a situation, get practical advice.

## Stack
- **python-telegram-bot** only — no Gemini, no OpenAI, no database

## 1. Get your API key

You only need **one** thing: a Telegram bot token.

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. `/newbot`, follow the prompts (choose a name and a username ending in "bot")
3. Copy the token it gives you

That's it — no other keys or accounts required.

## 2. Local setup

```bash
git clone <your-repo-url>
cd jose-alvarez-bot
pip install -r requirements.txt
cp .env.example .env   # then paste in your actual token
```

Load the `.env` file however you prefer, then run:

```bash
python bot.py
```

Message your bot on Telegram — send `/start` to see the menu.

## 3. Deploy on Railway

1. Push this repo to GitHub
2. In Railway: **New Project → Deploy from GitHub repo**
3. Add one environment variable in Railway's dashboard:
   - `TELEGRAM_BOT_TOKEN`
4. Railway auto-detects Python and installs `requirements.txt`. Set the
   **start command** to `python bot.py` if it isn't picked up automatically.

No volumes, no database, no persistence to worry about — this version has
no memory between messages, so there's nothing that can get wiped on
redeploy.

## How it works

- `/start` shows the main topic menu (Romance / Family / Friendship / Work)
- Tapping a topic shows a sub-menu of common situations
- Tapping a situation shows Jose's advice for that specific thing, plus a
  "Back" button to pick something else

## Customizing the content

Everything lives in the `TOPICS` dictionary in `bot.py`. Each topic has a
`label` and a set of `situations`; each situation has a `label` (the button
text) and a `text` (the advice shown). Add, remove, or edit entries there —
no other code changes needed.

## ⚠️ One thing to check before you redeploy

If you ever ran an earlier/different version of this bot (or a different
project) using the **same Telegram bot token**, make sure that other process
is fully stopped — whether it's running locally on your computer or as a
separate Railway service. Two programs polling the same token at once causes
replies to randomly come from whichever one Telegram hands the message to,
which looks like the bot "glitching" between two different personalities.
