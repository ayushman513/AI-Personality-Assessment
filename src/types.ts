// export interface Question {
//   id: string;
//   text: string;
//   trait: string;
//   category?: string; // Keeping this for backward compatibility
// }

// export interface Answer {
//   questionId: string;
//   response: string;
// }

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

export interface AssessmentResult {
  traits: {
    trait: string;
    score: number;
    description: string;
    insights : string;
  }[];
  summary: string;
}