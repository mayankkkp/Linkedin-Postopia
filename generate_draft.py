import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from google import genai
from google.genai import types
import time
import requests
import xml.etree.ElementTree as ET
import json

load_dotenv()

# New SDK initialization method
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")



def get_trending_topic():
    """Fetch trending topics, filter for education/technology relevance."""
    try:
        url = "https://trends.google.com/trending/rss?geo=IN"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()

        root = ET.fromstring(resp.content)
        items = root.findall('.//item')
        titles = [item.findtext('title') for item in items if item.findtext('title')]

        if not titles:
            raise ValueError("No trending titles found")

        # Ask Gemini to pick the most relevant one
        selection_prompt = f"""
        Here are today's trending search topics: {json.dumps(titles[:15])}

        Pick the ONE topic that is most relevant to "education" or "technology".
        If none of them are even loosely related to education or technology, reply with exactly: NONE

        Reply with only the chosen topic text, nothing else.
        """
        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=selection_prompt,
        )
        chosen = response.text.strip()

        if chosen and chosen.upper() != "NONE":
            print(f"Auto-selected topic (filtered): {chosen}")
            return chosen

    except Exception as e:
        print(f"Trending fetch/filter failed ({e})")

    # Fallback niche topic
    print("No relevant trend found, using fallback niche topic.")
    return "The intersection of education and technology"

def generate_post(topic):
    prompt = f"""
    Write a professional LinkedIn post about: {topic}.

    Requirements:
    - Frame the topic specifically through the lens of education and technology.
    - Length: around 600-900 characters.
    - Start with a hook that grabs attention in the first two lines.
    - Include one concrete insight or example that makes the post feel personal, not generic.
    - End with a question or a call to action that invites comments.
    - Include 3 relevant hashtags at the very end.
    - Do not use emojis.
    - Output only the post text, nothing else.
    """
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model='gemini-3.8-flash',
                contents=prompt,
            )
            # Robustly extract text
            text = None
            if response.text:
                text = response.text.strip()
            elif response.candidates:
                parts = response.candidates[0].content.parts
                text = "".join(p.text for p in parts if hasattr(p, "text") and p.text).strip()

            if not text or text.upper() == "NONE":
                raise ValueError("Model returned empty or NONE")

            return text

        except Exception as e:
            error_str = str(e)

            # Retryable errors (rate limit / overload)
            if any(k in error_str for k in ("429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE")):
                wait = 15 * (attempt + 1)
                print(f"Model busy or quota hit, waiting {wait}s before retry...")
                time.sleep(wait)
                continue  # move to next attempt

            # Empty/NONE output: retry once, then give up
            if isinstance(e, ValueError):
                print(f"Empty model output on attempt {attempt + 1}, retrying...")
                time.sleep(5)
                continue

            # Any other error: re-raise immediately
            raise

    # All attempts exhausted — return None so caller can handle gracefully
    print("Generation failed after 3 attempts.")
    return None

async def send_draft_for_approval(text):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    keyboard = [
        [
            InlineKeyboardButton("✅ Publish", callback_data="approve"),
            InlineKeyboardButton("❌ Discard", callback_data="reject"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=f"📝 Draft:\n\n{text}",
        reply_markup=reply_markup,
    )

def main():
    topic = get_trending_topic()
    print(f"Generating post about: {topic}")
    post_text = generate_post(topic)
    if not post_text:
        print("No draft generated. Exiting without sending.")
        return
    print(f"Draft:\n{post_text}")
    asyncio.run(send_draft_for_approval(post_text))
    print("Sent to Telegram. Check your phone.")

if __name__ == "__main__":
    main()