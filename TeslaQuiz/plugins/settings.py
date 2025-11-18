# =========================
# Created by git @karmaxexclusive
# =========================

import logging
from datetime import datetime, timedelta
from aiogram import F, Bot, Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.enums.chat_member_status import ChatMemberStatus

from TeslaQuiz.database import manager as db_manager

router = Router()

# Using temporary values for testing
INTERVAL_OPTIONS = {
    "Default (1h)": 3600,
    "30 min": 1800,
    "2 hours": 7200,
}

async def is_admin(bot: Bot, chat_id: int, user_id: int) -> bool:
    """Checks if a user is an admin or creator of the chat."""
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR]
    except Exception:
        return False

async def build_settings_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    """Builds the settings keyboard."""
    settings = await db_manager.get_chat_settings(chat_id)
    buttons = []
    interval_row = []
    for text, seconds in INTERVAL_OPTIONS.items():
        button_text = text + (" ✅" if settings.quiz_interval_seconds == seconds else "")
        interval_row.append(InlineKeyboardButton(text=button_text, callback_data=f"set_interval:{seconds}"))
    buttons.append(interval_row)
    toggle_text = "✅ Quizzes Enabled" if settings.scheduler_enabled else "❌ Quizzes Disabled"
    buttons.append([InlineKeyboardButton(text=toggle_text, callback_data="toggle_scheduler")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(Command("settings"))
async def command_settings_handler(message: types.Message, bot: Bot) -> None:
    """Handler for the /settings command."""
    if message.chat.type == "private":
        await message.answer("This command is only available in group chats.")
        return
    if not await is_admin(bot, message.chat.id, message.from_user.id):
        await message.answer("Only group admins can change the settings.")
        return
    keyboard = await build_settings_keyboard(message.chat.id)
    await message.answer("⚙️ **Bot Settings**\n\nChoose the quiz frequency and status for this chat.", reply_markup=keyboard)

@router.callback_query(F.data.startswith("set_interval:"))
async def interval_callback_handler(query: CallbackQuery, bot: Bot):
    """Handles interval selection and resets the timer."""
    if not await is_admin(bot, query.message.chat.id, query.from_user.id):
        await query.answer("Only admins can change settings.", show_alert=True)
        return
    
    interval_seconds = int(query.data.split(":")[1])
    await db_manager.update_chat_interval(query.message.chat.id, interval_seconds)
    
    # By setting the last quiz time to the past, we ensure the next quiz
    # is sent on the very next scheduler check (within 60 seconds).
    reset_time = datetime.utcnow() - timedelta(seconds=interval_seconds)
    await db_manager.update_last_quiz_timestamp(query.message.chat.id, reset_time)
    
    keyboard = await build_settings_keyboard(query.message.chat.id)
    await query.message.edit_reply_markup(reply_markup=keyboard)
    await query.answer("Quiz interval updated! The next quiz will arrive shortly.")


@router.callback_query(F.data == "toggle_scheduler")
async def toggle_scheduler_callback_handler(query: CallbackQuery, bot: Bot):
    """Handles enabling or disabling quizzes."""
    if not await is_admin(bot, query.message.chat.id, query.from_user.id):
        await query.answer("Only admins can change settings.", show_alert=True)
        return
    current_settings = await db_manager.get_chat_settings(query.message.chat.id)
    new_status = not current_settings.scheduler_enabled
    await db_manager.set_chat_active_status(query.message.chat.id, new_status)
    keyboard = await build_settings_keyboard(query.message.chat.id)
    await query.message.edit_reply_markup(reply_markup=keyboard)
    status_text = "enabled" if new_status else "disabled"
    await query.answer(f"Quizzes have been {status_text}.")

# =========================
