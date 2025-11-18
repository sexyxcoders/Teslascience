# =========================
# Created by git @karmaxexclusive
# =========================

import json
import logging
from typing import List, Dict, Any

# Define the path to your quiz file
QUIZ_FILE_PATH = "TeslaQuiz/data/quizs.json"

def load_quizzes() -> List[Dict[str, Any]]:
    """Loads quizzes from the JSON file."""
    try:
        # We use 'utf-8' encoding to support a wide range of characters
        with open(QUIZ_FILE_PATH, "r", encoding="utf-8") as file:
            quizzes = json.load(file)
        logging.info(f"Successfully loaded {len(quizzes)} quizzes.")
        return quizzes
    except FileNotFoundError:
        logging.error(f"Quiz file not found at: {QUIZ_FILE_PATH}")
        return []
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from the quiz file. Please check its format.")
        return []

# Load the quizzes once when the bot starts up.
# This list will be imported by other parts of the bot.
QUIZZES = load_quizzes()

# =========================
