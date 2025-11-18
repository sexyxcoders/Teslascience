# =========================
# Created by git @karmaxexclusive
# =========================

import logging
from aiogram import Bot, Router, F, types

from TeslaQuiz.database import manager as db_manager
from TeslaQuiz.config import LOG_CHANNEL_ID

router = Router()

@router.message(F.new_chat_members)
async def on_bot_join_group(message: types.Message, bot: Bot):
    """
    Handles when the bot is added to a new group, sends a welcome message,
    and logs the event.
    """
    for member in message.new_chat_members:
        if member.id == bot.id:
            chat = message.chat
            added_by = message.from_user
            chat_id = chat.id
            
            logging.info(f"Bot was added to chat {chat_id} by {added_by.id}.")
            
            # Create settings and ensure the scheduler is active for the new group.
            await db_manager.get_chat_settings(chat_id)
            await db_manager.set_chat_active_status(chat_id, True)
            
            # --- THIS IS THE FIX: SEND THE WELCOME MESSAGE ---
            # This line was missing.
            try:
                await message.answer(
                    "👋 Thanks for adding me! I will now send quizzes here according to the default schedule.\n\n"
                    "Group admins can use the `/settings` command to change the frequency or disable quizzes."
                )
            except Exception as e:
                logging.error(f"Failed to send welcome message to chat {chat_id}: {e}")

            # --- Send Log Message to Admin Channel ---
            if LOG_CHANNEL_ID:
                try:
                    member_count = await bot.get_chat_member_count(chat_id)
                    log_text = (
                        f"<b>#NewGroup</b>\n\n"
                        f"<b>Group:</b> {chat.title} ({chat_id})\n"
                        f"<b>Username:</b> @{chat.username or 'N/A'}\n"
                        f"<b>Members:</b> {member_count}\n"
                        f"<b>Added by:</b> {added_by.full_name} ({added_by.id})"
                    )
                    await bot.send_message(LOG_CHANNEL_ID, log_text)
                except Exception as e:
                    logging.error(f"Failed to send new group log for {chat_id}: {e}")
            break # Exit the loop once the bot is found

@router.message(F.left_chat_member)
async def on_bot_leave_group(message: types.Message, bot: Bot):
    """Handles when the bot leaves or is kicked from a group."""
    if message.left_chat_member.id == bot.id:
        chat_id = message.chat.id
        chat_title = message.chat.title
        
        logging.info(f"Bot left/was kicked from chat {chat_id}.")
        # Mark the chat as inactive in the database
        await db_manager.set_chat_active_status(chat_id, False)
        
        # --- Send Log Message ---
        if LOG_CHANNEL_ID:
            try:
                log_text = (
                    f"<b>#LeftGroup</b>\n\n"
                    f"<b>Group:</b> {chat_title} ({chat_id})"
                )
                await bot.send_message(LOG_CHANNEL_ID, log_text)
            except Exception as e:
                logging.error(f"Failed to send left group log for {chat_id}: {e}")

# =========================
