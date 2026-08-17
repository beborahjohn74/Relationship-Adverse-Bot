# Jose Alvarez — Relationship Advice Bot (Hybrid Version)

Pick a topic from a button menu (Romance / Family / Friendship), then chat
normally — Jose listens, asks follow-up questions, and gives real, practical
advice using AI, focused on the topic you picked.

## Stack
- **python-telegram-bot** — Telegram integration
- **Google Gemini (`gemini-flash-latest`)** — free-tier conversational AI
- Conversation history is kept in memory per user while the bot is running
  (no database) — restarting the bot clears it.

## 1. Get your API keys

**Telegram bot token**
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. `/newbot`, follow the prompts
3. Copy the token it gives you

**Gemini API key (free)**
1. Go to https://aistudio.google.com/app/apikey
2. If it fails to auto-create a project, create one manually first at
   https://console.cloud.google.com/projectcreate, then go back and choose
   "Create API key in existing project"
3. Copy the key

## 2. Local setup

```bash
git clone <your-repo-url>
cd jose-alvarez-bot
pip install -r requirements.txt
cp .env.example .env   # then fill in your actual keys
python bot.py
```

Message your bot on Telegram — send `/start` to see the topic menu.

## 3. Deploy on Railway

1. Push this repo to GitHub
2. In Railway: **New Project → Deploy from GitHub repo**
3. Add environment variables:
   - `TELEGRAM_BOT_TOKEN`
   - `GEMINI_API_KEY`
4. Set the start command to `python bot.py` if not auto-detected.

## How it works

- `/start` shows the topic menu
- Tapping a topic (e.g. "Romance") tells Jose what kind of relationship
  you're here to talk about
- From then on, just type normally — Jose responds in character, asking
  questions and giving advice
- `/reset` clears the conversation and shows the menu again

## ⚠️ Avoiding duplicate-bot conflicts

If you ever ran a different/older version of this bot with the **same
Telegram bot token** — locally on your computer, or as a separate Railway
service — stop that other process before testing. Two programs polling the
same token at once causes replies to randomly come from whichever one
Telegram hands the message to, which looks like the bot glitching between
different personalities.

## Model name note

`gemini-flash-latest` is an alias Google maintains to always point at their
current stable Flash model, so this should keep working even as Google
retires specific dated model versions (which has happened before with
hardcoded names like `gemini-2.0-flash`).
