import os
import json
import logging
from dotenv import load_dotenv
from typing import List, Dict, Optional

# Basic logging setup for config loading issues
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

class Settings:
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL_ANALYSIS: str = os.getenv("OPENROUTER_MODEL_ANALYSIS", "google/gemini-flash-1.5")
    # Path to a JSON file containing questions (optional)
    QUESTION_POOL_PATH: Optional[str] = os.getenv("QUESTION_POOL_PATH", None)

settings = Settings()

# Validate critical settings
if not settings.OPENROUTER_API_KEY:
    logger.warning("CRITICAL: OPENROUTER_API_KEY not found in .env file. LLM analysis will fail.")
else:
     # Optional: Mask parts of the key in logs if needed for security
    masked_key = settings.OPENROUTER_API_KEY[:4] + "****" + settings.OPENROUTER_API_KEY[-4:]
    logger.info(f"OpenRouter API Key loaded (masked): {masked_key}")

logger.info(f"Using OpenRouter Analysis Model: {settings.OPENROUTER_MODEL_ANALYSIS}")


# --- Load Question Pool ---
# For simplicity now, define it here. Ideally, load from settings.QUESTION_POOL_PATH
DEFAULT_QUESTION_POOL: List[Dict[str, str]] = [
    {"id": "q_001", "text": "Describe a time you had to work with a difficult colleague. How did you handle the situation and what was the outcome?", "trait": "Agreeableness"},
    {"id": "q_002", "text": "Tell me about a situation where you took initiative to solve a problem that wasn't explicitly assigned to you.", "trait": "Conscientiousness"},
    {"id": "q_003", "text": "Describe a project or accomplishment you are particularly proud of. What was your specific role and contribution?", "trait": "Extraversion/Conscientiousness"},
    {"id": "q_004", "text": "How do you typically handle working under pressure or with tight deadlines? Give an example.", "trait": "Neuroticism"},
    {"id": "q_005", "text": "Tell me about a time you had to learn something completely new to complete a task or project. How did you approach it?", "trait": "Openness"},
    {"id": "q_006", "text": "Describe a situation where you had to persuade others to see things your way. What was your approach?", "trait": "Extraversion"},
    {"id": "q_007", "text": "Give an example of a time you received constructive criticism. How did you react, and what did you do with the feedback?", "trait": "Agreeableness/Openness"},
    {"id": "q_008", "text": "How do you prioritize your tasks when you have multiple competing deadlines?", "trait": "Conscientiousness"},
    {"id": "q_009", "text": "Describe a time you worked effectively as part of a team to achieve a common goal.", "trait": "Agreeableness/Extraversion"},
    {"id": "q_010", "text": "Tell me about a time you faced unexpected challenges in a project. How did you adapt?", "trait": "Openness/Neuroticism"}
]

def load_questions() -> List[Dict[str, str]]:
    """Loads question pool from JSON file or uses default."""
    if settings.QUESTION_POOL_PATH:
        try:
            with open(settings.QUESTION_POOL_PATH, 'r') as f:
                questions = json.load(f)
            logger.info(f"Loaded {len(questions)} questions from {settings.QUESTION_POOL_PATH}")
            # Basic validation could be added here (e.g., check for 'id', 'text')
            return questions
        except Exception as e:
            logger.error(f"Failed to load questions from {settings.QUESTION_POOL_PATH}: {e}. Using default pool.")
            return DEFAULT_QUESTION_POOL
    else:
        logger.info("Using default question pool defined in config.py")
        return DEFAULT_QUESTION_POOL

QUESTION_POOL = load_questions()