import { useState, useEffect } from 'react';
import { Question, Answer, AssessmentResult } from './types';
import { AssessmentQuestion } from './components/AssessmentQuestion';
import { ResultsDashboard } from './components/ResultsDashboard';
import { LandingPage } from './components/LandingPage';
import { Brain } from 'lucide-react';
import * as api from './api.ts';
import { generateCandidateId } from './utils/candidateId';

function App() {
  const [assessmentId, setAssessmentId] = useState<string | null>(null);
  const [candidateId, setCandidateId] = useState<string | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null);
  const [currentAnswer, setCurrentAnswer] = useState('');
  const [isComplete, setIsComplete] = useState(false);
  const [result, setResult] = useState<AssessmentResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [hasStarted, setHasStarted] = useState(false);

  useEffect(() => {
    if (hasStarted) {
      startNewAssessment();
    }
  }, [hasStarted]);

  const startNewAssessment = async () => {
    try {
      setLoading(true);
      setError(null);

      const newCandidateId = generateCandidateId();
      setCandidateId(newCandidateId);

      const response = await api.startAssessment(newCandidateId);
      setAssessmentId(response.assessment_id);
      setCurrentQuestion(response.first_question);
    } catch (err) {
      setError('Failed to start assessment. Please try again.');
      console.error('Error starting assessment:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerSubmit = async () => {
    if (!currentAnswer.trim() || !assessmentId || !currentQuestion) return;

    try {
      setLoading(true);
      setError(null);

      const answer: Answer = {
        question_id: currentQuestion.id,
        response: currentAnswer.trim(),
        targeted_trait: currentQuestion.targeted_trait,
      };

      const nextQuestion = await api.getNextQuestion(assessmentId, answer);

      if (nextQuestion) {
        setCurrentQuestion(nextQuestion);
        setCurrentAnswer('');
      } else {
        const analysisResult = await api.triggerAnalysis(assessmentId);
        setResult(analysisResult);
        setIsComplete(true);
      }
    } catch (err) {
      setError('Failed to submit answer. Please try again.');
      console.error('Error submitting answer:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRestart = () => {
    setAssessmentId(null);
    setCandidateId(null);
    setCurrentQuestion(null);
    setCurrentAnswer('');
    setIsComplete(false);
    setResult(null);
    setError(null);
    setLoading(false);
    setHasStarted(false);
  };

  if (!hasStarted) {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
            <div className="flex items-center gap-3">
              <Brain className="w-8 h-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">AI Personality Assessment</h1>
            </div>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
          <LandingPage onStart={() => setHasStarted(true)} />
        </main>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-md text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={handleRestart}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Back to Home
          </button>
        </div>
      </div>
    );
  }

  if (loading && !currentQuestion && !isComplete) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Brain className="w-8 h-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">AI Personality Assessment</h1>
            </div>
            {candidateId && (
              <div className="text-sm text-gray-600">ID: {candidateId}</div>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {!isComplete && currentQuestion ? (
          <div className="space-y-8">
            <AssessmentQuestion
              question={currentQuestion}
              answer={currentAnswer}
              onAnswerChange={setCurrentAnswer}
              onSubmit={handleAnswerSubmit}
            />
          </div>
        ) : result ? (
          <ResultsDashboard result={result} onReturnHome={handleRestart} />
        ) : null}
      </main>
    </div>
  );
}

export default App;
