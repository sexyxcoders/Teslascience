# =========================
# Created by git @karmaxexclusive
# =========================

import logging
from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.utils.markdown import hbold

from TeslaQuiz.database import manager as db_manager

router = Router()

async def build_leaderboard_message(scope: str, time_range: str, chat_id: int):
    """Builds the leaderboard text and the interactive keyboard."""
    leaderboard_data = await db_manager.get_leaderboard(
        time_range=time_range,
        chat_id=chat_id if scope == "chat" else None
    )

    scope_text = "Current Chat" if scope == "chat" else "Global"
    time_text = {"all": "All Time", "week": "This Week", "today": "Today"}.get(time_range, "All Time")
    
    text = f"<b>🏆 Leaderboard - {scope_text} ({time_text})</b>\n\n"

    if not leaderboard_data:
        text += "<i>The leaderboard is empty for this selection!</i>"
    else:
        leaderboard_entries = []
        for i, user in enumerate(leaderboard_data, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"<b>{i}.</b>"
            # Sanitize username to prevent HTML injection
            username = user.get('username', 'Unknown User').replace("<", "&lt;").replace(">", "&gt;")
            score = user.get('score', 0)
            leaderboard_entries.append(f"{medal} {username} - {hbold(score)} points")
        text += "\n".join(leaderboard_entries)

    # Build the interactive keyboard
    buttons = [
        [
            InlineKeyboardButton(
                text=f"📍 Current Chat{' ✅' if scope == 'chat' else ''}",
                callback_data=f"lb:chat:{time_range}"
            ),
            InlineKeyboardButton(
                text=f"🌍 Global{' ✅' if scope == 'global' else ''}",
                callback_data=f"lb:global:{time_range}"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"Today{' ✅' if time_range == 'today' else ''}",
                callback_data=f"lb:{scope}:today"
            ),
            InlineKeyboardButton(
                text=f"Week{' ✅' if time_range == 'week' else ''}",
                callback_data=f"lb:{scope}:week"
            ),
            InlineKeyboardButton(
                text=f"All Time{' ✅' if time_range == 'all' else ''}",
                callback_data=f"lb:{scope}:all"
            ),
        ]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return text, keyboard


@router.message(Command("leaderboard"))
async def command_leaderboard_handler(message: types.Message) -> None:
    """Handler for the /leaderboard command, shows the default view."""
    try:
        text, reply_markup = await build_leaderboard_message(
            scope="chat", time_range="all", chat_id=message.chat.id
        )
        await message.answer(text, reply_markup=reply_markup)
    except Exception as e:
        await message.answer("😔 An error occurred while fetching the leaderboard.")
        logging.error(f"Error in /leaderboard for chat {message.chat.id}: {e}")


@router.callback_query(F.data.startswith("lb:"))
async def leaderboard_callback_handler(query: CallbackQuery):
    """Handler for leaderboard button presses, updates the message."""
    try:
        # Extract scope and time_range from callback data (e.g., "lb:chat:week")
        _, scope, time_range = query.data.split(":")
        
        text, reply_markup = await build_leaderboard_message(
            scope=scope, time_range=time_range, chat_id=query.message.chat.id
        )

        # Edit the message only if the content has changed to avoid Telegram API errors
        if query.message.text != text or query.message.reply_markup != reply_markup:
             await query.message.edit_text(text, reply_markup=reply_markup)
        
        # Acknowledge the callback to remove the "loading" state on the user's client
        await query.answer()

    except Exception as e:
        logging.error(f"Error in leaderboard callback: {e}")
        await query.answer("Error updating leaderboard.", show_alert=True)

# =========================
