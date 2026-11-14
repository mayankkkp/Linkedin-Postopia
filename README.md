# LinkedIn Postopia

An AI agent that generates LinkedIn posts about education and technology, sends them to Telegram for approval, and publishes them to LinkedIn with a single tap.

## How it works

1. **`generate_draft.py`** — Fetches a trending topic (filtered for education/technology relevance), generates a post with Google Gemini, and sends it to your Telegram chat with **Publish / Discard** buttons.
2. **`bot.py`** — Runs as a background Windows service (via NSSM). Listens for Telegram button taps and, on approval, publishes the draft to LinkedIn through the LinkedIn REST API.

The human stays in the loop: nothing gets posted without your explicit tap.

## Architecture
┌──────────────────┐ ┌──────────────┐ ┌─────────────────┐
│ Google Trends │────▶│ generate_ │────▶│ Telegram Bot │
│ RSS / fallback │ │ draft.py │ │ (Publish/Discard│
└──────────────────┘ │ + Gemini API │ │ buttons) │
└──────────────┘ └────────┬────────┘
│ tap
▼
┌──────────────┐ ┌─────────────────┐
│ LinkedIn API │◀────│ bot.py │
│ /rest/posts │ │ (NSSM service) │
└──────────────┘ └─────────────────┘

text

## Requirements

- Python 3.10+ (tested on 3.15)
- A LinkedIn Developer App with:
  - **Share on LinkedIn** product (`w_member_social` scope)
  - **Sign In with LinkedIn using OpenID Connect** product (`openid`, `profile` scopes)
- A Google Gemini API key (free tier works)
- A Telegram bot created via [@BotFather](https://t.me/BotFather)
- NSSM (Non-Sucking Service Manager) for running `bot.py` as a Windows service

## Setup

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/Linkedin-Postopia.git
cd Linkedin-Postopia
pip install -r requirements.txt
2. Configure secrets
Copy the example file and fill in your credentials:

bash
cp .env.example .env
Required values in .env:

Variable	Where to get it
LINKEDIN_CLIENT_ID	LinkedIn Developer Portal → your app → Auth tab
LINKEDIN_CLIENT_SECRET	Same as above
LINKEDIN_REDIRECT_URI	http://localhost:8080/callback (must match the app settings)
LINKEDIN_ACCESS_TOKEN	Printed by auth.py after the OAuth flow
LINKEDIN_PERSON_URN	Printed by auth.py (format: urn:li:person:xxxx)
GEMINI_API_KEY	Google AI Studio
TELEGRAM_BOT_TOKEN	@BotFather
TELEGRAM_CHAT_ID	@userinfobot
Never commit .env. It is listed in .gitignore for this reason.

3. Authorize LinkedIn (one-time)
bash
python auth.py
A browser window opens. Log in, approve the scopes, and copy the printed Access Token and Person URN into .env.

The token is valid for ~60 days. Re-run auth.py when it expires.

4. Test the Telegram connection
bash
python test_tg.py
You should receive a test message in Telegram. If you get Chat not found, send /start to your bot first.

5. Test the full flow manually
Terminal A:

bash
python bot.py
Terminal B:

bash
python generate_draft.py
Tap Publish on the Telegram message. The post should appear on LinkedIn and the message should change to ✅ Published to LinkedIn.

6. Install bot.py as a Windows service (optional, for automation)
cmd
nssm install LinkedInBotService
Fill in:

Path: full path to python.exe

Startup directory: the project folder

Arguments: full path to bot.py

Then:

cmd
nssm set LinkedInBotService AppDirectory "C:\path\to\Linkedin Postopia"
nssm set LinkedInBotService AppStdout "C:\path\to\Linkedin Postopia\bot_stdout.log"
nssm set LinkedInBotService AppStderr "C:\path\to\Linkedin Postopia\bot_stderr.log"
nssm start LinkedInBotService
Important: Only one bot.py instance may run at a time. Telegram returns Conflict: terminated by other getUpdates request if two poll the same token. If you're debugging manually, stop the service first.

7. Schedule daily draft generation (optional)
Use Windows Task Scheduler:

Program: full path to python.exe

Arguments: "C:\path\to\Linkedin Postopia\generate_draft.py"

Start in: C:\path\to\Linkedin Postopia

Trigger: Daily at your preferred time

General: check "Run whether user is logged on or not"

Files
File	Purpose
auth.py	One-time LinkedIn OAuth flow; prints access token and person URN
generate_draft.py	Fetches topic, generates post with Gemini, sends to Telegram
bot.py	Telegram listener; publishes approved drafts to LinkedIn
test_tg.py	Quick Telegram connectivity check
requirements.txt	Python dependencies
.env.example	Template for environment variables
Known limitations
LinkedIn API versioning — The /rest/posts endpoint requires a LinkedIn-Version header (format YYYYMM). Versions expire; if you get 426 NONEXISTENT_VERSION, bump the header in bot.py to a current version.

Token expiry — LinkedIn access tokens last ~60 days. Re-run auth.py when publishing starts returning 401.

Google Trends RSS — Google occasionally changes or blocks the trending RSS endpoint. The script falls back to a fixed niche topic when this happens.

Gemini availability — gemini-3.8-flash occasionally returns 503 UNAVAILABLE during demand spikes. The generator retries three times with backoff, then falls back to a lighter model.

No engagement automation — This agent only posts to your own feed. It does not read profiles, send connection requests, or comment on others' posts, as those actions require LinkedIn's Community Management API or violate LinkedIn's terms.
