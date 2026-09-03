import { useEffect, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import Layout from '../components/Layout';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorState from '../components/ErrorState';
import { Button } from '../components/ui/button';
import { useTracker } from '../hooks/useTracker';
import { useLearner } from '../contexts/LearnerContext';
import { Events } from '../api/trackingApi';
import { findLessonById, getLessonDetail } from '../api/coursesApi';
import { getPersonalisedRecommendations } from '../api/recommendationsApi';

export default function LessonDetail() {
  const { id } = useParams();
  const { track } = useTracker();
  const { refetch } = useLearner();
  const [lesson, setLesson] = useState(null);
  const [courseSlug, setCourseSlug] = useState(null);
  const [videoStarted, setVideoStarted] = useState(false);
  const [error, setError] = useState(null);
  const [nextStep, setNextStep] = useState(null);
  const [showNextStep, setShowNextStep] = useState(false);
  const [completed, setCompleted] = useState(false);
  const startTimeRef = useRef(Date.now());
  const navigate = useNavigate();

  useEffect(() => {
    let mounted = true;

    (async () => {
      try {
        setError(null);
        const resolved = await findLessonById(id);
        if (!resolved) {
          if (mounted) setError('Lesson not found');
          return;
        }

        const detailRes = await getLessonDetail(resolved.course.slug, resolved.lesson.slug);
        if (!mounted) return;

        setCourseSlug(resolved.course.slug);
        setLesson({
          ...detailRes.data,
          course_title: resolved.course.title,
          concept_tag: resolved.lesson.concept_tag,
          difficulty: resolved.lesson.difficulty || resolved.course.level,
        });
        track(Events.LESSON_OPENED, 'lesson', Number(id), {
          concept_tag: resolved.lesson.concept_tag,
        });
        startTimeRef.current = Date.now();
      } catch {
        if (mounted) setError('Failed to load lesson');
      }
    })();

    return () => {
      mounted = false;
    };
  }, [id, track]);

  const handleMarkComplete = async () => {
    if (completed) return;
    setCompleted(true);
    track(Events.LESSON_COMPLETED, 'lesson', Number(id), {
      time_spent_seconds: Math.round((Date.now() - startTimeRef.current) / 1000),
      concept_tag: lesson?.concept_tag,
    });
    try {
      await refetch();
      const result = await getPersonalisedRecommendations();
      const top = result?.data?.recommendations?.[0];
      if (top) {
        setNextStep(top);
        setShowNextStep(true);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleVideoStart = () => {
    if (!videoStarted) {
      setVideoStarted(true);
      track(Events.VIDEO_STARTED, 'video', Number(id));
    }
  };

  if (error) {
    return (
      <Layout>
        <ErrorState message={error} onRetry={() => window.location.reload()} />
      </Layout>
    );
  }

  if (!lesson) {
    return (
      <Layout>
        <LoadingSpinner text="Loading lesson..." />
      </Layout>
    );
  }

  const ytId =
    lesson.youtube_id ||
    (() => {
      const url = lesson.video_url || lesson.embed_url;
      if (!url) return null;
      const match = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)/);
      return match?.[1];
    })();

  const embedUrl = lesson.embed_url || (ytId ? `https://www.youtube.com/embed/${ytId}?enablejsapi=1` : null);

  return (
    <Layout>
      <div className="min-h-screen bg-[#0a0a0a] text-white">
        <div className="max-w-5xl mx-auto px-6 py-10">
          <nav className="text-sm text-gray-500 mb-6 flex items-center gap-2">
            <button
              type="button"
              onClick={() => navigate('/learn')}
              className="hover:text-[#E8392A] transition-colors"
            >
              Learn
            </button>
            <span>/</span>
            {courseSlug && (
              <>
                <button
                  type="button"
                  onClick={() => navigate(`/learn/courses/${courseSlug}`)}
                  className="hover:text-[#E8392A] transition-colors"
                >
                  {lesson.course_title || 'Course'}
                </button>
                <span>/</span>
              </>
            )}
            <span className="text-gray-300">{lesson.title}</span>
          </nav>

          <div className="mb-6">
            <div className="flex items-center gap-3 mb-3 flex-wrap">
              {lesson.concept_tag && (
                <span className="text-xs px-3 py-1 rounded-full border border-[#E8392A]/40 text-[#E8392A] capitalize">
                  {lesson.concept_tag.replace(/_/g, ' ')}
                </span>
              )}
              {lesson.difficulty && (
                <span
                  className={`text-xs px-3 py-1 rounded-full border capitalize ${
                    lesson.difficulty === 'advanced'
                      ? 'border-red-800 text-red-400'
                      : lesson.difficulty === 'intermediate'
                        ? 'border-yellow-800 text-yellow-400'
                        : 'border-green-800 text-green-400'
                  }`}
                >
                  {lesson.difficulty}
                </span>
              )}
              {lesson.duration_minutes && (
                <span className="text-xs text-gray-500">⏱ {lesson.duration_minutes} min</span>
              )}
            </div>
            <h1 className="text-3xl font-bold">{lesson.title}</h1>
          </div>

          {embedUrl ? (
            <div
              className="relative w-full mb-4 rounded-xl overflow-hidden border border-[#222]"
              style={{ paddingBottom: '56.25%' }}
              onClick={handleVideoStart}
              role="presentation"
            >
              <iframe
                className="absolute inset-0 w-full h-full"
                src={embedUrl}
                title={lesson.title}
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            </div>
          ) : (
            <div className="w-full h-64 bg-[#111] border border-[#222] rounded-xl flex items-center justify-center mb-4">
              <p className="text-gray-500">No video available for this lesson</p>
            </div>
          )}

          <div className="mt-4 flex justify-end mb-8">
            <Button
              onClick={handleMarkComplete}
              disabled={completed}
              className="bg-[#E8392A] hover:bg-[#c72d21]"
            >
              {completed ? 'Completed ✓' : 'Mark Complete ✓'}
            </Button>
          </div>

          {lesson.notes && (
            <div className="prose prose-invert max-w-none mb-8">
              <p className="text-gray-300 leading-relaxed whitespace-pre-wrap">{lesson.notes}</p>
            </div>
          )}

          {lesson.description && (
            <div className="prose prose-invert max-w-none mb-8">
              <p className="text-gray-300 leading-relaxed">{lesson.description}</p>
            </div>
          )}

          <div className="bg-[#111] border border-[#E8392A]/20 rounded-xl p-6 flex items-center justify-between flex-wrap gap-4">
            <div>
              <h3 className="font-semibold">Test your understanding</h3>
              <p className="text-sm text-gray-400 mt-1">Take the lesson quiz to update your mastery</p>
            </div>
            <button
              type="button"
              onClick={() => navigate(`/quiz/${id}`)}
              className="bg-[#E8392A] hover:bg-[#c42d1f] text-white px-6 py-2.5 rounded-lg font-medium transition-colors"
            >
              Take quiz →
            </button>
          </div>
        </div>
      </div>

      <AnimatePresence>
        {showNextStep && nextStep && (
          <motion.div
            initial={{ opacity: 0, y: 60 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 60 }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            className="fixed bottom-0 left-0 right-0 z-50 p-6 bg-[#111] border-t border-[#222] shadow-2xl"
          >
            <div className="max-w-3xl mx-auto flex items-center justify-between gap-6">
              <div className="min-w-0">
                <p className="text-xs text-[#E8392A] font-semibold uppercase tracking-widest mb-1">
                  Your Next Step
                </p>
                <h3 className="text-xl font-bold text-white truncate">{nextStep.title}</h3>
                <p className="text-gray-400 text-sm mt-1 line-clamp-2">{nextStep.explanation}</p>
                <span className="inline-block mt-2 text-xs bg-[#E8392A]/10 text-[#E8392A] border border-[#E8392A]/20 px-2 py-0.5 rounded-full">
                  {nextStep.why_badge}
                </span>
              </div>
              <div className="flex gap-3 shrink-0">
                <Button variant="outline" onClick={() => setShowNextStep(false)}>
                  Later
                </Button>
                <Button
                  onClick={() => navigate(`/learn/lessons/${nextStep.content_id}`)}
                  className="bg-[#E8392A] hover:bg-[#c72d21]"
                >
                  Start now →
                </Button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </Layout>
  );
}
