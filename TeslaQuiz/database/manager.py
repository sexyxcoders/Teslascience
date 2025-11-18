# =========================
# Created by git @karmaxexclusive
# =========================

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import certifi
import motor.motor_asyncio
from TeslaQuiz.config import MONGO_URI
from TeslaQuiz.database.models import ChatSettings

# --- Database Client Setup ---
client = None
db = None
users_collection = None # For tracking users who have /start-ed the bot
chats_collection = None # For chat-specific settings
quiz_logs_collection = None # For all quiz scores and events

async def connect_to_mongo():
    """Initializes the MongoDB client and all database collections."""
    global client, db, users_collection, chats_collection, quiz_logs_collection
    try:
        client = motor.motor_asyncio.AsyncIOMotorClient(
            MONGO_URI,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=5000
        )
        await client.admin.command('ismaster')
        logging.info("✅ Successfully connected to MongoDB.")
        db = client.TeslaQuizBot
        users_collection = db.users
        chats_collection = db.chats
        quiz_logs_collection = db.quiz_logs
        # Create indexes for performance
        await quiz_logs_collection.create_index([("timestamp", -1)])
        await quiz_logs_collection.create_index([("chat_id", 1), ("user_id", 1)])
        await users_collection.create_index([("user_id", 1)], unique=True)
        logging.info("✅ Database indexes ensured.")
    except Exception as e:
        logging.critical(f"❌ Failed to connect to MongoDB: {e}")
        client = None

async def close_mongo_connection():
    """Closes the MongoDB connection."""
    if client:
        client.close()
        logging.info("🔌 MongoDB connection closed.")

async def add_new_user(user_id: int, full_name: str, username: str) -> bool:
    """Adds a new user to the database if they don't exist. Returns True if the user was new."""
    if users_collection is None: return False
    result = await users_collection.update_one(
        {"user_id": user_id},
        {"$setOnInsert": {
            "full_name": full_name, "username": username, "start_date": datetime.utcnow()
        }},
        upsert=True
    )
    if result.upserted_id:
        logging.info(f"New user {user_id} ({full_name}) started the bot.")
        return True
    return False

async def log_correct_answer(user_id: int, chat_id: int, username: str) -> None:
    """Logs a single correct answer event."""
    if quiz_logs_collection is None: return
    await quiz_logs_collection.insert_one({
        "user_id": user_id, "chat_id": chat_id, "username": username,
        "timestamp": datetime.utcnow()
    })
    logging.info(f"Logged correct answer for user {user_id} in chat {chat_id}.")

async def get_leaderboard(time_range: str = "all", chat_id: Optional[int] = None, limit: int = 10) -> List[dict]:
    """Generates any leaderboard view using an aggregation pipeline."""
    if quiz_logs_collection is None: return []
    pipeline = []
    match_filter = {}
    if time_range != "all":
        now = datetime.utcnow()
        if time_range == "today":
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_range == "week":
            start_time = now - timedelta(days=now.weekday())
            start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
        else: return []
        match_filter["timestamp"] = {"$gte": start_time}
    if chat_id:
        match_filter["chat_id"] = chat_id
    if match_filter:
        pipeline.append({"$match": match_filter})
    pipeline.extend([
        {"$group": {"_id": "$user_id", "username": {"$last": "$username"}, "score": {"$sum": 1}}},
        {"$sort": {"score": -1}},
        {"$limit": limit},
        {"$project": {"_id": 0, "user_id": "$_id", "username": "$username", "score": "$score"}}
    ])
    return await quiz_logs_collection.aggregate(pipeline).to_list(length=limit)

async def get_user_stats_in_chat(user_id: int, chat_id: int) -> Optional[Dict[str, Any]]:
    """Calculates a user's score and rank for a specific chat."""
    if quiz_logs_collection is None: return None
    pipeline = [{"$match": {"chat_id": chat_id, "user_id": user_id}}, {"$count": "score"}]
    result = await quiz_logs_collection.aggregate(pipeline).to_list(length=1)
    user_score = result[0]['score'] if result else 0
    if user_score == 0: return {"score": 0, "rank": "N/A"}
    pipeline = [
        {"$match": {"chat_id": chat_id}},
        {"$group": {"_id": "$user_id", "score": {"$sum": 1}}},
        {"$match": {"score": {"$gt": user_score}}},
        {"$count": "rank"}
    ]
    result = await quiz_logs_collection.aggregate(pipeline).to_list(length=1)
    higher_scores = result[0]['rank'] if result else 0
    return {"score": user_score, "rank": higher_scores + 1}

async def get_user_global_stats(user_id: int) -> Optional[Dict[str, Any]]:
    """Calculates a user's total score and rank across all chats."""
    if quiz_logs_collection is None: return None
    pipeline = [{"$match": {"user_id": user_id}}, {"$count": "score"}]
    result = await quiz_logs_collection.aggregate(pipeline).to_list(length=1)
    user_score = result[0]['score'] if result else 0
    if user_score == 0: return {"score": 0, "rank": "N/A"}
    pipeline = [
        {"$group": {"_id": "$user_id", "score": {"$sum": 1}}},
        {"$match": {"score": {"$gt": user_score}}},
        {"$count": "rank"}
    ]
    result = await quiz_logs_collection.aggregate(pipeline).to_list(length=1)
    higher_scores = result[0]['rank'] if result else 0
    return {"score": user_score, "rank": higher_scores + 1}

async def get_chat_settings(chat_id: int) -> ChatSettings:
    """Retrieves chat settings, handling old data schemas gracefully."""
    if chats_collection is None: return ChatSettings(chat_id=chat_id)
    settings_doc = await chats_collection.find_one({"chat_id": chat_id})
    if not settings_doc:
        default_settings = ChatSettings(chat_id=chat_id)
        settings_dict = {k: v for k, v in default_settings.__dict__.items() if k != '_id'}
        await chats_collection.insert_one(settings_dict)
        return default_settings
    if 'quiz_interval_hours' in settings_doc:
        del settings_doc['quiz_interval_hours']
    return ChatSettings(**settings_doc)

async def set_chat_active_status(chat_id: int, status: bool) -> None:
    """Updates a chat's scheduler status."""
    if chats_collection is None: return
    await chats_collection.update_one({"chat_id": chat_id}, {"$set": {"scheduler_enabled": status}}, upsert=True)
    logging.info(f"Set scheduler for chat {chat_id} to {status}.")

async def update_chat_interval(chat_id: int, interval_seconds: int) -> None:
    """Updates a chat's custom quiz interval."""
    if chats_collection is None: return
    await chats_collection.update_one({"chat_id": chat_id}, {"$set": {"quiz_interval_seconds": interval_seconds}}, upsert=True)
    logging.info(f"Updated quiz interval for chat {chat_id} to {interval_seconds}s.")

async def update_last_quiz_timestamp(chat_id: int, timestamp: Optional[datetime] = None) -> None:
    """Updates the timestamp of the last sent quiz for a chat."""
    if chats_collection is None: return
    if timestamp is None:
        timestamp = datetime.utcnow()
    await chats_collection.update_one({"chat_id": chat_id}, {"$set": {"last_quiz_timestamp": timestamp}}, upsert=True)

async def get_all_scheduled_chats() -> List[ChatSettings]:
    """Gets a list of all chats that have the scheduler enabled."""
    if chats_collection is None: return []
    cursor = chats_collection.find({"scheduler_enabled": True})
    settings_list = []
    async for doc in cursor:
        if 'quiz_interval_hours' in doc:
            del doc['quiz_interval_hours']
        settings_list.append(ChatSettings(**doc))
    return settings_list

async def get_total_chat_count() -> int:
    """Counts the total number of chats the bot has settings for."""
    if chats_collection is None: return 0
    return await chats_collection.count_documents({})

async def get_enabled_chat_count() -> int:
    """Counts the number of chats with the scheduler enabled."""
    if chats_collection is None: return 0
    return await chats_collection.count_documents({"scheduler_enabled": True})

async def get_total_unique_players() -> int:
    """Counts the number of unique users who have answered at least one quiz."""
    if quiz_logs_collection is None: return 0
    pipeline = [{"$group": {"_id": "$user_id"}}, {"$count": "unique_players"}]
    result = await quiz_logs_collection.aggregate(pipeline).to_list(length=1)
    return result[0]['unique_players'] if result else 0

async def get_total_users_started() -> int:
    """Counts the total number of users who have started the bot."""
    if users_collection is None: return 0
    return await users_collection.count_documents({})

async def get_all_chats() -> List[Dict[str, Any]]:
    """Retrieves all chats the bot is a part of."""
    if chats_collection is None: return []
    # We only need the chat_id for broadcasting
    cursor = chats_collection.find({}, {"chat_id": 1})
    return await cursor.to_list(length=None)

async def get_all_started_users() -> List[Dict[str, Any]]:
    """Retrieves all users who have started the bot."""
    if users_collection is None: return []
    cursor = users_collection.find({}, {"user_id": 1})
    return await cursor.to_list(length=None)

# =========================
