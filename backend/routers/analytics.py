from fastapi import APIRouter, HTTPException, Depends, Body, status
from typing import List, Optional
from models import (
    CandidateSummary, CandidateComparisonRequest, CandidateComparisonResponse,
    TrendDataResponse
)
from services import assessment_logic # Import the logic service

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics (Recruiter/HR)"]
    # Consider adding security dependencies here later: dependencies=[Depends(get_current_hr_user)]
)

@router.get("/candidates", response_model=List[CandidateSummary])
async def get_candidate_list_summary():
    """
    Retrieves a summary list of all candidates and their assessment status.
    (Requires authentication/authorization in a real system)
    """
    summaries = await assessment_logic.get_all_candidate_summaries()
    return summaries

@router.post("/compare", response_model=CandidateComparisonResponse)
async def compare_candidates(request: CandidateComparisonRequest):
    """
    Provides data for comparing selected candidates based on their profiles.
    (Requires authentication/authorization)
    """
    comparison_data = await assessment_logic.compare_candidates_logic(
        candidate_ids=request.candidate_ids,
        traits=request.comparison_traits
        )
    return CandidateComparisonResponse(comparison_data=comparison_data)


@router.get("/trends", response_model=TrendDataResponse)
async def get_personality_trends():
    """
    Retrieves aggregated trend data from completed personality assessments.
    (Requires authentication/authorization)
    """
    trend_data = await assessment_logic.get_trends_logic()
    return TrendDataResponse(trend_info=trend_data)

# Note: We might want another endpoint like GET /analytics/candidates/{candidate_id}/details
# which could potentially return the same PersonalityProfile as the candidate view,
# or maybe a slightly augmented version for HR. For now, assume HR uses the main profile endpoint.