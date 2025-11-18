# =========================
# Created by git @karmaxexclusive
# =========================

import logging
from aiogram import Bot, Router, types

# Import the shared dictionary from the quiz plugin
from TeslaQuiz.plugins.quiz import active_quizzes
from TeslaQuiz.database import manager as db_manager

router = Router()

@router.poll_answer()
async def handle_poll_answer(poll_answer: types.PollAnswer, bot: Bot) -> None:
    """Handler for processing user answers to polls."""
    poll_id = poll_answer.poll_id
    
    if poll_id in active_quizzes:
        quiz_info = active_quizzes[poll_id]
        
        if poll_answer.option_ids[0] == quiz_info["correct_option_id"]:
            user = poll_answer.user
            chat_id = quiz_info["chat_id"]
            
            try:
                # Use the new function to log the answer for time-based leaderboards
                await db_manager.log_correct_answer(user.id, chat_id, user.full_name)
                logging.info(f"Database score updated for user {user.id} in chat {chat_id}.")
                
                user_mention = user.mention_html()
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"{user_mention} have answered the quiz correctly",
                    reply_to_message_id=quiz_info["message_id"]
                )
            except Exception as e:
                logging.error(f"Could not update score for user {user.id}: {e}")
            
            # This quiz is finished, remove it from tracking
            del active_quizzes[poll_id]

# =========================
