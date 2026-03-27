import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowLeft,
  ChevronLeft,
  ChevronRight,
  CheckCircle,
  List,
  Play,
  Lock,
  X,
  Menu,
  Clock,
  BookOpen,
  FileText,
  Download,
  ExternalLink,
  Maximize2,
  Volume2,
  Settings,
  SkipBack,
  SkipForward,
  Brain,
  CircleDot,
  Trophy,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';
import Layout from '../components/Layout';
import { Button } from '../components/ui/button';
import { Progress } from '../components/ui/progress';
import { Badge } from '../components/ui/badge';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '../components/ui/tabs';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorState from '../components/ErrorState';
import api from '../api/axios';
import { toast } from 'sonner';

/**
 * Lesson Page - Video Player with Progress Tracking
 * 
 * Features:
 * - Collapsible lesson sidebar
 * - Video player (YouTube embed or hosted video)
 * - Watch time tracking
 * - Mark complete functionality
 * - Lesson notes/content tab
 * - Resources/attachments tab
 * - Keyboard shortcuts
 */
export default function Lesson() {
  const { slug: courseSlug, lessonSlug } = useParams();
  const navigate = useNavigate();

  // State
  const [lesson, setLesson] = useState(null);
  const [course, setCourse] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showSidebar, setShowSidebar] = useState(true);
  const [isMarkingComplete, setIsMarkingComplete] = useState(false);
  const [watchTime, setWatchTime] = useState(0);
  const [activeTab, setActiveTab] = useState('notes');

  // Quiz state
  const [quiz, setQuiz] = useState(null);
  const [quizLoading, setQuizLoading] = useState(false);
  const [quizLocked, setQuizLocked] = useState(false);
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [quizResult, setQuizResult] = useState(null);
  const [isSubmittingQuiz, setIsSubmittingQuiz] = useState(false);
  const [showExplanations, setShowExplanations] = useState(false);

  // Refs
  const watchTimeIntervalRef = useRef(null);
  const lastSaveTimeRef = useRef(0);
  const iframeRef = useRef(null);

  // Fetch lesson and course data
  useEffect(() => {
    fetchLesson();
    return () => {
      // Cleanup interval on unmount
      if (watchTimeIntervalRef.current) {
        clearInterval(watchTimeIntervalRef.current);
      }
      // Save final watch time
      saveWatchTime();
    };
  }, [courseSlug, lessonSlug]);

  // Start watch time tracking
  useEffect(() => {
    if (lesson && !lesson.is_completed && !lesson.progress?.completed) {
      startWatchTimeTracking();
    }
    return () => {
      if (watchTimeIntervalRef.current) {
        clearInterval(watchTimeIntervalRef.current);
      }
    };
  }, [lesson]);

  // Fetch quiz only when lesson is unlocked (prevent unnecessary 403)
  useEffect(() => {
    if (lesson?.id && lesson?.is_unlocked !== false) {
      fetchQuiz();
    }
  }, [lesson?.id, lesson?.is_unlocked, courseSlug, lessonSlug]);

  // Reset quiz state when lesson changes
  useEffect(() => {
    setQuiz(null);
    setQuizLocked(false);
    setSelectedAnswers({});
    setQuizResult(null);
    setShowExplanations(false);
  }, [lessonSlug]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Don't trigger shortcuts when typing in inputs
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
        return;
      }

      switch (e.key) {
        case 'ArrowLeft':
          if (e.ctrlKey || e.metaKey) {
            goToPreviousLesson();
          }
          break;
        case 'ArrowRight':
          if (e.ctrlKey || e.metaKey) {
            goToNextLesson();
          }
          break;
        case 'm':
          if (!e.ctrlKey && !e.metaKey) {
            markAsComplete();
          }
          break;
        case 's':
          if (!e.ctrlKey && !e.metaKey) {
            setShowSidebar((prev) => !prev);
          }
          break;
        default:
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [lesson]);

  const fetchLesson = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Fetch lesson and course in parallel
      const [lessonRes, courseRes] = await Promise.all([
        api
          .get(`/api/learn/courses/${courseSlug}/lessons/${lessonSlug}/`)
          .catch((err) => {
            if (err.response?.status === 403) {
              return {
                data: null,
                accessDenied: true,
                message:
                  err.response.data?.message ||
                  err.response.data?.error ||
                  'Access denied',
              };
            }
            throw err;
          }),
        api.get(`/api/learn/courses/${courseSlug}/`),
      ]);

      if (lessonRes.accessDenied) {
        setError(lessonRes.message);
        setLesson(null);
      } else {
        const lessonData = lessonRes.data?.lesson ?? lessonRes.data;
        setLesson(lessonData);
        if (lessonData?.progress?.watch_time_seconds) {
          setWatchTime(lessonData.progress.watch_time_seconds);
        }
      }
      setCourse(courseRes.data?.course ?? courseRes.data);
    } catch (err) {
      if (err.response?.status === 403) {
        setError(
          err.response.data?.message ||
            err.response.data?.error ||
            'You do not have access to this lesson. Please purchase the course.'
        );
      } else if (err.response?.status === 404) {
        setError('Lesson not found');
      } else {
        setError(err.message || 'Failed to load lesson');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const startWatchTimeTracking = () => {
    // Track watch time every second
    watchTimeIntervalRef.current = setInterval(() => {
      setWatchTime((prev) => {
        const newTime = prev + 1;
        // Save every 30 seconds
        if (newTime - lastSaveTimeRef.current >= 30) {
          saveWatchTime(newTime);
          lastSaveTimeRef.current = newTime;
        }
        return newTime;
      });
    }, 1000);
  };

  const saveWatchTime = async (time = watchTime) => {
    if (!lesson || time <= 0) return;

    try {
      await api.post(
        `/api/learn/courses/${courseSlug}/lessons/${lessonSlug}/progress/`,
        {
          watch_time_seconds: time,
        }
      );
    } catch (err) {
      console.error('Failed to save watch time:', err);
    }
  };

  const markAsComplete = async () => {
    if (!lesson || isMarkingComplete) return;

    try {
      setIsMarkingComplete(true);
      await api.post(
        `/api/learn/courses/${courseSlug}/lessons/${lessonSlug}/progress/`,
        {
          completed: true,
          watch_time_seconds: watchTime,
        }
      );

      toast.success('Lesson marked as complete!');

      // Update lesson state
      setLesson((prev) => ({
        ...prev,
        is_completed: true,
        progress: {
          ...prev?.progress,
          completed: true,
          watch_time_seconds: watchTime,
        },
      }));

      // Auto-advance to next lesson after short delay
      if (lesson.next_lesson) {
        setTimeout(() => {
          navigate(
            `/learn/courses/${courseSlug}/lessons/${lesson.next_lesson.slug}`
          );
        }, 1500);
      }
    } catch (err) {
      toast.error(
        err.response?.data?.message ||
          err.response?.data?.error ||
          'Failed to update progress'
      );
    } finally {
      setIsMarkingComplete(false);
    }
  };

  // Quiz functions
  const fetchQuiz = async () => {
    try {
      setQuizLoading(true);
      setQuizLocked(false);
      const res = await api.get(
        `/api/learn/courses/${courseSlug}/lessons/${lessonSlug}/quiz/`
      );
      if (res.data?.has_quiz && res.data?.quiz) {
        setQuiz(res.data.quiz);
      } else {
        setQuiz(null);
      }
    } catch (err) {
      if (err.response?.status === 403) {
        setQuizLocked(true);
        setQuiz(null);
      } else if (err.response?.status !== 404) {
        setQuiz(null);
      } else {
        setQuiz(null);
      }
    } finally {
      setQuizLoading(false);
    }
  };

  const handleAnswerSelect = (mcqId, optionIndex) => {
    if (quizResult) return; // Don't allow changes after submission
    setSelectedAnswers((prev) => ({
      ...prev,
      [mcqId]: optionIndex,
    }));
  };

  const submitQuiz = async () => {
    if (!quiz || isSubmittingQuiz) return;

    // Validate all questions are answered
    const questions = quiz.questions || quiz.mcqs || [];
    const unanswered = questions.filter((q) => selectedAnswers[q.id] === undefined);
    if (unanswered.length > 0) {
      toast.error(`Please answer all questions (${unanswered.length} remaining)`);
      return;
    }

    try {
      setIsSubmittingQuiz(true);
      // API expects answers as {question_id: 'A'|'B'|'C'|'D'}
      const questions = quiz.questions || quiz.mcqs || [];
      const answers = {};
      questions.forEach((q) => {
        const optionIndex = selectedAnswers[q.id];
        if (optionIndex !== undefined) {
          answers[q.id] = ['A', 'B', 'C', 'D'][optionIndex];
        }
      });

      const res = await api.post(
        `/api/learn/courses/${courseSlug}/lessons/${lessonSlug}/quiz/submit/`,
        { answers }
      );

      // API returns {attempt, quiz, user_answers, question_results, lesson_completed}
      const { attempt, question_results } = res.data;
      setQuizResult({
        score: attempt?.score || 0,
        passed: attempt?.passed || false,
        results: question_results || [],
      });
      setShowExplanations(true);

      if (attempt?.passed) {
        toast.success(`Quiz passed! Score: ${attempt.score}%`);
      } else {
        toast.info(`Score: ${attempt?.score || 0}%. Need ${quiz.passing_score}% to pass.`);
      }
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to submit quiz');
    } finally {
      setIsSubmittingQuiz(false);
    }
  };

  const retakeQuiz = () => {
    setSelectedAnswers({});
    setQuizResult(null);
    setShowExplanations(false);
  };

  const goToPreviousLesson = () => {
    if (lesson?.prev_lesson) {
      saveWatchTime();
      navigate(
        `/learn/courses/${courseSlug}/lessons/${lesson.prev_lesson.slug}`
      );
    }
  };

  const goToNextLesson = () => {
    if (lesson?.next_lesson) {
      saveWatchTime();
      navigate(
        `/learn/courses/${courseSlug}/lessons/${lesson.next_lesson.slug}`
      );
    }
  };

  // Calculate progress - guard against NaN (division by zero)
  const totalLessons = course?.lessons?.length ?? 0;
  const currentIndex =
    totalLessons > 0
      ? (course?.lessons?.findIndex((l) => l.slug === lessonSlug) ?? 0)
      : 0;
  const completedCount =
    course?.lessons?.filter(
      (l) => l.is_completed || l.progress?.is_completed || l.progress?.completed
    )?.length ?? 0;
  const progress =
    totalLessons > 0 ? Math.round(((currentIndex + 1) / totalLessons) * 100) : 0;
  const completionPercent =
    totalLessons > 0
      ? Math.round((completedCount / totalLessons) * 100)
      : 0;

  // Format watch time
  const formatTime = (seconds) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    if (h > 0) {
      return `${h}:${m.toString().padStart(2, '0')}:${s
        .toString()
        .padStart(2, '0')}`;
    }
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  // Get video URL - prefer embed_url from backend, then video_url, youtube_id, youtube_url
  const getVideoUrl = () => {
    if (lesson?.embed_url) return lesson.embed_url;
    if (lesson?.video_url) return lesson.video_url;
    if (lesson?.youtube_id) {
      return `https://www.youtube.com/embed/${lesson.youtube_id}?rel=0&modestbranding=1`;
    }
    if (lesson?.youtube_url) {
      const match = lesson.youtube_url.match(
        /(?:youtube\.com\/(?:watch\?v=|embed\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})/
      );
      if (match) return `https://www.youtube.com/embed/${match[1]}?rel=0&modestbranding=1`;
    }
    return null;
  };

  const videoUrl = getVideoUrl();
  const isCompleted = lesson?.is_completed || lesson?.progress?.is_completed || lesson?.progress?.completed;

  // Loading state
  if (isLoading) {
    return (
      <Layout showFooter={false}>
        <div className="min-h-[80vh] flex items-center justify-center bg-background">
          <LoadingSpinner text="Loading lesson..." />
        </div>
      </Layout>
    );
  }

  // Error state
  if (error || !lesson) {
    return (
      <Layout showFooter={false}>
        <div className="min-h-[80vh] flex flex-col items-center justify-center bg-background px-4">
          <ErrorState message={error || 'Lesson not found'} onRetry={fetchLesson} />
          <Link
            to={`/learn/courses/${courseSlug}`}
            className="mt-6 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="w-4 h-4 inline mr-2" />
            Back to Course
          </Link>
        </div>
      </Layout>
    );
  }

  return (
    <Layout showFooter={false}>
      <div className="h-[calc(100vh-4rem)] flex bg-background">
        {/* Sidebar */}
        <AnimatePresence>
          {showSidebar && (
            <motion.aside
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 320, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="h-full border-r border-border bg-card overflow-hidden shrink-0"
            >
              <div className="w-80 h-full flex flex-col">
                {/* Sidebar Header */}
                <div className="p-4 border-b border-border shrink-0">
                  <Link
                    to={`/learn/courses/${courseSlug}`}
                    className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mb-3 transition-colors"
                  >
                    <ArrowLeft className="w-4 h-4" />
                    Back to Course
                  </Link>
                  <h2 className="font-semibold text-foreground line-clamp-2">
                    {course?.title}
                  </h2>

                  {/* Course Progress */}
                  <div className="mt-3">
                    <div className="flex justify-between text-xs mb-1.5">
                      <span className="text-muted-foreground">
                        {completedCount}/{totalLessons} completed
                      </span>
                      <span className="font-medium">{completionPercent}%</span>
                    </div>
                    <Progress
                      value={completionPercent}
                      className="h-1.5"
                    />
                  </div>
                </div>

                {/* Lesson List */}
                <div className="flex-1 overflow-auto">
                  <div className="p-2">
                    {course?.lessons?.map((l, index) => {
                      const isCurrent = l.slug === lessonSlug;
                      const isLessonCompleted =
                        l.is_completed || l.progress?.is_completed || l.progress?.completed;
                      const isUnlocked = l.is_unlocked !== false;

                      return isUnlocked ? (
                        <Link
                          key={l.id || l.slug}
                          to={`/learn/courses/${courseSlug}/lessons/${l.slug}`}
                          className={`flex items-center gap-3 p-3 rounded-lg transition-all ${
                            isCurrent
                              ? 'bg-primary/10 border border-primary/20'
                              : 'hover:bg-muted'
                          }`}
                        >
                          {/* Status Icon */}
                          <div
                            className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 text-xs font-medium ${
                              isLessonCompleted
                                ? 'bg-emerald-500/10 text-emerald-500'
                                : isCurrent
                                ? 'bg-primary text-primary-foreground'
                                : 'bg-muted text-muted-foreground'
                            }`}
                          >
                            {isLessonCompleted ? (
                              <CheckCircle className="w-4 h-4" />
                            ) : (
                              index + 1
                            )}
                          </div>

                          {/* Lesson Info */}
                          <div className="flex-1 min-w-0">
                            <p
                              className={`text-sm font-medium truncate ${
                                isCurrent
                                  ? 'text-primary'
                                  : 'text-foreground'
                              }`}
                            >
                              {l.title}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {l.duration_minutes || l.duration || 0}m
                            </p>
                          </div>

                          {/* Playing indicator */}
                          {isCurrent && (
                            <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                          )}
                        </Link>
                      ) : (
                        <div
                          key={l.id || l.slug}
                          className="flex items-center gap-3 p-3 rounded-lg opacity-60 cursor-not-allowed"
                        >
                          <div className="w-7 h-7 rounded-full flex items-center justify-center shrink-0 bg-muted text-muted-foreground">
                            <Lock className="w-3.5 h-3.5" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium truncate text-muted-foreground">{l.title}</p>
                            <p className="text-xs text-muted-foreground">Complete previous lesson</p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </motion.aside>
          )}
        </AnimatePresence>

        {/* Main Content */}
        <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
          {/* Video Player */}
          <div className="relative bg-black w-full" style={{ maxHeight: '60vh' }}>
            <div className="aspect-video w-full h-full">
              {videoUrl ? (
                <iframe
                  ref={iframeRef}
                  src={videoUrl}
                  className="w-full h-full"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                  allowFullScreen
                  frameBorder="0"
                  title={lesson.title}
                  loading="lazy"
                />
              ) : (
                <div className="w-full h-full flex flex-col items-center justify-center text-white/50">
                  <Play className="w-16 h-16 mb-4" />
                  <p className="text-sm">Video not available</p>
                </div>
              )}
            </div>

            {/* Toggle Sidebar Button */}
            <button
              onClick={() => setShowSidebar(!showSidebar)}
              className="absolute top-4 left-4 p-2.5 rounded-lg bg-black/60 text-white hover:bg-black/80 transition-colors z-10 backdrop-blur-sm"
              title={showSidebar ? 'Hide sidebar (S)' : 'Show sidebar (S)'}
            >
              {showSidebar ? (
                <X className="w-5 h-5" />
              ) : (
                <Menu className="w-5 h-5" />
              )}
            </button>

            {/* Watch Time Display */}
            <div className="absolute top-4 right-4 px-3 py-1.5 rounded-lg bg-black/60 text-white text-sm backdrop-blur-sm">
              <Clock className="w-4 h-4 inline mr-1.5" />
              {formatTime(watchTime)}
            </div>
          </div>

          {/* Lesson Content Area */}
          <div className="flex-1 overflow-auto">
            <div className="max-w-5xl mx-auto px-4 lg:px-8 py-6">
              {/* Lesson Header */}
              <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-6">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant="outline" className="text-xs">
                      Lesson {currentIndex + 1} of {totalLessons}
                    </Badge>
                    {isCompleted && (
                      <Badge
                        variant="secondary"
                        className="bg-emerald-500/10 text-emerald-500"
                      >
                        <CheckCircle className="w-3 h-3 mr-1" />
                        Completed
                      </Badge>
                    )}
                  </div>
                  <h1 className="text-2xl font-bold text-foreground">
                    {lesson.title}
                  </h1>
                </div>

                {/* Mark Complete Button */}
                <Button
                  onClick={markAsComplete}
                  disabled={isMarkingComplete || isCompleted}
                  className={`shrink-0 ${
                    isCompleted
                      ? 'bg-emerald-600 hover:bg-emerald-600 cursor-default'
                      : 'bg-primary hover:bg-primary/90'
                  }`}
                >
                  {isMarkingComplete ? (
                    <LoadingSpinner size="sm" className="mr-2" />
                  ) : (
                    <CheckCircle className="w-4 h-4 mr-2" />
                  )}
                  {isCompleted ? 'Completed' : 'Mark Complete'}
                </Button>
              </div>

              {/* Content Tabs */}
              <Tabs
                value={activeTab}
                onValueChange={setActiveTab}
                className="w-full"
              >
                <TabsList className="mb-6">
                  <TabsTrigger value="notes" className="gap-2">
                    <FileText className="w-4 h-4" />
                    Notes
                  </TabsTrigger>
                  <TabsTrigger value="resources" className="gap-2">
                    <Download className="w-4 h-4" />
                    Resources
                  </TabsTrigger>
                  <TabsTrigger value="quiz" className="gap-2">
                    <Brain className="w-4 h-4" />
                    Quiz
                    {quiz && (
                      <Badge variant="secondary" className="ml-1 text-xs">
                        {quiz.mcqs?.length || 0}
                      </Badge>
                    )}
                  </TabsTrigger>
                </TabsList>

                {/* Notes Tab */}
                <TabsContent value="notes" className="mt-0">
                  {lesson.description && (
                    <div className="mb-6">
                      <p className="text-muted-foreground leading-relaxed">
                        {lesson.description}
                      </p>
                    </div>
                  )}

                  {lesson.content ? (
                    <div className="prose prose-sm max-w-none dark:prose-invert">
                      <div
                        dangerouslySetInnerHTML={{ __html: lesson.content }}
                      />
                    </div>
                  ) : (
                    <div className="text-center py-12 text-muted-foreground">
                      <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
                      <p>No notes available for this lesson</p>
                    </div>
                  )}
                </TabsContent>

                {/* Resources Tab */}
                <TabsContent value="resources" className="mt-0">
                  {lesson.resources && lesson.resources.length > 0 ? (
                    <div className="space-y-3">
                      {lesson.resources.map((resource, index) => (
                        <a
                          key={resource.id || index}
                          href={resource.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-3 p-4 bg-card border border-border rounded-lg hover:border-primary/50 transition-colors"
                        >
                          <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                            {resource.type === 'pdf' ? (
                              <FileText className="w-5 h-5 text-primary" />
                            ) : resource.type === 'link' ? (
                              <ExternalLink className="w-5 h-5 text-primary" />
                            ) : (
                              <Download className="w-5 h-5 text-primary" />
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-sm truncate">
                              {resource.title || resource.name}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {resource.type?.toUpperCase() || 'Resource'}
                            </p>
                          </div>
                          <ExternalLink className="w-4 h-4 text-muted-foreground" />
                        </a>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-12 text-muted-foreground">
                      <Download className="w-12 h-12 mx-auto mb-4 opacity-50" />
                      <p>No resources available for this lesson</p>
                    </div>
                  )}
                </TabsContent>

                {/* Quiz Tab */}
                <TabsContent value="quiz" className="mt-0">
                  {(quizLocked || lesson?.is_unlocked === false) ? (
                    <div className="flex flex-col items-center justify-center py-16 px-4 bg-muted/30 rounded-lg border border-border">
                      <Lock className="w-12 h-12 text-muted-foreground mb-4" />
                      <p className="text-center font-medium text-foreground mb-2">
                        Lesson locked
                      </p>
                      <p className="text-center text-sm text-muted-foreground max-w-md">
                        Complete the previous lesson to unlock this quiz.
                      </p>
                    </div>
                  ) : quizLoading ? (
                    <div className="flex items-center justify-center py-12">
                      <LoadingSpinner size="lg" />
                    </div>
                  ) : quiz ? (
                    <div className="space-y-6">
                      {/* Quiz Header */}
                      <div className="flex items-center justify-between p-4 bg-card border border-border rounded-lg">
                        <div>
                          <h3 className="font-semibold text-foreground">
                            Lesson Quiz
                          </h3>
                          <p className="text-sm text-muted-foreground">
                            {(quiz.questions || quiz.mcqs)?.length || quiz.total_questions} questions • Pass: {quiz.passing_score}%
                          </p>
                        </div>
                        {quizResult && (
                          <div className={`text-right ${quizResult.passed ? 'text-emerald-500' : 'text-amber-500'}`}>
                            <div className="flex items-center gap-2">
                              {quizResult.passed ? (
                                <Trophy className="w-5 h-5" />
                              ) : (
                                <AlertCircle className="w-5 h-5" />
                              )}
                              <span className="text-2xl font-bold">{quizResult.score}%</span>
                            </div>
                            <p className="text-xs">
                              {quizResult.passed ? 'Passed!' : 'Try again'}
                            </p>
                          </div>
                        )}
                      </div>

                      {/* MCQ Questions */}
                      <div className="space-y-6">
                        {(quiz.questions || quiz.mcqs || []).map((mcq, qIndex) => {
                          const selectedOption = selectedAnswers[mcq.id];
                          const resultForMcq = quizResult?.results?.find(r => r.question_id === String(mcq.id));
                          const isCorrect = resultForMcq?.is_correct;
                          const correctOptionLetter = resultForMcq?.correct_answer;
                          const correctOptionIndex = correctOptionLetter ? ['A', 'B', 'C', 'D'].indexOf(correctOptionLetter) : -1;

                          return (
                            <motion.div
                              key={mcq.id}
                              initial={{ opacity: 0, y: 20 }}
                              animate={{ opacity: 1, y: 0 }}
                              transition={{ delay: qIndex * 0.1 }}
                              className={`p-5 bg-card border rounded-lg ${
                                quizResult
                                  ? isCorrect
                                    ? 'border-emerald-500/50'
                                    : 'border-red-500/50'
                                  : 'border-border'
                              }`}
                            >
                              {/* Question */}
                              <div className="flex gap-3 mb-4">
                                <span className="flex-shrink-0 w-7 h-7 rounded-full bg-primary/10 text-primary text-sm font-medium flex items-center justify-center">
                                  {qIndex + 1}
                                </span>
                                <p className="font-medium text-foreground pt-0.5">
                                  {mcq.question}
                                </p>
                              </div>

                              {/* Options */}
                              <div className="space-y-2 ml-10">
                                {['option_a', 'option_b', 'option_c', 'option_d'].map((optKey, optIndex) => {
                                  const optionLabel = ['A', 'B', 'C', 'D'][optIndex];
                                  const optionText = mcq[optKey];
                                  const isSelected = selectedOption === optIndex;
                                  const isCorrectOption = quizResult && correctOptionIndex === optIndex;
                                  const isWrongSelection = quizResult && isSelected && !isCorrect;

                                  return (
                                    <button
                                      key={optKey}
                                      onClick={() => handleAnswerSelect(mcq.id, optIndex)}
                                      disabled={!!quizResult}
                                      className={`w-full flex items-center gap-3 p-3 rounded-lg border text-left transition-all ${
                                        quizResult
                                          ? isCorrectOption
                                            ? 'bg-emerald-500/10 border-emerald-500 text-emerald-700 dark:text-emerald-400'
                                            : isWrongSelection
                                            ? 'bg-red-500/10 border-red-500 text-red-700 dark:text-red-400'
                                            : 'border-border text-muted-foreground'
                                          : isSelected
                                          ? 'bg-primary/10 border-primary text-primary'
                                          : 'border-border hover:border-primary/50 hover:bg-muted/50'
                                      }`}
                                    >
                                      <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
                                        quizResult
                                          ? isCorrectOption
                                            ? 'bg-emerald-500 text-white'
                                            : isWrongSelection
                                            ? 'bg-red-500 text-white'
                                            : 'bg-muted text-muted-foreground'
                                          : isSelected
                                          ? 'bg-primary text-primary-foreground'
                                          : 'bg-muted text-muted-foreground'
                                      }`}>
                                        {quizResult && isCorrectOption ? (
                                          <CheckCircle className="w-4 h-4" />
                                        ) : quizResult && isWrongSelection ? (
                                          <X className="w-4 h-4" />
                                        ) : (
                                          optionLabel
                                        )}
                                      </span>
                                      <span className="flex-1">{optionText}</span>
                                    </button>
                                  );
                                })}
                              </div>

                              {/* Explanation */}
                              {showExplanations && resultForMcq?.explanation && (
                                <motion.div
                                  initial={{ opacity: 0, height: 0 }}
                                  animate={{ opacity: 1, height: 'auto' }}
                                  className="mt-4 ml-10 p-3 bg-muted/50 rounded-lg border border-border"
                                >
                                  <p className="text-sm text-muted-foreground">
                                    <span className="font-medium text-foreground">Explanation: </span>
                                    {resultForMcq.explanation}
                                  </p>
                                </motion.div>
                              )}
                            </motion.div>
                          );
                        })}
                      </div>

                      {/* Submit/Retake Button */}
                      <div className="flex items-center justify-center gap-4 pt-4">
                        {quizResult ? (
                          <Button onClick={retakeQuiz} variant="outline" className="gap-2">
                            <RefreshCw className="w-4 h-4" />
                            Retake Quiz
                          </Button>
                        ) : (
                          <Button
                            onClick={submitQuiz}
                            disabled={isSubmittingQuiz || Object.keys(selectedAnswers).length === 0}
                            className="gap-2 min-w-[150px]"
                          >
                            {isSubmittingQuiz ? (
                              <LoadingSpinner size="sm" />
                            ) : (
                              <>
                                <CheckCircle className="w-4 h-4" />
                                Submit Quiz
                              </>
                            )}
                          </Button>
                        )}
                      </div>

                      {/* Progress indicator */}
                      {!quizResult && (
                        <div className="text-center text-sm text-muted-foreground">
                          {Object.keys(selectedAnswers).length} of {(quiz.questions || quiz.mcqs)?.length || quiz.total_questions} questions answered
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-center py-12 text-muted-foreground">
                      <Brain className="w-12 h-12 mx-auto mb-4 opacity-50" />
                      <p className="mb-2">No quiz available for this lesson yet</p>
                      <p className="text-xs">Quizzes are auto-generated after lesson content is processed</p>
                    </div>
                  )}
                </TabsContent>
              </Tabs>

              {/* Navigation */}
              <div className="flex items-center justify-between mt-12 pt-6 border-t border-border">
                {lesson.prev_lesson ? (
                  <Button variant="outline" onClick={goToPreviousLesson}>
                    <ChevronLeft className="w-4 h-4 mr-2" />
                    <span className="hidden sm:inline">Previous:</span>{' '}
                    <span className="truncate max-w-[150px]">
                      {lesson.prev_lesson.title}
                    </span>
                  </Button>
                ) : (
                  <div />
                )}

                {lesson.next_lesson ? (
                  <Button
                    onClick={goToNextLesson}
                    className="bg-primary hover:bg-primary/90"
                  >
                    <span className="hidden sm:inline">Next:</span>{' '}
                    <span className="truncate max-w-[150px]">
                      {lesson.next_lesson.title}
                    </span>
                    <ChevronRight className="w-4 h-4 ml-2" />
                  </Button>
                ) : (
                  <Link to={`/learn/courses/${courseSlug}`}>
                    <Button className="bg-emerald-600 hover:bg-emerald-700">
                      <CheckCircle className="w-4 h-4 mr-2" />
                      Complete Course
                    </Button>
                  </Link>
                )}
              </div>

              {/* Keyboard Shortcuts Hint */}
              <div className="mt-8 p-4 bg-muted/50 border border-border rounded-lg">
                <p className="text-xs text-muted-foreground text-center">
                  <span className="font-medium">Keyboard shortcuts:</span>{' '}
                  <kbd className="px-1.5 py-0.5 bg-background border rounded text-[10px] mx-1">
                    S
                  </kbd>{' '}
                  Toggle sidebar •{' '}
                  <kbd className="px-1.5 py-0.5 bg-background border rounded text-[10px] mx-1">
                    M
                  </kbd>{' '}
                  Mark complete •{' '}
                  <kbd className="px-1.5 py-0.5 bg-background border rounded text-[10px] mx-1">
                    Ctrl+←/→
                  </kbd>{' '}
                  Navigate lessons
                </p>
              </div>
            </div>
          </div>
        </main>
      </div>
    </Layout>
  );
}
