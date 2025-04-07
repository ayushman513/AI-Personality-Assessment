// api.ts

const API_BASE_URL = 'http://localhost:5000';

// Define the structure of an answer sent to the backend
export interface Answer {
  question_id: string;
  response: string;
  targeted_trait: string;
}

// Define the structure of a question returned by the backend
export interface Question {
  id: string;
  text: string;
  targeted_trait: string;
}

// Start a new assessment for a given candidate
export async function startAssessment(candidateId: string) {
  const response = await fetch(`${API_BASE_URL}/assessments/start`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      candidate_id: candidateId,
    }),
  });

  if (!response.ok) {
    throw new Error('Failed to start assessment');
  }

  return response.json();
}

// Get the next question in the assessment flow
export async function getNextQuestion(
    assessmentId: string,
    lastAnswer: Answer // now required
  ): Promise<Question> {
    const payload = {
      assessment_id: assessmentId,
      last_answer: {
        question_id: lastAnswer.question_id,
        response: lastAnswer.response,
        targeted_trait: lastAnswer.targeted_trait,
      },
    };

  const response = await fetch(`${API_BASE_URL}/assessments/next_question`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error('Failed to get next question');
  }

  return response.json();
}

// Trigger analysis of the completed assessment
export async function triggerAnalysis(assessmentId: string) {
  const response = await fetch(`${API_BASE_URL}/assessments/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      assessment_id: assessmentId,
    }),
  });

  if (!response.ok) {
    throw new Error('Failed to analyze assessment');
  }

  return response.json();
}
