# Jose Alvarez — Relationship Advice Bot

A Telegram bot that chats warmly with people about their relationship, family,
friendship, and work problems, and gives practical advice. Remembers each
user's conversation history so it can refer back to earlier context.

## Stack
- **python-telegram-bot** — Telegram integration
- **Google Gemini (`gemini-2.0-flash`)** — free-tier conversational AI
- **SQLite** — per-user conversation memory

## 1. Get your API keys

**Telegram bot token**
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. `/newbot`, follow the prompts
3. Copy the token it gives you

**Gemini API key (free)**
1. Go to https://aistudio.google.com/app/apikey
2. Create an API key (free tier — generous daily limits, no card required)
3. Copy the key

## 2. Local setup

```bash
git clone <your-repo-url>
cd jose-alvarez-bot
pip install -r requirements.txt
cp .env.example .env   # then fill in your actual keys
```

Load the `.env` file however you prefer (e.g. `python-dotenv`, or just
`export $(cat .env | xargs)` on Mac/Linux before running).

```bash
python bot.py
```

Message your bot on Telegram — send `/start` to see the welcome message.

## 3. Deploy on Railway

1. Push this repo to GitHub
2. In Railway: **New Project → Deploy from GitHub repo**
3. Add environment variables in Railway's dashboard:
   - `TELEGRAM_BOT_TOKEN`
   - `GEMINI_API_KEY`
4. Railway auto-detects Python and installs `requirements.txt`. Set the
   **start command** to `python bot.py` if it isn't picked up automatically.

### ⚠️ Important: persistent memory on Railway

Railway's default filesystem is **ephemeral** — it resets every time you
redeploy, which means the SQLite database (and everyone's conversation
history) gets wiped. To keep memory persistent across deploys:

1. In your Railway service, go to **Settings → Volumes**
2. Add a volume, mount it at e.g. `/data`
3. Set the `DB_PATH` environment variable to `/data/jose_memory.db`

Without this step, the bot still works fine — it just "forgets" everyone
whenever you push a new update.

## Commands
- `/start` — welcome message
- `/reset` — wipes that user's conversation history (fresh start)
- Any other text — Jose responds in character

## Customizing the persona

Edit the `SYSTEM_PROMPT` constant in `bot.py`. That's the entire personality —
tone, how much it asks vs. advises, safety guardrails around abuse/crisis
situations, etc. Keep the safety-related lines (about not diagnosing, and
pointing people toward real support in crisis situations) — those matter for
a bot handling sensitive personal topics.

## Notes on scaling advice quality

- `MAX_HISTORY_MESSAGES` in `bot.py` controls how many past messages get sent
  back to Gemini as context per reply. Raise it if you want Jose to remember
  further back, at the cost of slightly higher latency/token use per message.
- Gemini's free tier has rate limits (requests per minute/day). If you expect
  heavy usage, check current limits at https://ai.google.dev/pricing before
  launch.
