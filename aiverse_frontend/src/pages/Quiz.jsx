import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import PostActionCard from '../components/PostActionCard';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorState from '../components/ErrorState';
import { useTracker } from '../hooks/useTracker';
import { Events } from '../api/trackingApi';
import { useLearner } from '../contexts/LearnerContext';
import {
  findLessonById,
  getLessonQuiz,
  submitLessonQuiz,
  normalizeQuizQuestions,
} from '../api/coursesApi';

export default function Quiz() {
  const { id } = useParams();
  const { track } = useTracker();
  const { refetch } = useLearner();
  const navigate = useNavigate();

  const [quiz, setQuiz] = useState(null);
  const [route, setRoute] = useState(null);
  const [currentQ, setCurrentQ] = useState(0);
  const [answers, setAnswers] = useState({});
  const [submitted, setSubmitted] = useState(false);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const startTimeRef = useRef(Date.now());

  useEffect(() => {
    (async () => {
      try {
        const resolved = await findLessonById(id);
        if (!resolved) {
          setError('Quiz not found');
          setLoading(false);
          return;
        }

        setRoute(resolved);
        const res = await getLessonQuiz(resolved.course.slug, resolved.lesson.slug);
        if (!res.data?.has_quiz) {
          setError(res.data?.message || 'No quiz available for this lesson');
          setLoading(false);
          return;
        }

        const normalized = {
          ...res.data.quiz,
          questions: normalizeQuizQuestions(res.data.quiz?.questions || []),
          concept_tag: resolved.lesson.concept_tag,
        };
        setQuiz(normalized);
        track(Events.QUIZ_STARTED, 'quiz', Number(id));
      } catch {
        setError('Failed to load quiz');
      } finally {
        setLoading(false);
      }
    })();
  }, [id, track]);

  const handleAnswer = (questionId, answer) => {
    setAnswers((prev) => ({ ...prev, [questionId]: answer }));
  };

  const handleSubmit = async () => {
    if (!route) return;
    const timeTaken = Math.round((Date.now() - startTimeRef.current) / 1000);

    try {
      const res = await submitLessonQuiz(route.course.slug, route.lesson.slug, {
        answers,
        time_taken_seconds: timeTaken,
      });

      const passed = res.data?.passed ?? res.data?.score >= (quiz?.passing_score || 70);
      const score = res.data?.score ?? 0;

      setResult({
        passed,
        score,
        mastery_before: res.data?.mastery_before,
        mastery_after: res.data?.mastery_after,
        concept_tag: res.data?.concept_tag || quiz?.concept_tag,
      });
      setSubmitted(true);

      track(Events.QUIZ_SUBMITTED, 'quiz', Number(id), {
        score,
        time_taken_seconds: timeTaken,
      });
      track(passed ? Events.QUIZ_PASSED : Events.QUIZ_FAILED, 'quiz', Number(id), { score });

      setTimeout(refetch, 1500);
    } catch (e) {
      console.error('Quiz submit failed', e);
    }
  };

  if (loading) {
    return (
      <Layout>
        <LoadingSpinner text="Loading quiz..." />
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <ErrorState message={error} onRetry={() => navigate('/learn')} />
      </Layout>
    );
  }

  const question = quiz?.questions?.[currentQ];
  const totalQ = quiz?.questions?.length || 0;
  const progress = totalQ ? ((currentQ + 1) / totalQ) * 100 : 0;

  if (submitted && result) {
    return (
      <Layout showFooter={false}>
        <div className="min-h-[calc(100vh-4rem)] bg-[#0a0a0a] text-white flex items-center justify-center px-6">
          <div className="max-w-lg w-full bg-[#111] border border-[#222] rounded-2xl p-8 text-center">
            <div className="text-6xl mb-4">{result.passed ? '🎉' : '📚'}</div>
            <h2 className="text-2xl font-bold mb-2">
              {result.passed ? 'Quiz Passed!' : 'Keep Practicing'}
            </h2>
            <p className="text-gray-400 mb-6">
              You scored{' '}
              <span
                className={`font-bold text-xl ${result.passed ? 'text-green-400' : 'text-red-400'}`}
              >
                {Number(result.score).toFixed(0)}%
              </span>
            </p>

            {(result.mastery_before != null || result.mastery_after != null) && (
              <div className="mt-4 bg-[#1a1a1a] border border-[#333] rounded-xl p-4 mb-4 text-left">
                <p className="text-xs text-gray-500 mb-2 uppercase tracking-wide">
                  Knowledge tracing update
                </p>
                <div className="flex items-center gap-4">
                  <div className="text-center">
                    <p className="text-xs text-gray-600">Before</p>
                    <p className="text-lg font-bold text-gray-400">
                      {Math.round((result.mastery_before || 0) * 100)}%
                    </p>
                  </div>
                  <div className="text-2xl text-[#E8392A]">→</div>
                  <div className="text-center">
                    <p className="text-xs text-gray-600">After</p>
                    <p className="text-lg font-bold text-green-400">
                      {Math.round((result.mastery_after || 0) * 100)}%
                    </p>
                  </div>
                  <div className="flex-1 ml-4">
                    <p className="text-xs text-gray-500 mb-1">
                      {(result.concept_tag || quiz?.concept_tag || '').replace(/_/g, ' ')} mastery
                    </p>
                    <div className="w-full h-2 bg-[#222] rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-[#E8392A] to-green-500 rounded-full transition-all duration-1000"
                        style={{ width: `${(result.mastery_after || 0) * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
                <p className="text-xs text-gray-600 mt-2 italic">
                  Powered by Bayesian Knowledge Tracing
                </p>
              </div>
            )}

            <div className="bg-[#1a1a1a] rounded-xl p-4 mb-6 text-left">
              <PostActionCard
                type="quiz"
                score={Number(result.score).toFixed(0)}
                conceptTag={result.concept_tag || quiz.concept_tag}
                passed={result.passed}
              />
            </div>

            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => navigate('/dashboard')}
                className="flex-1 bg-[#E8392A] hover:bg-[#c42d1f] text-white py-3 rounded-lg font-medium transition-colors"
              >
                Back to dashboard
              </button>
              {!result.passed && (
                <button
                  type="button"
                  onClick={() => {
                    setSubmitted(false);
                    setCurrentQ(0);
                    setAnswers({});
                    startTimeRef.current = Date.now();
                  }}
                  className="flex-1 border border-[#333] hover:border-[#E8392A]/50 text-white py-3 rounded-lg font-medium transition-colors"
                >
                  Try again
                </button>
              )}
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout showFooter={false}>
      <div className="min-h-[calc(100vh-4rem)] bg-[#0a0a0a] text-white px-6 py-10">
        <div className="max-w-2xl mx-auto">
          <div className="mb-8">
            <div className="flex justify-between text-sm text-gray-500 mb-2">
              <span>{quiz?.title}</span>
              <span>
                Question {currentQ + 1} of {totalQ}
              </span>
            </div>
            <div className="w-full h-1.5 bg-[#222] rounded-full overflow-hidden">
              <div
                className="h-full bg-[#E8392A] rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          {question && (
            <div className="bg-[#111] border border-[#222] rounded-2xl p-8">
              <p className="text-lg font-medium mb-8 leading-relaxed">{question.question_text}</p>

              <div className="space-y-3">
                {question.options.map((option) => {
                  const isSelected = answers[question.id] === option.id;
                  return (
                    <button
                      key={option.id}
                      type="button"
                      onClick={() => handleAnswer(question.id, option.id)}
                      className={`w-full text-left px-5 py-4 rounded-xl border text-sm transition-all ${
                        isSelected
                          ? 'border-[#E8392A] bg-[#E8392A]/10 text-white'
                          : 'border-[#333] bg-[#1a1a1a] text-gray-300 hover:border-[#444] hover:text-white'
                      }`}
                    >
                      <span
                        className={`inline-block w-6 h-6 rounded-full border mr-3 text-xs align-middle text-center leading-6 ${
                          isSelected
                            ? 'border-[#E8392A] bg-[#E8392A] text-white'
                            : 'border-[#555] text-gray-500'
                        }`}
                      >
                        {option.id}
                      </span>
                      {option.text}
                    </button>
                  );
                })}
              </div>

              <div className="flex justify-between items-center mt-8">
                <button
                  type="button"
                  onClick={() => setCurrentQ((q) => Math.max(0, q - 1))}
                  disabled={currentQ === 0}
                  className="text-sm text-gray-500 hover:text-white disabled:opacity-30 transition-colors"
                >
                  ← Previous
                </button>

                {currentQ < totalQ - 1 ? (
                  <button
                    type="button"
                    onClick={() => setCurrentQ((q) => q + 1)}
                    disabled={!answers[question.id]}
                    className="bg-[#E8392A] disabled:opacity-40 hover:bg-[#c42d1f] text-white px-6 py-2.5 rounded-lg font-medium transition-colors"
                  >
                    Next →
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={handleSubmit}
                    disabled={Object.keys(answers).length < totalQ}
                    className="bg-[#E8392A] disabled:opacity-40 hover:bg-[#c42d1f] text-white px-6 py-2.5 rounded-lg font-medium transition-colors"
                  >
                    Submit quiz
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}
