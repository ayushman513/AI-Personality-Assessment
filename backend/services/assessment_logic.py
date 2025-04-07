import logging
import uuid
from typing import List, Dict, Optional
from config import QUESTION_POOL
from models import Question, Answer, PersonalityProfile, TraitScore
# Updated imports: use the new function names
from services.openrouter_service import (
    get_next_question_from_pool, # Changed function
    analyze_responses_for_profile,
    generate_profile_summary,
)

logger = logging.getLogger(__name__)

# --- In-Memory Storage (Placeholder - NOT PRODUCTION READY) ---
# WARNING: Data stored in these dictionaries will be lost on server restart.
# Replace with a persistent database solution (SQL, NoSQL) for production.
assessments_db: Dict[str, Dict] = {}
profiles_db: Dict[str, PersonalityProfile] = {}
logger.warning("Using in-memory dictionaries for data storage. Data will NOT persist across server restarts. Replace with a database for production.")
# --- Service Functions ---

async def start_new_assessment(candidate_id: str, config: Optional[dict] = None) -> (str | Optional[Question]):
    """Starts a new assessment, gets the first question from the pool."""
    assessment_id = str(uuid.uuid4())
    logger.info(f"Starting assessment {assessment_id} for candidate {candidate_id}")

    # Get first question from the pool (no asked questions yet)
    first_question = get_next_question_from_pool(asked_question_ids=[])

    if not first_question:
        logger.error("Failed to get the first question from the pool. Pool might be empty.")
        # Cannot start assessment without questions
        return assessment_id, None # Indicate failure to start

    assessments_db[assessment_id] = {
        "candidate_id": candidate_id,
        "status": "In Progress",
        "questions": [first_question], # Store the actual Question objects
        "answers": [],
        "config": config or {},
        "asked_question_ids": [first_question.id] # Track IDs asked
    }
    logger.info(f"Assessment {assessment_id} created in DB. First question ID: {first_question.id}")
    return assessment_id, first_question

async def get_next_assessment_question(assessment_id: str, last_answer: Optional[Answer]) -> Optional[Question]:
    """Gets the next question from the pool, avoiding repetition."""
    assessment_data = assessments_db.get(assessment_id)
    if not assessment_data or assessment_data["status"] != "In Progress":
        logger.warning(f"Cannot get next question: Assessment {assessment_id} not found or not 'In Progress'. Status: {assessment_data.get('status') if assessment_data else 'Not Found'}")
        return None

    # Store the last answer if provided
    if last_answer:
        if assessment_data["questions"] and last_answer.question_id == assessment_data["questions"][-1].id:
            assessment_data["answers"].append(last_answer)
            logger.info(f"Stored answer for question {last_answer.question_id} in assessment {assessment_id}")
        else:
            # Log clearly but don't block getting next question maybe? Or return error? Let's log.
            logger.warning(f"Received answer for non-matching question ID ({last_answer.question_id}) in assessment {assessment_id}. Ignoring answer storage.")

    # Determine if assessment should end (e.g., fixed number of questions from pool)
    MAX_QUESTIONS = len(QUESTION_POOL) 
    asked_ids = assessment_data["asked_question_ids"]

    if len(asked_ids) >= MAX_QUESTIONS:
        logger.info(f"Assessment {assessment_id} reached max questions ({MAX_QUESTIONS}). Ending assessment.")
        assessment_data["status"] = "Pending Analysis" # Ready for analysis
        return None # Signal assessment end

    # Get the next unique question from the pool
    next_question = get_next_question_from_pool(asked_question_ids=asked_ids)

    if not next_question:
        logger.info(f"No more unique questions in pool for assessment {assessment_id}. Ending assessment.")
        assessment_data["status"] = "Pending Analysis" # Ready for analysis
        return None # Signal assessment end (ran out of questions)

    # Store the new question and its ID
    assessment_data["questions"].append(next_question)
    assessment_data["asked_question_ids"].append(next_question.id)
    logger.info(f"Added next question {next_question.id} to assessment {assessment_id}")
    return next_question

async def process_assessment_analysis(assessment_id: str) -> Optional[PersonalityProfile]:
    """Triggers the analysis of responses and generates the profile using OpenRouter."""
    assessment_data = assessments_db.get(assessment_id)

    # Check status more precisely
    if not assessment_data:
         logger.error(f"Cannot analyze: Assessment {assessment_id} not found.")
         return None
    if assessment_data["status"] not in ["Pending Analysis", "In Progress"]: # Allow analysis even if in progress? Maybe only Pending Analysis.
        logger.warning(f"Cannot analyze: Assessment {assessment_id} has status '{assessment_data['status']}'. Requires 'Pending Analysis'.")
        # If ending implicitly in get_next_question, status should be Pending Analysis.
        # If called manually, ensure assessment is ready.
        if assessment_data["status"] == "Completed": # Already done?
             logger.info(f"Analysis already completed for {assessment_id}. Retrieving stored profile.")
             return profiles_db.get(assessment_data["candidate_id"])
        return None

    candidate_id = assessment_data["candidate_id"]
    # Ensure Answer and Question objects are correctly typed if loaded from DB later
    answers: List[Answer] = assessment_data.get("answers", [])
    questions: List[Question] = assessment_data.get("questions", [])

    if not answers:
        logger.error(f"Cannot analyze assessment {assessment_id}: No answers found.")
        # Update status to reflect failure?
        assessment_data["status"] = "Analysis Failed (No Answers)"
        return None

    logger.info(f"Starting analysis process for assessment {assessment_id} (Candidate: {candidate_id})")

    # Call the updated OpenRouter service function
    trait_scores = await analyze_responses_for_profile(candidate_id, answers, questions) # Pass questions for context

    if trait_scores is None: # Handles errors within analyze_responses_for_profile
        logger.error(f"Analysis failed to produce trait scores for {assessment_id}.")
        assessment_data["status"] = "Analysis Failed (LLM Error)"
        return None

    # Generate summary
    summary = await generate_profile_summary(trait_scores)

    # Create and store the profile
    profile = PersonalityProfile(
        candidate_id=candidate_id,
        model_type="BigFive",
        traits=trait_scores,
        summary=summary
    )
    profiles_db[candidate_id] = profile # Store profile
    assessment_data["status"] = "Completed" # Mark assessment as completed

    logger.info(f"Analysis complete for {assessment_id}. Profile stored for candidate {candidate_id}.")
    return profile


# --- Other functions (get_candidate_profile, analytics) remain largely the same ---
# --- but rely on the NON-PERSISTENT profiles_db and assessments_db ---

async def get_candidate_profile(candidate_id: str) -> Optional[PersonalityProfile]:
    """Retrieves the generated personality profile for a candidate."""
    logger.info(f"Retrieving profile for candidate {candidate_id}")
    profile = profiles_db.get(candidate_id)
    if not profile:
        logger.warning(f"Profile not found for candidate {candidate_id}")
    return profile

async def get_all_candidate_summaries() -> List[dict]:
    """Placeholder: Retrieves summary data for all candidates."""
    summaries = []
    logger.debug(f"Retrieving summaries. Current assessments: {len(assessments_db)}, Current profiles: {len(profiles_db)}")
    # Enhanced example referencing stored data
    processed_candidates = set()
    for assessment_id, data in assessments_db.items():
        candidate_id = data["candidate_id"]
        if candidate_id in processed_candidates: continue # Avoid duplicates if multiple assessments per candidate

        profile = profiles_db.get(candidate_id)
        summary_data = {
             "candidate_id": candidate_id,
             "assessment_id": assessment_id, # Include last known assessment ID
             "assessment_status": data["status"],
             "profile_available": profile is not None,
             # Add more summary fields if needed from profile
             "summary_text": profile.summary if profile else None
         }
        summaries.append(summary_data)
        processed_candidates.add(candidate_id)

    # Add candidates who might only exist in profile_db (e.g., if assessment data was cleared/lost)
    for candidate_id, profile in profiles_db.items():
         if candidate_id not in processed_candidates:
              summaries.append({
                   "candidate_id": candidate_id,
                   "assessment_id": None,
                   "assessment_status": "Completed (Assessment data missing)",
                   "profile_available": True,
                   "summary_text": profile.summary
              })
              processed_candidates.add(candidate_id) # Should already be added, but safe

    logger.info(f"Retrieved {len(summaries)} candidate summaries.")
    return summaries


async def compare_candidates_logic(candidate_ids: List[str], traits: Optional[List[str]] = None) -> dict:
    """Generates comparison data for selected candidates."""
    comparison_data = {}
    logger.info(f"Comparing candidates: {candidate_ids}. Specific traits: {traits or 'All'}")
    for candidate_id in candidate_ids:
        profile = profiles_db.get(candidate_id)
        if profile:
            scores_to_show = {
                ts.trait: ts.score
                for ts in profile.traits
                if not traits or ts.trait in traits
            }
            comparison_data[candidate_id] = {
                "summary": profile.summary,
                "scores": scores_to_show
            }
        else:
            logger.warning(f"Profile not found during comparison for candidate {candidate_id}")
            comparison_data[candidate_id] = None
    return {"comparison": comparison_data}


async def get_trends_logic() -> dict:
    """Generates trend data."""
    logger.info("Calculating personality trends.")
    if not profiles_db:
        logger.info("No profiles available to calculate trends.")
        return {"total_profiles_analyzed": 0, "average_scores_per_trait": {}}

    trait_totals: Dict[str, float] = {}
    trait_counts: Dict[str, int] = {}
    profile_count = 0

    for profile in profiles_db.values():
        profile_count += 1
        for trait_score in profile.traits:
            trait = trait_score.trait
            trait_totals[trait] = trait_totals.get(trait, 0) + trait_score.score
            trait_counts[trait] = trait_counts.get(trait, 0) + 1

    average_scores = {
        trait: round(trait_totals[trait] / trait_counts[trait], 1)
        for trait in trait_totals
        if trait_counts.get(trait, 0) > 0 # Check count exists and > 0
    }

    logger.info(f"Trend calculation complete. Analyzed {profile_count} profiles.")
    return {
        "total_profiles_analyzed": profile_count,
        "average_scores_per_trait": average_scores
        }