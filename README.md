# Jose Alvarez — Relationship Advice Bot (Groq Version)

Pick a topic from a button menu (Romance / Family / Friendship), then chat
normally — Jose listens, asks follow-up questions, and gives real, practical
advice using AI, focused on the topic you picked.

## Stack
- **python-telegram-bot** — Telegram integration
- **Groq API (`openai/gpt-oss-120b`)** — free-tier conversational AI
- Conversation history is kept in memory per user while the bot is running
  (no database) — restarting the bot clears it.

## Why Groq instead of Gemini

Gemini's free tier caps out at only ~20 requests per day per model — fine
for solo testing, not enough for real users. Groq's free tier is far more
generous (tens of thousands of requests/day range), with no card required,
so it actually supports many people using the bot in a day.

## 1. Get your API keys

**Telegram bot token**
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. `/newbot`, follow the prompts
3. Copy the token it gives you

**Groq API key (free)**
1. Go to https://console.groq.com
2. Sign up / log in (no card required)
3. Go to API Keys → Create API Key
4. Copy the key

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
   - `GROQ_API_KEY`
4. Set the start command to `python bot.py` if not auto-detected.
5. **Important:** after adding/changing variables, make sure Railway actually
   redeploys — check the Deployments tab shows a fresh deploy timestamp, not
   an older one that predates the variable.

## How it works

- `/start` shows the topic menu
- Tapping a topic (e.g. "Romance") tells Jose what kind of relationship
  you're here to talk about
- From then on, just type normally — Jose responds in character, asking
  questions and giving advice
- `/reset` clears the conversation and shows the menu again

## ⚠️ Avoiding duplicate-bot conflicts

If you ever run a different/older version of this bot with the **same
Telegram bot token** — on a different Railway account, locally, or anywhere
else — stop that other process before testing. Two programs polling the
same token at once causes replies to randomly come from whichever one
Telegram hands the message to, which looks like the bot glitching between
different personalities. (This happened once already — an old deployment on
a first Railway account kept running after switching to a second account.)

## Model name note

Groq occasionally deprecates specific model versions (this happened to
`llama-3.3-70b-versatile`, which this bot used to use). If you start seeing
errors mentioning a model name, check
https://console.groq.com/docs/models for Groq's current recommended model
and update the `GROQ_MODEL` constant in `bot.py`.
