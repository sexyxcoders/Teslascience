# =========================
# Created by git @karmaxexclusive
# =========================

import os
from dotenv import load_dotenv
load_dotenv()


BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
SCHEDULER_INTERVAL_SECONDS = int(60)
OWNER_ID = int(os.getenv("OWNER_ID", 0)) 
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", 0))

if not MONGO_URI:
    raise ValueError("MONGO_URI not found in .env file! Please add it.")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in .env file! Please add it.")
if not OWNER_ID:
    raise ValueError("OWNER_ID not found in .env file! Please add it.")
if not LOG_CHANNEL_ID:
    raise ValueError("LOG_CHANNEL_ID not found in .env file! Please add it.")

# =========================
