# =========================
# Created by git @karmaxexclusive
# =========================

# import random
# from aiogram import Router, types
# from aiogram.filters import Command

# from TeslaQuiz.data.quiz_loader import QUIZZES

# router = Router()
# active_quizzes = {}

# @router.message(Command("quiz"))
# async def command_quiz_handler(message: types.Message) -> None:
#     """Handler for the /quiz command."""
#     if not QUIZZES:
#         await message.answer("😔 Sorry, I couldn't load any quizzes.")
#         return

#     random_quiz = random.choice(QUIZZES)
    
#     sent_poll = await message.answer_poll(
#         question=random_quiz["question"],
#         options=random_quiz["options"],
#         type="quiz",
#         correct_option_id=random_quiz["correct_answer"],
#         is_anonymous=False
#         # The 'open_period' parameter has been completely removed.
#     )
    
#     active_quizzes[sent_poll.poll.id] = {
#         "correct_option_id": random_quiz["correct_answer"],
#         "chat_id": message.chat.id,
#         "message_id": sent_poll.message_id
#     }

from aiogram import Router

router = Router()

# --- Shared Quiz Tracking Dictionaries ---
# This file now only holds the variables shared between the scheduler and poll_handler.

# Tracks all active polls by their unique poll ID
# Format: {poll_id: {"correct_option_id": int, "chat_id": int, "message_id": int}}
active_quizzes = {}

# Maps a chat ID to the message ID of its currently active poll for easy cleanup
# Format: {chat_id: message_id}
chat_active_polls = {}

# =========================
