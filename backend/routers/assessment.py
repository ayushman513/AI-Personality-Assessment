import logging
from fastapi import APIRouter, HTTPException, Depends, Body, status
from typing import List, Optional
from models import (
    Question, Answer, AssessmentStartRequest, AssessmentStartResponse,
    NextQuestionRequest, AnalysisTriggerRequest, PersonalityProfile
)
from services import assessment_logic

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/assessments",
    tags=["Assessments"]
)

@router.post("/start", response_model=AssessmentStartResponse, status_code=status.HTTP_201_CREATED)
async def start_assessment(request: AssessmentStartRequest):
    """
    Initiates a new personality assessment for a candidate and returns the first question.
    """
    assessment_id, first_question = await assessment_logic.start_new_assessment(
        candidate_id=request.candidate_id,
        config=request.assessment_config
    )
    # Check if first_question is None (indicates failure, e.g., empty pool)
    if first_question is None:
        logger.error(f"Failed to start assessment for candidate {request.candidate_id}. No initial question.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve the first assessment question. The question pool might be empty or misconfigured."
        )
    logger.info(f"Assessment {assessment_id} started for candidate {request.candidate_id}.")
    return AssessmentStartResponse(assessment_id=assessment_id, first_question=first_question)


@router.post("/next_question", response_model=Optional[Question])
async def get_next_question(request: NextQuestionRequest):
    """
    Submits the answer to the previous question (if provided) and retrieves the next dynamic question
    from the pool for the ongoing assessment. Returns null when the assessment is complete.
    """
    logger.debug(f"Received request for next question for assessment {request.assessment_id}.")
    next_question = await assessment_logic.get_next_assessment_question(
        assessment_id=request.assessment_id,
        last_answer=request.last_answer
    )
    if next_question:
        logger.info(f"Returning next question {next_question.id} for assessment {request.assessment_id}.")
    else:
         # This is expected when assessment ends normally
         logger.info(f"No more questions for assessment {request.assessment_id}. Assessment likely ended.")
    return next_question


@router.post("/analyze", response_model=PersonalityProfile, status_code=status.HTTP_200_OK)
async def trigger_analysis(request: AnalysisTriggerRequest):
    """
    Triggers the analysis of an assessment using submitted answers and returns the generated profile.
    The assessment status should typically be 'Pending Analysis'.
    """
    logger.info(f"Received request to analyze assessment {request.assessment_id}")
    profile = await assessment_logic.process_assessment_analysis(request.assessment_id)

    if profile is None:
        logger.error(f"Analysis failed or returned no profile for assessment {request.assessment_id}.")
        # Provide a more informative error based on potential underlying issues
        assessment_data = assessment_logic.assessments_db.get(request.assessment_id)
        status_code = status.HTTP_400_BAD_REQUEST # Default to Bad Request
        detail = f"Failed to analyze assessment {request.assessment_id}."

        if not assessment_data:
             status_code = status.HTTP_404_NOT_FOUND
             detail = f"Assessment {request.assessment_id} not found."
        elif assessment_data.get("status") == "Analysis Failed (No Answers)":
             detail = f"Analysis failed: No answers found for assessment {request.assessment_id}."
        elif assessment_data.get("status") == "Analysis Failed (LLM Error)":
             status_code = status.HTTP_503_SERVICE_UNAVAILABLE # Indicate backend/LLM issue
             detail = f"Analysis failed due to an issue contacting or interpreting the language model for assessment {request.assessment_id}."
        elif assessment_data.get("status") not in ["Pending Analysis", "In Progress"]: # Check if status prevents analysis
             detail = f"Cannot analyze assessment {request.assessment_id} with current status '{assessment_data['status']}'. Requires 'Pending Analysis'."

        raise HTTPException(status_code=status_code, detail=detail)

    logger.info(f"Analysis successful for assessment {request.assessment_id}. Returning profile.")
    return profile