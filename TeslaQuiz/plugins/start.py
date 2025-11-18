# =========================
# Created by git @karmaxexclusive
# =========================

import logging
from aiogram import Bot, Router, types
from aiogram.filters import CommandStart
from aiogram.utils.markdown import hbold

from TeslaQuiz.database import manager as db_manager
from TeslaQuiz.config import LOG_CHANNEL_ID

router = Router()

@router.message(CommandStart())
async def command_start_handler(message: types.Message, bot: Bot) -> None:
    """
    Handles the /start command in both private messages and groups.
    Logs new users who start the bot privately.
    """
    user = message.from_user
    chat_type = message.chat.type

    # --- Handle Private Chat /start ---
    if chat_type == "private":
        # Add user to DB and check if they are new
        is_new_user = await db_manager.add_new_user(
            user_id=user.id,
            full_name=user.full_name,
            username=user.username or "N/A"
        )
        
        # If they are a new user, send a log message
        if is_new_user and LOG_CHANNEL_ID:
            try:
                log_text = (
                    f"<b>#NewUser</b>\n\n"
                    f"<b>User:</b> {user.mention_html()} ({user.id})\n"
                    f"<b>Username:</b> @{user.username or 'N/A'}"
                )
                await bot.send_message(LOG_CHANNEL_ID, log_text)
            except Exception as e:
                logging.error(f"Failed to send new user log for {user.id}: {e}")

        # Send welcome message
        start_message = (
            f"👋 Hello, {hbold(user.full_name)}!\n\n"
            "I am the Tesla Quiz Bot. Add me to a group chat, and I'll start sending quizzes based on the group's settings."
        )
        await message.answer(start_message)
        
    # --- Handle Group Chat /start ---
    elif chat_type in ["group", "supergroup"]:
        chat_id = message.chat.id
        # In groups, /start simply reactivates quizzes if they were disabled.
        settings = await db_manager.get_chat_settings(chat_id)
        if not settings.scheduler_enabled:
            await db_manager.set_chat_active_status(chat_id, True)
            await message.answer("✅ Quizzes have been re-enabled for this chat!")
            logging.info(f"Chat {chat_id} re-activated via /start command.")
        else:
            await message.answer("👋 Hello! I'm already set up to send quizzes here.")

# =========================
