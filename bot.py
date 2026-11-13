import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv
import requests

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
LINKEDIN_PERSON_URN = os.getenv("LINKEDIN_PERSON_URN")

def publish_to_linkedin(text):
    url = "https://api.linkedin.com/rest/posts"
    headers = {
        "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "LinkedIn-Version": "202603",  # Must have, use a recent version
        "X-Restli-Protocol-Version": "2.0.0"
    }
    payload = {
        "author": LINKEDIN_PERSON_URN,
        "commentary": text,
        "visibility": "PUBLIC",
        "distribution": {"feedDistribution": "MAIN_FEED"},
        "lifecycleState": "PUBLISHED"
    }
    resp = requests.post(url, headers=headers, json=payload)
    print("LinkedIn response:", resp.status_code, resp.text)  # Key: print it out
    return resp.status_code in (200, 201), resp.text

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass  # Query expired, ignore, continue processing

    original_text = query.message.text
    draft_text = original_text.replace("📝 Draft:\n\n", "").strip()

    if query.data == "approve":
        success, msg = publish_to_linkedin(draft_text)
        if success:
            await query.edit_message_text("✅ Published to LinkedIn.")
        else:
            await query.edit_message_text(f"❌ Failed:\n{msg}")
    elif query.data == "reject":
        await query.edit_message_text("🗑 Discarded.")

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CallbackQueryHandler(button_callback))
    print("Bot listener started. Waiting for button taps...")
    app.run_polling()

if __name__ == "__main__":
    main()