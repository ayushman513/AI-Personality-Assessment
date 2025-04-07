import { useState } from 'react';
import { Question } from '../types';

interface Props {
  question: Question;
  answer: string;
  onAnswerChange: (answer: string) => void;
  onSubmit: () => void;
}

export function AssessmentQuestion({
  question,
  answer,
  onAnswerChange,
  onSubmit
}: Props) {
  const [questionCounter, setQuestionCounter] = useState(1);
  const [isLoading, setIsLoading] = useState(false);

  const isLastQuestion = questionCounter === 10;

  const handleSubmit = () => {
    if (isLastQuestion) {
      setIsLoading(true);
      onSubmit(); // Do not reset loading; show "Processing..." permanently
    } else {
      setQuestionCounter((prev) => prev + 1);
      onSubmit();
    }
  };

  const isButtonDisabled = isLoading || answer.trim() === '';

  return (
    <div className="w-full max-w-2xl mx-auto p-6 bg-white rounded-xl shadow-lg">
      <h2 className="text-2xl font-semibold text-gray-800 mb-6">{question.text}</h2>
      <div className="space-y-4">
        <textarea
          value={answer}
          onChange={(e) => onAnswerChange(e.target.value)}
          className="w-full h-32 p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="Type your answer here..."
        />
        <button
          onClick={handleSubmit}
          disabled={isButtonDisabled}
          className={`w-full py-3 px-6 rounded-lg text-white transition-colors ${
            isButtonDisabled
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          {isLoading
            ? 'Analyzing your responses to uncover deep personality insights......'
            : isLastQuestion
            ? 'Complete Assessment'
            : 'Next Question'}
        </button>
      </div>
    </div>
  );
}
