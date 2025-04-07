from pydantic import BaseModel, Field
from typing import List, Optional

# --- Data Models ---

class TraitScore(BaseModel):
    trait: str = Field(..., description="Name of the personality trait (e.g., Openness)")
    score: int = Field(..., ge=0, le=100, description="Score for the trait (0-100)")
    insights: Optional[str] = Field(None, description="Brief explanation or insight about the score")

class PersonalityProfile(BaseModel):
    candidate_id: str
    model_type: str = Field("BigFive", description="Personality model used (e.g., BigFive, MBTI)")
    traits: List[TraitScore] = Field(..., description="List of trait scores for the candidate")
    summary: Optional[str] = Field(None, description="Overall summary of the personality profile")

class Question(BaseModel):
    id: str # Use string IDs for flexibility (e.g., UUID)
    text: str
    targeted_trait: Optional[str] = None # Which trait this question primarily aims to assess

# class Answer(BaseModel):
#     question_id: str
#     response_text: str
class Answer(BaseModel):
    question_id: str
    response: str
    targeted_trait: str
# --- Request/Response Models ---

class AssessmentStartRequest(BaseModel):
    candidate_id: str
    assessment_config: Optional[dict] = Field(None, description="Optional config, e.g., target role")

class AssessmentStartResponse(BaseModel):
    assessment_id: str
    first_question: Question

class NextQuestionRequest(BaseModel):
    assessment_id: str
    last_answer: Optional[Answer] = Field(None, description="The answer to the previous question, used for adaptive questioning")

class SubmitAssessmentRequest(BaseModel):
    assessment_id: str
    answers: List[Answer] # Or maybe submit answers one by one via NextQuestionRequest? Let's keep batch for now.

class AnalysisTriggerRequest(BaseModel):
    assessment_id: str

# Models for Analytics (Simplified Examples)
class CandidateSummary(BaseModel):
    candidate_id: str
    assessment_status: str # e.g., "Not Started", "In Progress", "Completed"
    overall_score: Optional[float] = None # Example summary metric

class CandidateComparisonRequest(BaseModel):
    candidate_ids: List[str]
    comparison_traits: Optional[List[str]] = None # Specific traits to compare

class CandidateComparisonResponse(BaseModel):
    comparison_data: dict # Structure depends on how you want to compare

class TrendDataResponse(BaseModel):
    trend_info: dict # e.g., average scores per trait across candidates