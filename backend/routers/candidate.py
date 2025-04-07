from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional
from models import PersonalityProfile
from services import assessment_logic # Import the logic service

router = APIRouter(
    prefix="/candidates",
    tags=["Candidates"]
)

@router.get("/{candidate_id}/profile", response_model=PersonalityProfile)
async def get_profile(candidate_id: str):
    """
    Retrieves the generated personality profile for a specific candidate.
    """
    profile = await assessment_logic.get_candidate_profile(candidate_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Personality profile not found for candidate {candidate_id}")
    return profile