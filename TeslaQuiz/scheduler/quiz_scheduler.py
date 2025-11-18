# =========================
# Created by git @karmaxexclusive
# =========================

import logging
import random
from datetime import datetime, timedelta
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from TeslaQuiz.database import manager as db_manager
from TeslaQuiz.data.quiz_loader import QUIZZES
from TeslaQuiz.plugins.quiz import active_quizzes, chat_active_polls

async def send_scheduled_quiz(bot: Bot):
    """
    Runs every minute, checks all active chats, and sends a quiz
    only if the chat's custom interval has passed.
    """
    if not QUIZZES:
        return

    active_chats = await db_manager.get_all_scheduled_chats()
    if not active_chats:
        return

    logging.info(f"Scheduler check run: Checking {len(active_chats)} active chats.")
    
    chats_to_send = []
    now = datetime.utcnow()
    for chat_settings in active_chats:
        time_since_last_quiz = now - chat_settings.last_quiz_timestamp
        if time_since_last_quiz >= timedelta(seconds=chat_settings.quiz_interval_seconds):
            chats_to_send.append(chat_settings)

    if not chats_to_send:
        return

    logging.info(f"Scheduler sending quizzes to {len(chats_to_send)} due chats.")
    random_quiz = random.choice(QUIZZES)

    for chat in chats_to_send:
        chat_id = chat.chat_id
        try:
            if chat_id in chat_active_polls:
                await bot.stop_poll(chat_id, chat_active_polls[chat_id])

            sent_poll_message = await bot.send_poll(
                chat_id=chat_id,
                question=random_quiz["question"],
                options=random_quiz["options"],
                type="quiz",
                correct_option_id=random_quiz["correct_answer"],
                is_anonymous=False
            )
            
            poll_id = sent_poll_message.poll.id
            message_id = sent_poll_message.message_id
            active_quizzes[poll_id] = { "correct_option_id": random_quiz["correct_answer"], "chat_id": chat_id, "message_id": message_id }
            chat_active_polls[chat_id] = message_id

            await db_manager.update_last_quiz_timestamp(chat_id)
            logging.info(f"Quiz sent to chat {chat_id} and timestamp updated.")

        except Exception as e:
            logging.error(f"Scheduler failed for chat {chat_id}: {e}")
            # Consider marking the chat as inactive if there are persistent errors
            if "bot was kicked" in str(e) or "not enough rights" in str(e):
                await db_manager.set_chat_active_status(chat_id, False)
                logging.warning(f"Disabling scheduler for chat {chat_id} due to error: {e}")

async def setup_scheduler(bot: Bot, scheduler: AsyncIOScheduler):
    """Adds the quiz job to run every 60 seconds."""
    scheduler.add_job(
        send_scheduled_quiz,
        trigger='interval',
        seconds=60,
        args=[bot]
    )
    try:
        scheduler.start()
        logging.info("Scheduler has been started (running every 60s).")
    except Exception as e:
        logging.error(f"Error starting scheduler: {e}")

# =========================
