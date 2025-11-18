# =========================
# Created by git @karmaxexclusive
# =========================

import requests
import json
import logging
import time
import random

# --- Configuration ---
GEMINI_API_URL = "https://gemini-2flash-lite.eternalowner06.workers.dev/"
OUTPUT_FILE = "high_quality_question_bank.json"
QUESTIONS_PER_TOPIC = 100  # The target number of questions for each topic
BATCH_SIZE = 10           # Reduced batch size for higher quality per request

# A more specific list of grammar topics to ensure better focus
GRAMMAR_TOPICS = [
    "Subject-Verb Agreement with interrupting phrases", "Verb Tenses (Perfect vs. Simple Past)", "Pronoun-Antecedent Agreement",
    "Adjectives vs. Adverbs", "Sentence Structure (Fragments and Run-ons)", "Punctuation (Commas, Semicolons, Colons)",
    "Prepositions of Time and Place", "Coordinating vs. Subordinating Conjunctions", "Articles (a, an, the)", 
    "Commonly Confused Words (e.g., affect/effect, lay/lie)", "Active and Passive Voice", "Reported Speech", 
    "Conditional Sentences (Type 1, 2, and 3)", "Modal Verbs (can, could, may, might)"
]

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_questions_from_gemini(topic: str):
    """
    Calls the Gemini API with a rigorous, high-accuracy prompt.
    """
    # This new prompt is much more demanding to ensure factual correctness.
    prompt = f"""
    Act as a meticulous English grammar professor creating questions for a university entrance exam. Absolute accuracy is the highest priority.

    For the topic of "{topic}", generate exactly {BATCH_SIZE} multiple-choice questions.

    For each question, follow this rigorous process:
    1.  Formulate a clear question that tests a specific rule within the topic.
    2.  Create four options: one that is unequivocally correct and three plausible but definitively incorrect distractors.
    3.  Verify the correct answer against established grammar rules.
    4.  Write a clear, concise explanation that cites the specific grammar rule justifying the correct answer.

    The final output MUST be a single, valid JSON object with a root key "questions". Each object in the list must have keys: "question_text", "options", "correct_answer", "explanation", and "difficulty" (easy, medium, or hard).

    Crucial Instruction: Before finalizing the JSON, review every single question one last time to ensure the 'correct_answer' and 'explanation' are 100% factually accurate. An incorrect question is a failed task.
    """
    
    logging.info(f"Requesting a high-quality batch of {BATCH_SIZE} questions for topic: {topic}")
    try:
        response = requests.get(GEMINI_API_URL, params={'prompt': prompt}, timeout=90)
        response.raise_for_status()
        response_data = response.json()
        json_string = response_data.get("Response", "{}")
        
        if json_string.strip().startswith("```json"):
            json_string = json_string.strip()[7:-3]
            
        return json.loads(json_string)

    except requests.exceptions.RequestException as e:
        logging.error(f"API request failed for topic '{topic}': {e}")
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON for topic '{topic}': {e}")
        logging.error(f"Raw response was: {response.text}")
    return None

def reformat_for_quiz_app(generated_data: dict, start_id: int):
    reformatted_questions = []
    if not generated_data or "questions" not in generated_data:
        return [], 0

    processed_texts = set()
    for item in generated_data["questions"]:
        try:
            q_text = item["question_text"]
            if q_text in processed_texts: continue
            
            options = item["options"]
            correct_answer_text = item["correct_answer"]
            correct_answer_index = options.index(correct_answer_text)

            formatted_question = {
                "id": f"Q-GEM-{start_id:04d}",
                "question": q_text,
                "options": options,
                "correct_answer": correct_answer_index,
                "difficulty": item.get("difficulty", "medium").lower(),
                "category": "English",
                "answer": item.get("explanation", ""),
                "type": "multiple",
                "source": "Gemini-Generated"
            }
            reformatted_questions.append(formatted_question)
            processed_texts.add(q_text)
            start_id += 1
        except (ValueError, KeyError, TypeError) as e:
            logging.warning(f"Could not process an item: {e}")
    
    return reformatted_questions, start_id

if __name__ == "__main__":
    all_questions = []
    unique_question_texts = set()
    current_question_id = 1
    num_batches = QUESTIONS_PER_TOPIC // BATCH_SIZE
    
    for topic in GRAMMAR_TOPICS:
        logging.info(f"--- Starting Topic: {topic} ---")
        for i in range(num_batches):
            gemini_output = generate_questions_from_gemini(topic)
            if gemini_output:
                formatted_batch, new_id = reformat_for_quiz_app(gemini_output, current_question_id)
                for q in formatted_batch:
                    if q["question"] not in unique_question_texts:
                        all_questions.append(q)
                        unique_question_texts.add(q["question"])
                current_question_id = new_id
            time.sleep(5)  # Pause between batches to be respectful to the API

    if all_questions:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_questions, f, indent=2)
        logging.info(f"--- PROCESS COMPLETE ---")
        logging.info(f"Successfully saved {len(all_questions)} unique questions to '{OUTPUT_FILE}'")
    else:
        logging.warning("PROCESS FAILED: No questions were generated.")

# =========================
