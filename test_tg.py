import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

async def test():
    bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
    await bot.send_message(
        chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        text="Test: Bot is connected successfully."
    )
    print("Message sent, check your Telegram.")

asyncio.run(test())