import { AssessmentResult } from '../types';
import { BarChart, Home } from 'lucide-react';
import { marked } from 'marked';

interface Props {
  result: AssessmentResult;
  onReturnHome: () => void;
}

export function ResultsDashboard({ result, onReturnHome }: Props) {
  return (
    <div className="w-full flex justify-center bg-gray-50 mt-6 px-4 overflow-hidden">
      <div className="w-full max-w-5xl p-4 bg-white rounded-xl shadow-lg">
        <div className="flex items-center gap-3 mb-4">
          <BarChart className="w-6 h-6 text-blue-600" />
          <h1 className="text-xl font-bold text-gray-900">Your Personality Assessment Results</h1>
        </div>

        <div className="mb-4">
          <h2 className="text-lg font-semibold text-gray-800 mb-2">Personality Traits</h2>
          <div className="grid grid-cols-2 gap-3 max-h-[40vh] overflow-y-auto pr-1">
            {result.traits.map((trait) => (
              <div key={trait.trait} className="p-3 bg-gray-50 rounded-md text-sm">
                <div className="flex justify-between items-center mb-1">
                  <span className="font-medium text-gray-800">{trait.trait}</span>
                  <span className="font-bold text-blue-600">{trait.score}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full"
                    style={{ width: `${trait.score}%` }}
                  />
                </div>
                <p className="text-gray-600 text-xs leading-tight">{trait.description}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-gray-50 p-3 rounded-md mb-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-2">Summary</h2>
          <div
            className="text-gray-700 text-sm leading-snug"
            dangerouslySetInnerHTML={{ __html: marked(result.summary) }}
          />
        </div>

        {/* Return to Home button */}
        <div className="flex justify-center">
          <button
            onClick={onReturnHome}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200"
          >
            <Home className="w-4 h-4 mr-2" />
            Return to Home
          </button>
        </div>
      </div>
    </div>
  );
}
