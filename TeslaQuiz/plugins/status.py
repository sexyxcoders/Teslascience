# =========================
# Created by git @karmaxexclusive
# =========================

import logging
from datetime import datetime
from aiogram import Bot, Router, types
from aiogram.filters import Command

from TeslaQuiz.config import OWNER_ID
from TeslaQuiz.database import manager as db_manager

router = Router()

def format_uptime(start_time: datetime) -> str:
    """Formats the uptime into a human-readable string."""
    uptime_delta = datetime.utcnow() - start_time
    days = uptime_delta.days
    hours, rem = divmod(uptime_delta.seconds, 3600)
    minutes, _ = divmod(rem, 60)
    return f"{days}d {hours}h {minutes}m"

@router.message(Command("status"))
async def command_status_handler(message: types.Message, bot: Bot, bot_start_time: datetime):
    """
    Handler for the /status command. Provides statistics about the bot's
    performance. Restricted to the bot owner.
    """
    if message.from_user.id != OWNER_ID:
        return # Silently ignore for non-owners

    try:
        # Gather all statistics
        total_chats = await db_manager.get_total_chat_count()
        enabled_chats = await db_manager.get_enabled_chat_count()
        total_players = await db_manager.get_total_unique_players()
        total_users_started = await db_manager.get_total_users_started() # <-- New metric
        
        status_text = (
            f"<b>📊 Bot Status</b>\n\n"
            f"<b>Uptime:</b> {format_uptime(bot_start_time)}\n\n"
            f"<b>Chats:</b>\n"
            f"  - Quizzes Enabled: {enabled_chats}\n"
            f"  - Total Chats Joined: {total_chats}\n\n"
            f"<b>Users:</b>\n"
            f"  - Total Users Started: {total_users_started}\n" # <-- New metric displayed
            f"  - Total Unique Players: {total_players}"
        )
        
        await message.answer(status_text)
        
    except Exception as e:
        logging.error(f"Error in /status command: {e}")
        await message.answer("An error occurred while fetching bot status.")

# =========================
