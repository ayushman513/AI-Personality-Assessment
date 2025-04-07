import { ChevronRight, Clock, FileText, Target } from 'lucide-react';

interface Props {
  onStart: () => void;
}

export function LandingPage({ onStart }: Props) {
  return (
    <div className="h-full flex items-center">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Discover Your Personality Traits
          </h1>
          <p className="text-xl text-gray-600">
            Take our AI-powered assessment to gain deep insights into your personality
            and behavioral patterns.
          </p>

          {/* Move button further down */}
          <div className="mt-12">
            <button
              onClick={onStart}
              className="inline-flex items-center px-8 py-4 bg-blue-600 text-white text-lg font-semibold rounded-lg hover:bg-blue-700 transition-colors duration-200"
            >
              Start Assessment
              <ChevronRight className="ml-2 w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Move cards down */}
        <div className="grid md:grid-cols-3 gap-6 mt-20">
          <div className="bg-white p-4 rounded-xl shadow-sm">
            <Clock className="w-8 h-8 text-blue-600 mb-2" />
            <h2 className="text-lg font-semibold text-gray-900 mb-1">30 Minutes</h2>
            <p className="text-sm text-gray-600">
              Quick assessment that provides comprehensive insights
            </p>
          </div>
          <div className="bg-white p-4 rounded-xl shadow-sm">
            <FileText className="w-8 h-8 text-blue-600 mb-2" />
            <h2 className="text-lg font-semibold text-gray-900 mb-1">10 Questions</h2>
            <p className="text-sm text-gray-600">
              Carefully crafted questions to analyze your personality
            </p>
          </div>
          <div className="bg-white p-4 rounded-xl shadow-sm">
            <Target className="w-8 h-8 text-blue-600 mb-2" />
            <h2 className="text-lg font-semibold text-gray-900 mb-1">Instant Results</h2>
            <p className="text-sm text-gray-600">
              Get detailed analysis of your personality traits
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
