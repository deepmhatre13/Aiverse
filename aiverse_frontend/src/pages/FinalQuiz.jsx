import { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowLeft,
  Brain,
  CheckCircle,
  XCircle,
  Timer,
  Trophy,
  AlertCircle,
  RefreshCw,
  Download,
  Award,
  Sparkles,
  CircleDot,
} from 'lucide-react';
import Layout from '../components/Layout';
import { Button } from '../components/ui/button';
import { Progress } from '../components/ui/progress';
import { Badge } from '../components/ui/badge';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorState from '../components/ErrorState';
import api from '../api/axios';
import { toast } from 'sonner';
import confetti from 'canvas-confetti';

/**
 * FinalQuiz Page - Course Completion Assessment
 * 
 * Flow:
 * 1. User must complete all lessons first
 * 2. GET /api/learn/courses/{slug}/final-quiz/ - fetches quiz or generates if none
 * 3. User selects answers for all MCQs
 * 4. POST /api/learn/courses/{slug}/final-quiz/submit/ - submits and gets results
 * 5. 75%+ = Pass → Certificate generated
 * 6. <75% = Fail → Can retry
 */
export default function FinalQuiz() {
  const { slug } = useParams();
  const navigate = useNavigate();

  // State
  const [quiz, setQuiz] = useState(null);
  const [course, setCourse] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [showExplanations, setShowExplanations] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [startTime] = useState(Date.now());

  // Timer state
  const [timeElapsed, setTimeElapsed] = useState(0);

  useEffect(() => {
    fetchQuiz();
  }, [slug]);

  // Timer effect
  useEffect(() => {
    let interval;
    if (!result) {
      interval = setInterval(() => {
        setTimeElapsed(Math.floor((Date.now() - startTime) / 1000));
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [result, startTime]);

  const fetchQuiz = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await api.get(`/api/learn/courses/${slug}/final-quiz/`);
      
      if (response.data.quiz) {
        setQuiz(response.data.quiz);
        setCourse(response.data.course);
        
        // Check if user has previous attempt
        if (response.data.previous_attempt) {
          setResult(response.data.previous_attempt);
        }
      } else if (response.data.message) {
        // Quiz not yet generated or generating
        setError(response.data.message);
      }
    } catch (err) {
      const status = err.response?.status;
      const message = err.response?.data?.error || err.response?.data?.detail;
      
      if (status === 403) {
        // Not enrolled or lessons not completed
        setError(message || 'You must complete all lessons before taking the final quiz');
      } else if (status === 404) {
        setError('Course not found');
      } else {
        setError(message || 'Failed to load quiz');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async () => {
    const questions = quiz?.questions || [];
    const answeredCount = Object.keys(selectedAnswers).length;
    
    if (answeredCount < questions.length) {
      toast.warning(`Please answer all ${questions.length} questions before submitting`);
      return;
    }

    try {
      setIsSubmitting(true);
      const response = await api.post(`/api/learn/courses/${slug}/final-quiz/submit/`, {
        answers: selectedAnswers,
      });
      
      setResult(response.data);
      
      // Celebrate on pass
      if (response.data.passed) {
        confetti({
          particleCount: 100,
          spread: 70,
          origin: { y: 0.6 },
          colors: ['#10B981', '#3B82F6', '#8B5CF6', '#F59E0B'],
        });
        toast.success('Congratulations! You passed the final quiz! 🎉');
      } else {
        toast.error(`You scored ${response.data.score}%. You need 75% to pass. Try again!`);
      }
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to submit quiz');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRetry = () => {
    setResult(null);
    setSelectedAnswers({});
    setCurrentQuestion(0);
    setShowExplanations(false);
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Progress calculation
  const answeredCount = Object.keys(selectedAnswers).length;
  const totalQuestions = quiz?.questions?.length || 0;
  const progressPercent = totalQuestions > 0 ? (answeredCount / totalQuestions) * 100 : 0;

  if (isLoading) {
    return (
      <Layout>
        <div className="min-h-[60vh] flex items-center justify-center">
          <LoadingSpinner text="Loading final quiz..." />
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <div className="container mx-auto px-4 py-12">
          <div className="max-w-2xl mx-auto text-center">
            <AlertCircle className="w-16 h-16 mx-auto mb-4 text-amber-500" />
            <h2 className="text-2xl font-bold mb-4">Cannot Take Quiz</h2>
            <p className="text-muted-foreground mb-6">{error}</p>
            <div className="flex justify-center gap-4">
              <Button variant="outline" onClick={() => navigate(`/learn/courses/${slug}`)}>
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Course
              </Button>
              <Button onClick={fetchQuiz}>
                <RefreshCw className="w-4 h-4 mr-2" />
                Try Again
              </Button>
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  // Result view
  if (result) {
    return (
      <Layout>
        <div className="container mx-auto px-4 py-8">
          <div className="max-w-4xl mx-auto">
            {/* Result Header */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className={`rounded-2xl p-8 mb-8 ${
                result.passed
                  ? 'bg-gradient-to-r from-emerald-500/10 via-emerald-500/5 to-transparent border border-emerald-500/20'
                  : 'bg-gradient-to-r from-red-500/10 via-red-500/5 to-transparent border border-red-500/20'
              }`}
            >
              <div className="flex items-center justify-between flex-wrap gap-6">
                <div className="flex items-center gap-4">
                  <div
                    className={`w-16 h-16 rounded-full flex items-center justify-center ${
                      result.passed ? 'bg-emerald-500/20' : 'bg-red-500/20'
                    }`}
                  >
                    {result.passed ? (
                      <Trophy className="w-8 h-8 text-emerald-500" />
                    ) : (
                      <XCircle className="w-8 h-8 text-red-500" />
                    )}
                  </div>
                  <div>
                    <h1 className="text-2xl font-bold">
                      {result.passed ? 'Quiz Passed!' : 'Quiz Not Passed'}
                    </h1>
                    <p className="text-muted-foreground">
                      {result.passed
                        ? 'Congratulations! Your certificate is ready.'
                        : 'Keep learning and try again!'}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-8">
                  <div className="text-center">
                    <div className={`text-4xl font-bold ${result.passed ? 'text-emerald-500' : 'text-red-500'}`}>
                      {result.score ?? (result.score_percent || 0)}%
                    </div>
                    <p className="text-sm text-muted-foreground">Your Score</p>
                  </div>
                  <div className="text-center">
                    <div className="text-4xl font-bold text-muted-foreground">75%</div>
                    <p className="text-sm text-muted-foreground">Required</p>
                  </div>
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-border">
                <div className="text-center">
                  <div className="text-lg font-semibold">
                    {result.correct_count ?? result.correct ?? '?'}/{result.total_questions ?? totalQuestions}
                  </div>
                  <p className="text-xs text-muted-foreground">Correct Answers</p>
                </div>
                <div className="text-center">
                  <div className="text-lg font-semibold">
                    {result.attempt_number ?? 1}
                  </div>
                  <p className="text-xs text-muted-foreground">Attempt</p>
                </div>
                <div className="text-center">
                  <div className="text-lg font-semibold">
                    {result.time_taken ? formatTime(result.time_taken) : formatTime(timeElapsed)}
                  </div>
                  <p className="text-xs text-muted-foreground">Time Taken</p>
                </div>
              </div>
            </motion.div>

            {/* Actions */}
            <div className="flex justify-center gap-4 mb-8">
              <Button variant="outline" onClick={() => navigate(`/learn/courses/${slug}`)}>
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Course
              </Button>
              
              {result.passed && result.certificate_url && (
                <Button asChild className="bg-emerald-600 hover:bg-emerald-700">
                  <a href={result.certificate_url} target="_blank" rel="noopener noreferrer">
                    <Download className="w-4 h-4 mr-2" />
                    Download Certificate
                  </a>
                </Button>
              )}
              
              {!result.passed && (
                <Button onClick={handleRetry}>
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Try Again
                </Button>
              )}
              
              <Button
                variant="ghost"
                onClick={() => setShowExplanations(!showExplanations)}
              >
                {showExplanations ? 'Hide Explanations' : 'View Explanations'}
              </Button>
            </div>

            {/* Question Review with Explanations */}
            <AnimatePresence>
              {showExplanations && result.question_results && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="space-y-4"
                >
                  <h3 className="text-lg font-semibold mb-4">Question Review</h3>
                  {result.question_results.map((qr, index) => (
                    <div
                      key={qr.question_id || index}
                      className={`p-4 rounded-lg border ${
                        qr.is_correct
                          ? 'bg-emerald-500/5 border-emerald-500/20'
                          : 'bg-red-500/5 border-red-500/20'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <div
                          className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 ${
                            qr.is_correct ? 'bg-emerald-500/20' : 'bg-red-500/20'
                          }`}
                        >
                          {qr.is_correct ? (
                            <CheckCircle className="w-4 h-4 text-emerald-500" />
                          ) : (
                            <XCircle className="w-4 h-4 text-red-500" />
                          )}
                        </div>
                        <div className="flex-1">
                          <p className="font-medium mb-2">Q{index + 1}: {qr.question_text || qr.question}</p>
                          <p className="text-sm text-muted-foreground">
                            Your answer: <span className={qr.is_correct ? 'text-emerald-500' : 'text-red-500'}>{qr.user_answer}</span>
                            {!qr.is_correct && (
                              <> • Correct: <span className="text-emerald-500">{qr.correct_answer}</span></>
                            )}
                          </p>
                          {qr.explanation && (
                            <p className="text-sm text-muted-foreground mt-2 p-2 bg-muted/50 rounded">
                              {qr.explanation}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </Layout>
    );
  }

  // Quiz taking view
  const questions = quiz?.questions || [];
  const currentQ = questions[currentQuestion];

  return (
    <Layout>
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <Button
              variant="ghost"
              onClick={() => navigate(`/learn/courses/${slug}`)}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Course
            </Button>
            
            <div className="flex items-center gap-4">
              <Badge variant="outline" className="gap-2">
                <Timer className="w-4 h-4" />
                {formatTime(timeElapsed)}
              </Badge>
              <Badge variant="outline" className="gap-2">
                <Brain className="w-4 h-4" />
                {answeredCount}/{totalQuestions}
              </Badge>
            </div>
          </div>

          {/* Quiz Header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gradient-to-r from-primary/10 via-primary/5 to-primary/10 rounded-2xl p-6 mb-8 border border-primary/20"
          >
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 rounded-xl bg-primary/20 flex items-center justify-center">
                <Award className="w-6 h-6 text-primary" />
              </div>
              <div>
                <h1 className="text-2xl font-bold">Final Assessment</h1>
                <p className="text-muted-foreground">{course?.title || 'Course'}</p>
              </div>
            </div>
            
            <div className="flex items-center gap-6 text-sm text-muted-foreground">
              <span className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-amber-500" />
                {totalQuestions} Questions
              </span>
              <span>•</span>
              <span>75% to Pass</span>
              <span>•</span>
              <span>Certificate on Completion</span>
            </div>
            
            {/* Progress bar */}
            <div className="mt-4">
              <Progress value={progressPercent} className="h-2" />
              <p className="text-xs text-muted-foreground mt-1">
                {answeredCount} of {totalQuestions} answered
              </p>
            </div>
          </motion.div>

          {/* Question Navigation Pills */}
          <div className="flex flex-wrap gap-2 mb-6">
            {questions.map((q, idx) => {
              const isAnswered = selectedAnswers[q.id] !== undefined;
              const isCurrent = idx === currentQuestion;
              
              return (
                <button
                  key={q.id}
                  onClick={() => setCurrentQuestion(idx)}
                  className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium transition-colors ${
                    isCurrent
                      ? 'bg-primary text-primary-foreground'
                      : isAnswered
                      ? 'bg-emerald-500/20 text-emerald-500 border border-emerald-500/30'
                      : 'bg-muted hover:bg-muted/80'
                  }`}
                >
                  {idx + 1}
                </button>
              );
            })}
          </div>

          {/* Current Question */}
          {currentQ && (
            <motion.div
              key={currentQ.id}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-card border border-border rounded-xl p-6"
            >
              <div className="flex items-start gap-4 mb-6">
                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                  <span className="text-sm font-semibold text-primary">
                    {currentQuestion + 1}
                  </span>
                </div>
                <h3 className="text-lg font-medium leading-relaxed">
                  {currentQ.question_text || currentQ.question}
                </h3>
              </div>

              {/* Answer Options */}
              <div className="space-y-3 pl-12">
                {['A', 'B', 'C', 'D'].map((option) => {
                  const optionText = currentQ[`option_${option.toLowerCase()}`] || currentQ[`option${option}`];
                  if (!optionText) return null;
                  
                  const isSelected = selectedAnswers[currentQ.id] === option;
                  
                  return (
                    <button
                      key={option}
                      onClick={() => setSelectedAnswers(prev => ({ ...prev, [currentQ.id]: option }))}
                      className={`w-full flex items-center gap-4 p-4 rounded-lg border text-left transition-all ${
                        isSelected
                          ? 'bg-primary/10 border-primary shadow-sm'
                          : 'bg-muted/30 border-transparent hover:bg-muted/50 hover:border-border'
                      }`}
                    >
                      <div
                        className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 transition-colors ${
                          isSelected
                            ? 'bg-primary text-primary-foreground'
                            : 'bg-muted'
                        }`}
                      >
                        <span className="text-sm font-medium">{option}</span>
                      </div>
                      <span className="text-sm">{optionText}</span>
                    </button>
                  );
                })}
              </div>

              {/* Navigation */}
              <div className="flex items-center justify-between mt-8 pt-6 border-t border-border">
                <Button
                  variant="outline"
                  onClick={() => setCurrentQuestion(prev => Math.max(0, prev - 1))}
                  disabled={currentQuestion === 0}
                >
                  Previous
                </Button>
                
                {currentQuestion < questions.length - 1 ? (
                  <Button
                    onClick={() => setCurrentQuestion(prev => Math.min(questions.length - 1, prev + 1))}
                  >
                    Next Question
                  </Button>
                ) : (
                  <Button
                    onClick={handleSubmit}
                    disabled={isSubmitting || answeredCount < totalQuestions}
                    className="bg-emerald-600 hover:bg-emerald-700"
                  >
                    {isSubmitting ? (
                      <>
                        <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                        Submitting...
                      </>
                    ) : (
                      <>
                        <CheckCircle className="w-4 h-4 mr-2" />
                        Submit Quiz
                      </>
                    )}
                  </Button>
                )}
              </div>
            </motion.div>
          )}

          {/* Submit Button (always visible when all answered) */}
          {answeredCount === totalQuestions && currentQuestion < questions.length - 1 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-6 text-center"
            >
              <Button
                size="lg"
                onClick={handleSubmit}
                disabled={isSubmitting}
                className="bg-emerald-600 hover:bg-emerald-700"
              >
                {isSubmitting ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  <>
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Submit All Answers
                  </>
                )}
              </Button>
            </motion.div>
          )}
        </div>
      </div>
    </Layout>
  );
}
