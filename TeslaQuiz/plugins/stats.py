# =========================
# Created by git @karmaxexclusive
# =========================

import logging
from aiogram import Bot, Router, types
from aiogram.filters import Command
from aiogram.exceptions import TelegramForbiddenError

from TeslaQuiz.database import manager as db_manager

router = Router()

@router.message(Command("stats"))
async def command_stats_handler(message: types.Message, bot: Bot):
    """
    Handler for the /stats command. Checks if it can message the user,
    then replies privately with their personal statistics.
    """
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # --- THE FIX IS HERE: PERMISSION CHECK ---
    # We first try a harmless action to see if the user has started the bot.
    # If this fails, we catch the error and instruct the user.
    try:
        await bot.send_chat_action(chat_id=user_id, action="typing")
    except TelegramForbiddenError:
        logging.warning(f"Failed to send action to user {user_id}. They haven't started the bot.")
        await message.reply(
            "I can't send you a private message because you haven't started a chat with me yet. "
            "Please click on my username, start a chat, and then use the `/stats` command again."
        )
        return # Stop further execution

    try:
        # --- Get Chat-Specific Stats ---
        chat_stats = await db_manager.get_user_stats_in_chat(user_id, chat_id)
        chat_score = chat_stats.get("score", 0) if chat_stats else 0
        chat_rank = chat_stats.get("rank", "N/A") if chat_stats else "N/A"

        # --- Get Global Stats ---
        global_stats = await db_manager.get_user_global_stats(user_id)
        global_score = global_stats.get("score", 0) if global_stats else 0
        global_rank = global_stats.get("rank", "N/A") if global_stats else "N/A"

        if chat_score == 0 and global_score == 0:
            stats_text = "You haven't answered any quizzes correctly yet. Keep trying!"
        else:
            stats_text = (
                f"<b>Your TeslaQuiz Stats 📊</b>\n\n"
                f"<b>In this Chat:</b>\n"
                f"• <b>Score:</b> {chat_score}\n"
                f"• <b>Rank:</b> #{chat_rank}\n\n"
                f"<b>Globally (across all chats):</b>\n"
                f"• <b>Total Score:</b> {global_score}\n"
                f"• <b>Global Rank:</b> #{global_rank}"
            )

        # Send the stats in a private message to the user
        await bot.send_message(
            chat_id=user_id,
            text=stats_text
        )
        
        # If the command was used in a group, confirm that the message was sent privately
        if message.chat.type != "private":
            await message.reply("✅ I've sent you your personal stats in a private message.", disable_notification=True)

    except Exception as e:
        logging.error(f"Could not fetch stats for user {user_id}: {e}")
        # This is a fallback for other potential errors during stat fetching.
        await bot.send_message(user_id, "😔 An error occurred while fetching your stats. Please try again later.")

# =========================
