import { useState, useEffect, useMemo } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BookOpen,
  Clock,
  Play,
  Search,
  Star,
  Users,
  Lock,
  Filter,
  ChevronDown,
  GraduationCap,
  TrendingUp,
  Check,
  Sparkles,
} from 'lucide-react';
import Layout from '../components/Layout';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorState from '../components/ErrorState';
import EmptyState from '../components/EmptyState';
import api from '../api/axios';
import { useAuth } from '../contexts/AuthContext';
import { useLearner } from '../contexts/LearnerContext';
import RecommendationCard from '../components/dashboard/RecommendationCard';
import { getPersonalizedLearn } from '../api/recommendationsApi';
import { formatINR } from '../lib/currency';
import { getCourseVisual } from '../lib/courseVisuals';

// Animation variants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.08 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.4, ease: 'easeOut' },
  },
};

/**
 * Premium Course Card Component
 * Clean, professional design with all key metrics visible
 */
function CourseCard({ course, userRating, masteryPercent, isWeak, isRecommended }) {
  const visual = getCourseVisual(course.title, course.thumbnail);
  const isPaid = course.is_paid === true || parseFloat(course.price || 0) > 0;
  const isFree = course.is_free === true || parseFloat(course.price || 0) === 0;
  const isEnrolled = course.is_enrolled === true;
  const requiredRating = course.required_rating || 0;
  const isLocked = requiredRating > 0 && (userRating || 0) < requiredRating;

  // Format price display
  const priceDisplay = isPaid
    ? formatINR(course.price)
    : 'Free';

  // Format duration
  const formatDuration = (hours) => {
    if (!hours) return '0h';
    const h = Math.floor(hours);
    const m = Math.round((hours - h) * 60);
    return m > 0 ? `${h}h ${m}m` : `${h}h`;
  };

  return (
    <motion.div variants={itemVariants}>
      <Link
        to={isLocked ? '#' : `/learn/courses/${course.slug}`}
        onClick={(e) => isLocked && e.preventDefault()}
        className={`group block h-full ${isLocked ? 'cursor-not-allowed' : ''}`}
      >
        <div
          className={`h-full bg-card border border-border rounded-xl overflow-hidden transition-all duration-300 ${
            isLocked
              ? 'opacity-60'
              : 'hover:border-primary/50 hover:shadow-lg hover:shadow-primary/5'
          }`}
        >
          {/* Thumbnail */}
          <div className="relative aspect-[16/9] bg-muted overflow-hidden">
            {visual.src ? (
              <img
                src={visual.src}
                alt={course.title}
                className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                loading="lazy"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-primary/10 to-primary/5">
                <BookOpen className="w-12 h-12 text-primary/40" />
              </div>
            )}

            {/* Lock Overlay */}
            {isLocked && (
              <div className="absolute inset-0 bg-background/80 backdrop-blur-sm flex flex-col items-center justify-center">
                <Lock className="w-8 h-8 text-muted-foreground mb-2" />
                <span className="text-sm font-medium text-muted-foreground">
                  {requiredRating}+ rating required
                </span>
              </div>
            )}

            {/* Top Badges */}
            <div className="absolute top-3 left-3 right-3 flex justify-between items-start">
              {/* Track Badge */}
              {course.track && (
                <Badge
                  variant="secondary"
                  className="bg-background/90 backdrop-blur-sm text-xs font-medium"
                >
                    {course.track.title || course.track.name || course.track}
                </Badge>
              )}

              <div className="flex flex-col items-end gap-2">
                {isRecommended && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: 'spring', stiffness: 300 }}
                    className="bg-[#E8392A] text-white text-xs px-2 py-0.5 rounded-full flex items-center gap-1"
                  >
                    <Sparkles className="w-3 h-3" /> For You
                  </motion.div>
                )}

                <Badge
                  className={`${
                    isFree
                      ? 'bg-emerald-500/90 hover:bg-emerald-500'
                      : 'bg-primary/90 hover:bg-primary'
                  } text-white font-semibold px-3 py-1`}
                >
                  {priceDisplay}
                </Badge>
              </div>
            </div>

            {/* Enrolled Indicator */}
            {isEnrolled && (
              <div className="absolute bottom-3 left-3">
                <Badge
                  variant="secondary"
                  className="bg-emerald-500/90 text-white text-xs"
                >
                  <Check className="w-3 h-3 mr-1" />
                  Enrolled
                </Badge>
              </div>
            )}
          </div>

          {/* Content */}
          <div className="p-5">
            {/* Difficulty & Level */}
            <div className="flex items-center gap-2 mb-3">
              <Badge
                variant="outline"
                className={`text-xs capitalize ${
                  course.difficulty === 'advanced'
                    ? 'border-red-500/50 text-red-500'
                    : course.difficulty === 'intermediate'
                    ? 'border-amber-500/50 text-amber-500'
                    : 'border-emerald-500/50 text-emerald-500'
                }`}
              >
                {course.difficulty || 'Beginner'}
              </Badge>

              {/* Rating */}
              {course.rating_avg > 0 && (
                <div className="flex items-center gap-1 text-xs">
                  <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
                  <span className="font-medium">
                    {course.rating_avg?.toFixed(1)}
                  </span>
                  <span className="text-muted-foreground">
                    ({course.rating_count || 0})
                  </span>
                </div>
              )}
            </div>

            {/* Title */}
            <h3 className="font-semibold text-base text-foreground mb-2 line-clamp-2 group-hover:text-primary transition-colors">
              {course.title}
            </h3>

            {/* Description */}
            <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
              {course.description}
            </p>

            {masteryPercent != null && (
              <div className="mb-4">
                <div className="flex items-center justify-between text-xs mb-1.5">
                  <span className="text-muted-foreground capitalize">
                    {(course.concept_tag || 'concept').replace(/_/g, ' ')} mastery
                  </span>
                  <span className={isWeak ? 'text-amber-500 font-medium' : 'text-muted-foreground'}>
                    {Math.round(masteryPercent * 100)}%
                    {isWeak ? ' · focus area' : ''}
                  </span>
                </div>
                <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${isWeak ? 'bg-amber-500' : 'bg-primary'}`}
                    style={{ width: `${Math.min(100, masteryPercent * 100)}%` }}
                  />
                </div>
              </div>
            )}

            {/* Stats Footer */}
            <div className="flex items-center justify-between pt-4 border-t border-border text-xs text-muted-foreground">
              <div className="flex items-center gap-4">
                <span className="flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5" />
                  {formatDuration(course.total_duration_hours || course.duration_hours)}
                </span>
                <span className="flex items-center gap-1.5">
                  <Play className="w-3.5 h-3.5" />
                  {course.total_lessons || course.lesson_count || 0} lessons
                </span>
              </div>

              <span className="flex items-center gap-1.5">
                <Users className="w-3.5 h-3.5" />
                {course.students_count || course.enrollment_count || 0}
              </span>
            </div>
          </div>
        </div>
      </Link>
    </motion.div>
  );
}
/**
 * Personalized Learn panel (Phase 3).
 * Surfaces the sections produced by GET /api/learn/recommendations/
 * (build_personalized_learn_response) with each recommendation's short reason.
 */

function LessonItemCard({ item, reasonLabel }) {
  const navigate = useNavigate();
  const lesson = item.lesson || item;
  const lessonId = lesson?.id ?? item.id;
  const reason = item.reason || 'Recommended based on your learning progress.';
  const progress = item.progress_percent;

  const handleClick = () => {
    const courseSlug = lesson?.course_slug || item.course_slug;
    const slug = lesson?.slug;
    if (courseSlug && slug) {
      navigate(`/learn/courses/${courseSlug}/lessons/${slug}`);
    } else if (lessonId) {
      navigate(`/learn/lesson/${lessonId}`);
    }
  };

  return (
    <motion.div variants={itemVariants}>
      <div
        onClick={handleClick}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && handleClick()}
        className="bg-[#111] border border-[#222] rounded-xl p-4 cursor-pointer hover:border-[#E8392A]/40 transition-colors h-full flex flex-col"
      >
        <div className="flex items-center justify-between mb-2">
          <span className="text-[10px] uppercase tracking-wide text-[#E8392A]/80 font-semibold">
            {reasonLabel}
          </span>
          {typeof progress === 'number' && (
            <span className="text-xs text-green-400 font-medium">{progress}%</span>
          )}
        </div>
        <p className="text-white text-sm font-medium line-clamp-2 mb-1">
          {lesson?.title || item.title}
        </p>
        {lesson?.concept_tag && (
          <p className="text-xs text-gray-500 mb-2 capitalize">
            {lesson.concept_tag.replace(/_/g, ' ')}
          </p>
        )}
        <p className="text-xs text-gray-500 italic line-clamp-2 mt-auto">
          &ldquo;{reason}&rdquo;
        </p>
      </div>
    </motion.div>
  );
}

function PersonalizedLearnPanel() {
  const [payload, setPayload] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;
    getPersonalizedLearn()
      .then((data) => mounted && setPayload(data))
      .catch((err) => mounted && setError(err));
    return () => {
      mounted = false;
    };
  }, []);

  if (error) return null;
  if (!payload) return null;

  const hasAny =
    (payload.continue_learning || []).length ||
    (payload.recommended_for_you || []).length ||
    (payload.missing_prerequisites || []).length ||
    (payload.strengthen_weak_areas || []).length;

  if (!hasAny) return null;

  const renderGrid = (items, reasonLabel) => (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
    >
      {items.map((item) => (
        <LessonItemCard
          key={`${reasonLabel}-${item.id ?? item.lesson?.id}`}
          item={item}
          reasonLabel={reasonLabel}
        />
      ))}
    </motion.div>
  );

  const nextBest = payload.next_best_lesson;
  const sectionClass = 'mb-8';

  return (
    <div className="mb-12">
      {/* Next Best Lesson */}
      <div className={`${sectionClass} bg-[#0d0d0d] border border-[#222] rounded-2xl p-5`}>
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[#E8392A]" />
          Next Best Lesson
        </h2>
        <div className="md:grid md:grid-cols-2 gap-4">
          <LessonItemCard item={nextBest} reasonLabel={nextBest?.reason_code || 'Next'} />
        </div>
      </div>

      {/* Continue Learning */}
      {(payload.continue_learning || []).length > 0 && (
        <div className={sectionClass}>
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-green-500" />
            Continue Learning
          </h2>
          {renderGrid(payload.continue_learning, 'Continue')}
        </div>
      )}

      {/* Complete These First */}
      {(payload.missing_prerequisites || []).length > 0 && (
        <div className={sectionClass}>
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-amber-500" />
            Complete These First
          </h2>
          {renderGrid(payload.missing_prerequisites, 'Prerequisite')}
        </div>
      )}

      {/* Strengthen Weak Areas */}
      {(payload.strengthen_weak_areas || []).length > 0 && (
        <div className={sectionClass}>
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-red-500" />
            Strengthen Weak Areas
          </h2>
          {renderGrid(payload.strengthen_weak_areas, 'Weak Area')}
        </div>
      )}
    </div>
  );
}

/**
 * Learn Page - Premium Course Catalog
 * Elite ML Engineering Academy experience
 */
export default function Learn() {
  const { user, isAuthenticated } = useAuth();
  const { recommendations, modelVersion, learnerAbility, isPersonalised, profile, getMasteryForConcept, isWeakConcept } = useLearner();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const conceptFilter = searchParams.get('concept');
  const [activeTab, setActiveTab] = useState('all');
  const [courses, setCourses] = useState([]);
  const [tracks, setTracks] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('all'); // all, free, paid
  const [filterLevel, setFilterLevel] = useState('all'); // all, beginner, intermediate, advanced
  const [filterTrack, setFilterTrack] = useState('all');
  const [sortBy, setSortBy] = useState(isAuthenticated ? 'relevance' : 'newest');

  // User's rating for lock checking
  const userRating = user?.rating || 0;

  useEffect(() => {
    fetchCourses();
    fetchTracks();
  }, []);

  const fetchCourses = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await api.get('/api/learn/courses/');
      const data = response.data;
      setCourses(Array.isArray(data) ? data : data.results || []);
    } catch (err) {
      if (err.response?.status !== 401) {
        setError(
          err.response?.data?.message ||
            err.response?.data?.detail ||
            'Failed to load courses'
        );
      }
      setCourses([]);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchTracks = async () => {
    try {
      const response = await api.get('/api/tracks/');
      const data = response.data;
      setTracks(Array.isArray(data) ? data : data.results || []);
    } catch (err) {
      console.error('Failed to fetch tracks:', err);
    }
  };

  const mlRecs = recommendations.slice(0, 5);
  const recIds = useMemo(
    () => new Set(recommendations.map((r) => r.content_id)),
    [recommendations]
  );
  const recCourseIds = useMemo(
    () => new Set(recommendations.map((r) => r.course_id).filter(Boolean)),
    [recommendations]
  );

  const tabs = [
    { id: 'all', label: 'All Courses' },
    { id: 'for-you', label: 'For You' },
    { id: 'weak-areas', label: 'Weak Areas' },
  ];

  // Filter and sort courses
  const filteredCourses = useMemo(() => {
    let result = [...courses];

    if (activeTab === 'for-you') {
      result = result.filter((c) => recIds.has(c.id) || recCourseIds.has(c.id));
    } else if (activeTab === 'weak-areas') {
      result = result.filter((c) => profile?.weak_concepts?.includes(c.concept_tag));
    }

    if (conceptFilter) {
      result = result.filter((c) =>
        (c.tags || []).some(
          (tag) => String(tag).toLowerCase().replace(/\s+/g, '_') === conceptFilter
        )
      );
    }

    // Search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (c) =>
          c.title?.toLowerCase().includes(query) ||
          c.description?.toLowerCase().includes(query)
      );
    }

    // Type filter (free/paid)
    if (filterType === 'free') {
      result = result.filter(
        (c) => c.is_free === true || parseFloat(c.price || 0) === 0
      );
    } else if (filterType === 'paid') {
      result = result.filter(
        (c) => c.is_paid === true || parseFloat(c.price || 0) > 0
      );
    }

    // Difficulty filter
    if (filterLevel !== 'all') {
      result = result.filter(
        (c) => c.difficulty?.toLowerCase() === filterLevel.toLowerCase()
      );
    }

    // Track filter
    if (filterTrack !== 'all') {
      result = result.filter((c) => {
        const trackId = c.track?.id || c.track;
        return String(trackId) === String(filterTrack);
      });
    }

    // Sort
    switch (sortBy) {
      case 'relevance':
        if (isAuthenticated) {
          result.sort((a, b) => {
            const tagA = a.concept_tag || '';
            const tagB = b.concept_tag || '';
            const isWeakA = isWeakConcept(tagA) ? 1 : 0;
            const isWeakB = isWeakConcept(tagB) ? 1 : 0;
            if (isWeakA !== isWeakB) return isWeakB - isWeakA;
            return getMasteryForConcept(tagA) - getMasteryForConcept(tagB);
          });
        }
        break;
      case 'popular':
        result.sort(
          (a, b) =>
            (b.students_count || b.enrollment_count || 0) -
            (a.students_count || a.enrollment_count || 0)
        );
        break;
      case 'rating':
        result.sort((a, b) => (b.rating_avg || 0) - (a.rating_avg || 0));
        break;
      case 'newest':
      default:
        result.sort(
          (a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0)
        );
        break;
    }

    return result;
  }, [courses, searchQuery, filterType, filterLevel, filterTrack, sortBy, conceptFilter, isAuthenticated, getMasteryForConcept, isWeakConcept, activeTab, recIds, recCourseIds, profile]);

  // Stats for hero section
  const stats = useMemo(() => {
    return {
      totalCourses: courses.length,
      freeCourses: courses.filter(
        (c) => c.is_free || parseFloat(c.price || 0) === 0
      ).length,
      totalLessons: courses.reduce(
        (acc, c) => acc + (c.total_lessons || c.lesson_count || 0),
        0
      ),
      totalHours: courses.reduce(
        (acc, c) =>
          acc + (c.total_duration_hours || c.duration_hours || 0),
        0
      ),
    };
  }, [courses]);

  const clearFilters = () => {
    setSearchQuery('');
    setFilterType('all');
    setFilterLevel('all');
    setFilterTrack('all');
    setSortBy('newest');
  };

  const hasActiveFilters =
    searchQuery ||
    filterType !== 'all' ||
    filterLevel !== 'all' ||
    filterTrack !== 'all';

  return (
    <Layout>
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-b from-background via-background to-muted/30 border-b border-border">
        <div className="absolute inset-0 bg-grid-pattern opacity-5" />
        <div className="container mx-auto px-4 lg:px-8 py-16 lg:py-20 relative">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="max-w-3xl"
          >
            <div className="flex items-center gap-2 mb-4">
              <GraduationCap className="w-6 h-6 text-primary" />
              <span className="text-sm font-medium text-primary uppercase tracking-wider">
                ML Engineering Academy
              </span>
            </div>

            <h1 className="text-4xl lg:text-5xl font-bold text-foreground mb-4 tracking-tight">
              Master Machine Learning
            </h1>

            <p className="text-lg lg:text-xl text-muted-foreground mb-8 leading-relaxed">
              Structured video courses designed for aspiring ML engineers.
              From fundamentals to production-ready skills.
            </p>

            {/* Stats */}
            <div className="flex flex-wrap items-center gap-6 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                  <BookOpen className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <p className="font-semibold text-foreground">
                    {stats.totalCourses}
                  </p>
                  <p className="text-muted-foreground text-xs">Courses</p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                  <Play className="w-5 h-5 text-emerald-500" />
                </div>
                <div>
                  <p className="font-semibold text-foreground">
                    {stats.totalLessons}+
                  </p>
                  <p className="text-muted-foreground text-xs">Lessons</p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <div className="w-10 h-10 rounded-lg bg-amber-500/10 flex items-center justify-center">
                  <Clock className="w-5 h-5 text-amber-500" />
                </div>
                <div>
                  <p className="font-semibold text-foreground">
                    {Math.round(stats.totalHours)}h
                  </p>
                  <p className="text-muted-foreground text-xs">Content</p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                  <Sparkles className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <p className="font-semibold text-foreground">
                    {stats.freeCourses}
                  </p>
                  <p className="text-muted-foreground text-xs">Free Courses</p>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Main Content */}
      <section className="container mx-auto px-4 lg:px-8 py-10">
        {isAuthenticated && (
          <>
            <div className="flex gap-1 p-1 bg-[#111] rounded-xl border border-[#222] w-fit mb-6">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setActiveTab(tab.id)}
                  className={`relative px-4 py-2 text-sm rounded-lg transition-colors z-10 ${
                    activeTab === tab.id ? 'text-white' : 'text-gray-400 hover:text-white'
                  }`}
                >
                  {activeTab === tab.id && (
                    <motion.div
                      layoutId="learnTab"
                      className="absolute inset-0 bg-[#E8392A]/20 rounded-lg border border-[#E8392A]/30"
                      style={{ zIndex: -1 }}
                    />
                  )}
                  {tab.label}
                </button>
              ))}
            </div>

            {mlRecs.length > 0 && (
              <div className="flex gap-3 overflow-x-auto pb-2 mb-4 scrollbar-hide">
                {mlRecs.map((rec, i) => (
                  <motion.div
                    key={rec.content_id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.07 }}
                    className="shrink-0 w-52 bg-[#111] border border-[#222] rounded-xl p-4 cursor-pointer hover:border-[#E8392A]/40 transition-colors"
                    onClick={() => navigate(`/learn/lessons/${rec.content_id}`)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => e.key === 'Enter' && navigate(`/learn/lessons/${rec.content_id}`)}
                  >
                    <p className="text-white text-sm font-medium line-clamp-2 mb-2">{rec.title}</p>
                    <span className="text-xs bg-[#E8392A]/10 text-[#E8392A] px-2 py-0.5 rounded-full">
                      {rec.why_badge}
                    </span>
                    {rec.mastery_after != null && (
                      <p className="text-xs text-green-400 mt-2">
                        +{(rec.mastery_after * 100).toFixed(0)}% projected
                      </p>
                    )}
                  </motion.div>
                ))}
              </div>
            )}
          </>
        )}

        {isAuthenticated && (
          <div className="mb-10">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[#E8392A]" />
              Recommended for you
            </h2>
            {modelVersion && (
              <div className="flex flex-wrap items-center gap-3 mb-4 text-xs text-gray-600">
                <span className="inline-flex items-center gap-2">
                  <span
                    className={`w-2 h-2 rounded-full ${
                      modelVersion.includes('lgbm') ? 'bg-green-500' : 'bg-amber-500'
                    }`}
                  />
                  {modelVersion.includes('lgbm')
                    ? 'Powered by trained ML model'
                    : 'Rule-based recommendations (ML model training in progress)'}
                </span>
                <span className="inline-flex items-center gap-2">
                  <span className="font-semibold text-foreground">Ability</span>
                  {Math.round((learnerAbility || 0) * 100)}%
                </span>
                <span className="inline-flex items-center gap-2">
                  {isPersonalised ? 'Personalised learning active' : 'Personalisation is initializing'}
                </span>
              </div>
            )}
            {mlRecs.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {mlRecs.map((rec) => (
                  <RecommendationCard key={`${rec.content_type}-${rec.content_id || rec.id}`} rec={rec} />
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500 italic">
                Start learning to unlock personalized recommendations
              </p>
            )}
          </div>
        )}
{/* Phase 3: Personalized Learn — Continue / Complete These First / Weak Areas / Next Best */}
        {isAuthenticated && <PersonalizedLearnPanel />}

        {conceptFilter && (
          <div className="mb-6 text-sm text-muted-foreground">
            Showing courses related to{' '}
            <span className="text-primary capitalize">{conceptFilter.replace(/_/g, ' ')}</span>
          </div>
        )}

        {/* Filters Bar */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mb-8"
        >
          <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-center justify-between">
            {/* Search */}
            <div className="relative w-full lg:w-80">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search courses..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 h-10 bg-card"
              />
            </div>

            {/* Filter Controls */}
            <div className="flex flex-wrap items-center gap-3">
              {/* Type Filter */}
              <div className="flex items-center rounded-lg border border-border bg-card p-1">
                {['all', 'free', 'paid'].map((type) => (
                  <button
                    key={type}
                    onClick={() => setFilterType(type)}
                    className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                      filterType === type
                        ? 'bg-primary text-primary-foreground'
                        : 'text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    {type === 'all' ? 'All' : type === 'free' ? 'Free' : 'Premium'}
                  </button>
                ))}
              </div>

              {/* Level Filter */}
              <Select value={filterLevel} onValueChange={setFilterLevel}>
                <SelectTrigger className="w-[140px] h-10 bg-card">
                  <SelectValue placeholder="Level" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Levels</SelectItem>
                  <SelectItem value="beginner">Beginner</SelectItem>
                  <SelectItem value="intermediate">Intermediate</SelectItem>
                  <SelectItem value="advanced">Advanced</SelectItem>
                </SelectContent>
              </Select>

              {/* Track Filter */}
              {tracks.length > 0 && (
                <Select value={filterTrack} onValueChange={setFilterTrack}>
                  <SelectTrigger className="w-[160px] h-10 bg-card">
                    <SelectValue placeholder="Track" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Tracks</SelectItem>
                    {tracks.map((track) => (
                      <SelectItem key={track.id} value={String(track.id)}>
                        {track.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}

              {/* Sort */}
              <Select value={sortBy} onValueChange={setSortBy}>
                <SelectTrigger className="w-[130px] h-10 bg-card">
                  <SelectValue placeholder="Sort" />
                </SelectTrigger>
                <SelectContent>
                  {isAuthenticated && (
                    <SelectItem value="relevance">For You</SelectItem>
                  )}
                  <SelectItem value="newest">Newest</SelectItem>
                  <SelectItem value="popular">Popular</SelectItem>
                  <SelectItem value="rating">Top Rated</SelectItem>
                </SelectContent>
              </Select>

              {/* Clear Filters */}
              {hasActiveFilters && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearFilters}
                  className="text-muted-foreground hover:text-foreground"
                >
                  Clear
                </Button>
              )}
            </div>
          </div>

          {/* Active Filters Summary */}
          {hasActiveFilters && (
            <div className="mt-4 flex items-center gap-2 text-sm text-muted-foreground">
              <Filter className="w-4 h-4" />
              <span>
                Showing {filteredCourses.length} of {courses.length} courses
              </span>
            </div>
          )}
        </motion.div>

        {/* Course Grid */}
        {isLoading ? (
          <div className="min-h-[40vh] flex items-center justify-center">
            <LoadingSpinner text="Loading courses..." />
          </div>
        ) : error ? (
          <ErrorState message={error} onRetry={fetchCourses} />
        ) : filteredCourses.length === 0 ? (
          <EmptyState
            icon={BookOpen}
            title={hasActiveFilters ? 'No courses match your filters' : 'No courses available'}
            description={
              hasActiveFilters
                ? 'Try adjusting your filters or search query'
                : 'Check back soon for new courses'
            }
            action={
              hasActiveFilters && (
                <Button variant="outline" onClick={clearFilters}>
                  Clear Filters
                </Button>
              )
            }
          />
        ) : (
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
          >
            {filteredCourses.map((course) => (
              <CourseCard
                key={course.id || course.slug}
                course={course}
                userRating={userRating}
                masteryPercent={
                  isAuthenticated && course.concept_tag
                    ? getMasteryForConcept(course.concept_tag)
                    : null
                }
                isWeak={isAuthenticated && isWeakConcept(course.concept_tag)}
                isRecommended={
                  isAuthenticated &&
                  (recIds.has(course.id) || recCourseIds.has(course.id))
                }
              />
            ))}
          </motion.div>
        )}

        {/* Rating Requirement Notice */}
        {userRating > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="mt-12 p-4 bg-muted/50 border border-border rounded-lg"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-amber-500/10 flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-amber-500" />
              </div>
              <div>
                <p className="text-sm font-medium text-foreground">
                  Your Rating: {userRating}
                </p>
                <p className="text-xs text-muted-foreground">
                  Some courses require a minimum rating to unlock. Complete ML
                  problems to increase your rating.
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </section>
    </Layout>
  );
}
