# =========================
# Created by git @karmaxexclusive
# =========================

from dataclasses import dataclass, field
from typing import Optional, Any
from datetime import datetime

@dataclass
class UserStats:
    """Represents a user's statistics within a specific chat."""
    user_id: int
    chat_id: int
    username: str
    score: int = 0
    _id: Optional[Any] = None

@dataclass
class ChatSettings:
    """Represents the settings for a specific chat."""
    chat_id: int
    scheduler_enabled: bool = True
    quiz_interval_seconds: int = 3600  # Default to 1 hour (3600s)
    last_quiz_timestamp: datetime = field(default_factory=datetime.utcnow)
    _id: Optional[Any] = None

# =========================
