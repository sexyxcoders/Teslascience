# =========================
# Created by git @karmaxexclusive
# =========================

import asyncio
import logging
import sys
from datetime import datetime # Import datetime
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from TeslaQuiz.config import BOT_TOKEN
from TeslaQuiz.scheduler.quiz_scheduler import setup_scheduler
from TeslaQuiz.utils.plugin_loader import load_plugins
from TeslaQuiz.database.manager import connect_to_mongo, close_mongo_connection

BOT_START_TIME = datetime.utcnow()

async def main() -> None:
    """Initializes and starts the bot."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
        force=True
    )
    logging.info("Logging configured successfully.")

    await connect_to_mongo()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher()
    # Pass the start time to the dispatcher so handlers can access it
    dp["bot_start_time"] = BOT_START_TIME 
    
    scheduler = AsyncIOScheduler()
    load_plugins(dp)
    await setup_scheduler(bot, scheduler)

    logging.info("Bot is starting polling...")
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()
        await close_mongo_connection()
        logging.info("Bot has been shut down.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped by user.")

# =========================
