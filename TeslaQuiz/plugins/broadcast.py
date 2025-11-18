# =========================
# Created by git @karmaxexclusive
# =========================

import asyncio
import logging
from aiogram import Bot, Router, types
from aiogram.filters import Command
from aiogram.types import BufferedInputFile

from TeslaQuiz.config import OWNER_ID, LOG_CHANNEL_ID
from TeslaQuiz.database import manager as db_manager

router = Router()

@router.message(Command("broadcast"))
async def command_broadcast_handler(message: types.Message, bot: Bot):
    """
    Handler for the /broadcast command. Sends a message to all users AND
    all groups. Restricted to the bot owner.
    """
    if message.from_user.id != OWNER_ID:
        return # Silently ignore for non-owners

    if not message.reply_to_message:
        await message.reply("Please use this command by replying to the message you want to broadcast.")
        return

    # Get all target audiences from the database
    all_users = await db_manager.get_all_started_users()
    all_chats = await db_manager.get_all_chats()
    
    if not all_users and not all_chats:
        await message.reply("There are no users or chats to broadcast to.")
        return

    # Send initial status message
    status_message = await message.reply(
        f"📢 Starting broadcast...\n"
        f"👤 Targeting {len(all_users)} users.\n"
        f"👥 Targeting {len(all_chats)} groups.\n"
        "Please wait, this may take a while."
    )

    # --- Initialize Counters and Failure Logs ---
    user_success, user_fail = 0, 0
    group_success, group_fail = 0, 0
    failed_user_ids = []
    failed_group_ids = []
    
    # --- Broadcast to Users ---
    logging.info(f"Starting broadcast to {len(all_users)} users.")
    for user in all_users:
        user_id = user['user_id']
        try:
            await bot.forward_message(
                chat_id=user_id,
                from_chat_id=message.chat.id,
                message_id=message.reply_to_message.message_id
            )
            user_success += 1
        except Exception as e:
            user_fail += 1
            failed_user_ids.append(str(user_id))
            logging.warning(f"Failed to broadcast to user {user_id}: {e}")
        await asyncio.sleep(0.1)

    # --- Broadcast to Groups ---
    logging.info(f"Starting broadcast to {len(all_chats)} groups.")
    for chat in all_chats:
        chat_id = chat['chat_id']
        try:
            await bot.forward_message(
                chat_id=chat_id,
                from_chat_id=message.chat.id,
                message_id=message.reply_to_message.message_id
            )
            group_success += 1
        except Exception as e:
            group_fail += 1
            failed_group_ids.append(str(chat_id))
            logging.warning(f"Failed to broadcast to group {chat_id}: {e}")
        await asyncio.sleep(0.1)

    # --- Send Failure Log if Necessary ---
    log_file_sent = False
    if (failed_user_ids or failed_group_ids) and LOG_CHANNEL_ID:
        try:
            log_content = "--- BROADCAST FAILURE LOG ---\n\n"
            if failed_user_ids:
                log_content += "Failed User IDs:\n" + "\n".join(failed_user_ids) + "\n\n"
            if failed_group_ids:
                log_content += "Failed Group & Channel IDs:\n" + "\n".join(failed_group_ids)
            
            log_file = BufferedInputFile(log_content.encode('utf-8'), filename="broadcast_failures.txt")
            await bot.send_document(LOG_CHANNEL_ID, log_file, caption="A log of failed broadcast deliveries.")
            log_file_sent = True
        except Exception as e:
            logging.error(f"Failed to send broadcast log file: {e}")

    # --- Final Report ---
    final_report = (
        f"<b>Broadcast Complete ✅</b>\n\n"
        f"👤 <b>Users:</b>\n"
        f"  - Successful: {user_success} / {len(all_users)}\n"
        f"  - Failed: {user_fail}\n\n"
        f"👥 <b>Groups & Channels:</b>\n"
        f"  - Successful: {group_success} / {len(all_chats)}\n"
        f"  - Failed: {group_fail}"
    )
    if log_file_sent:
        final_report += "\n\n<i>A log of failed IDs has been sent to the log channel.</i>"
        
    await status_message.edit_text(final_report)

# =========================
