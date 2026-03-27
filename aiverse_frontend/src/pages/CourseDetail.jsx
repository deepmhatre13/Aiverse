import { useState, useEffect, useMemo } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowLeft,
  Clock,
  Play,
  Lock,
  CheckCircle,
  Users,
  Star,
  ShoppingCart,
  BookOpen,
  ChevronDown,
  ChevronUp,
  Award,
  FileText,
  Download,
  ExternalLink,
  Sparkles,
  BarChart3,
  AlertCircle,
  Check,
} from 'lucide-react';
import Layout from '../components/Layout';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '../components/ui/accordion';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '../components/ui/tabs';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorState from '../components/ErrorState';
import PurchaseModal from '../components/learn/PurchaseModal';
import api from '../api/axios';
import { toast } from 'sonner';
import { useAuth } from '../contexts/AuthContext';
import { formatINR } from '../lib/currency';
import { getCourseVisual } from '../lib/courseVisuals';

/**
 * CourseDetail Page - Premium Layout
 * 
 * Left: Course content (Overview, Curriculum, Requirements, Instructor)
 * Right: Sticky sidebar (Price, Enrollment, Progress, CTA)
 * 
 * Payment Flow:
 * 1. User clicks "Enroll Now" / "Buy Course"
 * 2. Stripe Payment Modal opens
 * 3. Payment intent created on backend
 * 4. User completes payment
 * 5. Webhook activates enrollment
 * 6. UI refreshes to show enrolled state
 */
export default function CourseDetail() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();
  const [course, setCourse] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [isEnrolling, setIsEnrolling] = useState(false);

  useEffect(() => {
    fetchCourse();
  }, [slug]);

  const fetchCourse = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await api.get(`/api/learn/courses/${slug}/`);
      const data = response.data;
      setCourse(
        data.course
          ? { ...data.course, is_enrolled: data.is_enrolled, is_locked: data.is_locked, progress: data.progress }
          : data
      );
    } catch (err) {
      if (err.response?.status === 404) {
        setError('Course not found');
      } else if (err.response?.status === 403) {
        // Rating-locked course
        setError(
          err.response?.data?.message ||
            'You need a higher rating to access this course'
        );
      } else {
        setError(
          err.response?.data?.message ||
            err.response?.data?.detail ||
            'Failed to load course'
        );
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Derived state
  const isPaid = course && (course.is_paid || parseFloat(course.price || 0) > 0);
  const isFree = course && (course.is_free || parseFloat(course.price || 0) === 0);
  const isEnrolled = course?.is_enrolled === true;
  const hasAccess = isFree || isEnrolled;
  const enrollmentStatus = course?.enrollment_status;

  // Progress calculation - guard against NaN
  const progressData = useMemo(() => {
    if (!course?.lessons) return { completed: 0, total: 0, percent: 0 };
    const total = course.lessons.length;
    const completed = course.lessons.filter(
      (l) => l.is_completed || l.progress?.is_completed || l.progress?.completed
    ).length;
    return {
      completed,
      total,
      percent: total > 0 ? Math.round((completed / total) * 100) : 0,
    };
  }, [course?.lessons]);

  // Group lessons by section
  const sections = useMemo(() => {
    if (!course?.lessons) return [];

    // If lessons have section info, group by section
    const sectionMap = new Map();
    course.lessons.forEach((lesson, index) => {
      const sectionTitle = lesson.section || 'Course Content';
      if (!sectionMap.has(sectionTitle)) {
        sectionMap.set(sectionTitle, []);
      }
      sectionMap.get(sectionTitle).push({ ...lesson, index: index + 1 });
    });

    return Array.from(sectionMap.entries()).map(([title, lessons]) => ({
      title,
      lessons,
      totalDuration: lessons.reduce(
        (acc, l) => acc + (l.duration_minutes || 0),
        0
      ),
    }));
  }, [course?.lessons]);

  // Handlers
  const handleBuyClick = () => {
    if (!isAuthenticated) {
      toast.error('Please login to purchase courses');
      navigate('/login');
      return;
    }
    setShowPaymentModal(true);
  };

  const handleEnrollFree = async () => {
    if (!isAuthenticated) {
      toast.error('Please login to enroll');
      navigate('/login');
      return;
    }

    try {
      setIsEnrolling(true);
      await api.post(`/api/learn/courses/${slug}/enroll/`);
      toast.success('Successfully enrolled!');
      fetchCourse();
    } catch (err) {
      const message =
        err.response?.data?.error ||
        err.response?.data?.message ||
        'Failed to enroll';
      toast.error(message);
    } finally {
      setIsEnrolling(false);
    }
  };

  const handlePaymentSuccess = () => {
    toast.success('Payment successful! Activating your enrollment...');
    // Give webhook time to process
    setTimeout(fetchCourse, 2000);
  };

  const startFirstLesson = () => {
    if (course?.lessons?.[0]) {
      navigate(`/learn/courses/${slug}/lessons/${course.lessons[0].slug}`);
    }
  };

  const continueLesson = () => {
    // Find first incomplete lesson
    const nextLesson = course?.lessons?.find(
      (l) => !l.is_completed && !l.progress?.completed
    );
    if (nextLesson) {
      navigate(`/learn/courses/${slug}/lessons/${nextLesson.slug}`);
    } else if (course?.lessons?.[0]) {
      // All complete, go to first
      navigate(`/learn/courses/${slug}/lessons/${course.lessons[0].slug}`);
    }
  };

  // Format helpers
  const formatDuration = (minutes) => {
    if (!minutes) return '0m';
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    return h > 0 ? `${h}h ${m}m` : `${m}m`;
  };

  if (isLoading) {
    return (
      <Layout>
        <div className="min-h-[60vh] flex items-center justify-center">
          <LoadingSpinner text="Loading course..." />
        </div>
      </Layout>
    );
  }

  if (error && !course) {
    return (
      <Layout>
        <div className="container mx-auto px-4 py-12">
          <ErrorState message={error} onRetry={fetchCourse} />
        </div>
      </Layout>
    );
  }

  if (!course) {
    return (
      <Layout>
        <div className="container mx-auto px-4 py-12">
          <ErrorState message="Course not found" onRetry={fetchCourse} />
        </div>
      </Layout>
    );
  }

  const visual = getCourseVisual(course.title, course.thumbnail);

  return (
    <Layout>
      {/* Hero Section */}
      <section className="bg-gradient-to-b from-background to-muted/30 border-b border-border">
        <div className="container mx-auto px-4 lg:px-8 py-8">
          <Link
            to="/learn"
            className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mb-6 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Courses
          </Link>

          <div className="grid lg:grid-cols-3 gap-8 lg:gap-12">
            {/* Main Content */}
            <div className="lg:col-span-2">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
              >
                {/* Badges */}
                <div className="flex flex-wrap items-center gap-2 mb-4">
                  {course.track && (
                    <Badge variant="secondary" className="font-medium">
                      {course.track.title || course.track.name || course.track}
                    </Badge>
                  )}
                  <Badge
                    variant="outline"
                    className={`capitalize ${
                      course.difficulty === 'advanced'
                        ? 'border-red-500/50 text-red-500'
                        : course.difficulty === 'intermediate'
                        ? 'border-amber-500/50 text-amber-500'
                        : 'border-emerald-500/50 text-emerald-500'
                    }`}
                  >
                    {course.difficulty || 'Beginner'}
                  </Badge>
                  {isFree && (
                    <Badge className="bg-emerald-500/90 text-white">Free</Badge>
                  )}
                  {isEnrolled && (
                    <Badge
                      variant="secondary"
                      className="bg-primary/10 text-primary"
                    >
                      <Check className="w-3 h-3 mr-1" />
                      Enrolled
                    </Badge>
                  )}
                </div>

                {/* Title */}
                <h1 className="text-3xl lg:text-4xl font-bold text-foreground mb-4 tracking-tight">
                  {course.title}
                </h1>

                {/* Description */}
                <p className="text-lg text-muted-foreground mb-6 leading-relaxed">
                  {course.description}
                </p>

                {/* Stats Row */}
                <div className="flex flex-wrap items-center gap-6 text-sm text-muted-foreground">
                  {course.rating_avg > 0 && (
                    <div className="flex items-center gap-1.5">
                      <Star className="w-4 h-4 fill-amber-400 text-amber-400" />
                      <span className="font-semibold text-foreground">
                        {course.rating_avg?.toFixed(1)}
                      </span>
                      <span>({course.rating_count || 0} reviews)</span>
                    </div>
                  )}
                  <div className="flex items-center gap-1.5">
                    <Users className="w-4 h-4" />
                    <span>
                      {course.students_count || course.enrollment_count || 0}{' '}
                      students
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Clock className="w-4 h-4" />
                    <span>
                      {course.total_duration_hours ||
                        course.duration_hours ||
                        0}{' '}
                      hours
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Play className="w-4 h-4" />
                    <span>
                      {course.total_lessons || course.lessons?.length || 0}{' '}
                      lessons
                    </span>
                  </div>
                </div>
              </motion.div>
            </div>

            {/* Sidebar Card */}
            <div className="lg:col-span-1">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2, duration: 0.5 }}
                className="sticky top-24"
              >
                <div className="bg-card border border-border rounded-xl overflow-hidden shadow-lg">
                  {/* Thumbnail */}
                  {(visual.src || course.thumbnail) && (
                    <div className="aspect-video bg-muted">
                      <img
                        src={visual.src || course.thumbnail}
                        alt={course.title}
                        className="w-full h-full object-cover"
                      />
                    </div>
                  )}

                  <div className="p-6">
                    {/* Price */}
                    <div className="flex items-baseline gap-2 mb-6">
                      <span className="text-3xl font-bold text-foreground">
                        {isFree ? 'Free' : formatINR(course.price)}
                      </span>
                      {course.original_price &&
                        parseFloat(course.original_price) >
                          parseFloat(course.price) && (
                          <span className="text-lg text-muted-foreground line-through">
                            {formatINR(course.original_price)}
                          </span>
                        )}
                    </div>

                    {/* Progress (if enrolled) */}
                    {hasAccess && (
                      <div className="mb-6">
                        <div className="flex justify-between text-sm mb-2">
                          <span className="text-muted-foreground">
                            Progress
                          </span>
                          <span className="font-medium">
                            {progressData.completed}/{progressData.total}{' '}
                            lessons ({progressData.percent}%)
                          </span>
                        </div>
                        <Progress value={progressData.percent} className="h-2" />
                      </div>
                    )}

                    {/* CTA Button */}
                    {hasAccess ? (
                      <>
                        <Button
                          onClick={
                            progressData.completed > 0
                              ? continueLesson
                              : startFirstLesson
                          }
                          className="w-full h-12 text-base font-semibold bg-primary hover:bg-primary/90"
                        >
                          <Play className="w-5 h-5 mr-2" />
                          {progressData.completed > 0
                            ? 'Continue Learning'
                            : 'Start Learning'}
                        </Button>
                        
                        {/* Final Quiz Button - Show when all lessons completed */}
                        {progressData.percent === 100 && (
                          <Button
                            onClick={() => navigate(`/learn/courses/${slug}/final-quiz`)}
                            variant="outline"
                            className="w-full h-12 text-base font-semibold mt-3 border-emerald-500/50 text-emerald-600 hover:bg-emerald-500/10"
                          >
                            <Award className="w-5 h-5 mr-2" />
                            Take Final Quiz
                          </Button>
                        )}
                      </>
                    ) : isPaid ? (
                      <Button
                        onClick={handleBuyClick}
                        className="w-full h-12 text-base font-semibold bg-primary hover:bg-primary/90"
                      >
                        <ShoppingCart className="w-5 h-5 mr-2" />
                        Enroll Now
                      </Button>
                    ) : (
                      <Button
                        onClick={handleEnrollFree}
                        disabled={isEnrolling}
                        className="w-full h-12 text-base font-semibold bg-emerald-600 hover:bg-emerald-700"
                      >
                        {isEnrolling ? (
                          <LoadingSpinner size="sm" />
                        ) : (
                          <>
                            <Sparkles className="w-5 h-5 mr-2" />
                            Enroll for Free
                          </>
                        )}
                      </Button>
                    )}

                    {/* Features List */}
                    <div className="mt-6 space-y-3">
                      <div className="flex items-center gap-3 text-sm">
                        <Check className="w-4 h-4 text-emerald-500 shrink-0" />
                        <span className="text-muted-foreground">
                          {course.total_lessons || course.lessons?.length || 0}{' '}
                          video lessons
                        </span>
                      </div>
                      <div className="flex items-center gap-3 text-sm">
                        <Check className="w-4 h-4 text-emerald-500 shrink-0" />
                        <span className="text-muted-foreground">
                          Lifetime access
                        </span>
                      </div>
                      <div className="flex items-center gap-3 text-sm">
                        <Check className="w-4 h-4 text-emerald-500 shrink-0" />
                        <span className="text-muted-foreground">
                          Certificate of completion
                        </span>
                      </div>
                      {isPaid && (
                        <div className="flex items-center gap-3 text-sm">
                          <Check className="w-4 h-4 text-emerald-500 shrink-0" />
                          <span className="text-muted-foreground">
                            30-day money-back guarantee
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Required Rating Warning */}
                    {course.required_rating > 0 && !hasAccess && (
                      <div className="mt-6 p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                        <div className="flex items-start gap-2">
                          <AlertCircle className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />
                          <div className="text-sm">
                            <p className="font-medium text-amber-600">
                              Requires {course.required_rating}+ rating
                            </p>
                            <p className="text-muted-foreground text-xs mt-1">
                              Complete ML problems to increase your rating
                            </p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            </div>
          </div>
        </div>
      </section>

      {/* Content Tabs */}
      <section className="container mx-auto px-4 lg:px-8 py-10">
        <div className="lg:pr-[calc(33.33%+3rem)]">
          <Tabs defaultValue="curriculum" className="w-full">
            <TabsList className="grid w-full grid-cols-3 lg:w-auto lg:inline-flex mb-8">
              <TabsTrigger value="curriculum" className="gap-2">
                <BookOpen className="w-4 h-4 hidden sm:inline" />
                Curriculum
              </TabsTrigger>
              <TabsTrigger value="overview" className="gap-2">
                <FileText className="w-4 h-4 hidden sm:inline" />
                Overview
              </TabsTrigger>
              <TabsTrigger value="reviews" className="gap-2">
                <Star className="w-4 h-4 hidden sm:inline" />
                Reviews
              </TabsTrigger>
            </TabsList>

            {/* Curriculum Tab */}
            <TabsContent value="curriculum" className="mt-0">
              <div className="space-y-4">
                {sections.length > 0 ? (
                  <Accordion
                    type="multiple"
                    defaultValue={sections.map((_, i) => `section-${i}`)}
                    className="space-y-4"
                  >
                    {sections.map((section, sectionIndex) => (
                      <AccordionItem
                        key={sectionIndex}
                        value={`section-${sectionIndex}`}
                        className="border border-border rounded-lg overflow-hidden bg-card"
                      >
                        <AccordionTrigger className="px-4 py-3 hover:no-underline hover:bg-muted/50 transition-colors">
                          <div className="flex items-center justify-between w-full pr-4">
                            <span className="font-semibold text-left">
                              {section.title}
                            </span>
                            <span className="text-sm text-muted-foreground">
                              {section.lessons.length} lessons •{' '}
                              {formatDuration(section.totalDuration)}
                            </span>
                          </div>
                        </AccordionTrigger>
                        <AccordionContent className="pb-0">
                          <div className="divide-y divide-border">
                            {section.lessons.map((lesson) => {
                              const isCompleted =
                                lesson.is_completed || lesson.progress?.completed;
                              const isAccessible = hasAccess || lesson.is_preview;

                              return (
                                <Link
                                  key={lesson.id || lesson.slug}
                                  to={
                                    isAccessible
                                      ? `/learn/courses/${slug}/lessons/${lesson.slug}`
                                      : '#'
                                  }
                                  onClick={(e) =>
                                    !isAccessible && e.preventDefault()
                                  }
                                  className={`flex items-center gap-4 px-4 py-3 transition-colors ${
                                    isAccessible
                                      ? 'hover:bg-muted/50 cursor-pointer'
                                      : 'cursor-not-allowed opacity-60'
                                  }`}
                                >
                                  {/* Completion Status / Lock */}
                                  <div
                                    className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                                      isCompleted
                                        ? 'bg-emerald-500/10 text-emerald-500'
                                        : isAccessible
                                        ? 'bg-primary/10 text-primary'
                                        : 'bg-muted text-muted-foreground'
                                    }`}
                                  >
                                    {isCompleted ? (
                                      <CheckCircle className="w-4 h-4" />
                                    ) : !isAccessible ? (
                                      <Lock className="w-4 h-4" />
                                    ) : (
                                      <Play className="w-4 h-4" />
                                    )}
                                  </div>

                                  {/* Lesson Info */}
                                  <div className="flex-1 min-w-0">
                                    <p className="font-medium text-sm truncate">
                                      {lesson.index}. {lesson.title}
                                    </p>
                                    <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                                      <span className="flex items-center gap-1">
                                        <Play className="w-3 h-3" />
                                        Video
                                      </span>
                                      <span className="flex items-center gap-1">
                                        <Clock className="w-3 h-3" />
                                        {lesson.duration_minutes || 0}m
                                      </span>
                                      {lesson.is_preview && (
                                        <Badge
                                          variant="outline"
                                          className="text-xs px-1.5 py-0"
                                        >
                                          Preview
                                        </Badge>
                                      )}
                                    </div>
                                  </div>
                                </Link>
                              );
                            })}
                          </div>
                        </AccordionContent>
                      </AccordionItem>
                    ))}
                  </Accordion>
                ) : (
                  <div className="text-center py-12 text-muted-foreground">
                    <BookOpen className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>No lessons available yet</p>
                  </div>
                )}
              </div>
            </TabsContent>

            {/* Overview Tab */}
            <TabsContent value="overview" className="mt-0">
              <div className="space-y-8">
                {/* What you'll learn */}
                {course.learning_outcomes && (
                  <div>
                    <h3 className="text-lg font-semibold mb-4">
                      What you'll learn
                    </h3>
                    <div className="grid sm:grid-cols-2 gap-3">
                      {(Array.isArray(course.learning_outcomes)
                        ? course.learning_outcomes
                        : course.learning_outcomes.split('\n')
                      ).map((item, i) => (
                        <div key={i} className="flex items-start gap-3">
                          <Check className="w-4 h-4 text-emerald-500 mt-1 shrink-0" />
                          <span className="text-muted-foreground text-sm">
                            {item}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Requirements */}
                {course.requirements && (
                  <div>
                    <h3 className="text-lg font-semibold mb-4">Requirements</h3>
                    <ul className="space-y-2">
                      {(Array.isArray(course.requirements)
                        ? course.requirements
                        : course.requirements.split('\n')
                      ).map((req, i) => (
                        <li
                          key={i}
                          className="flex items-start gap-3 text-sm text-muted-foreground"
                        >
                          <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground mt-2 shrink-0" />
                          {req}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Full Description */}
                {course.full_description && (
                  <div>
                    <h3 className="text-lg font-semibold mb-4">Description</h3>
                    <div className="prose prose-sm max-w-none dark:prose-invert text-muted-foreground">
                      <p className="whitespace-pre-line">
                        {course.full_description}
                      </p>
                    </div>
                  </div>
                )}

                {/* Track Info */}
                {course.track && (
                  <div>
                    <h3 className="text-lg font-semibold mb-4">
                      Part of Track
                    </h3>
                    <div className="p-4 bg-muted/50 border border-border rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                          <BarChart3 className="w-6 h-6 text-primary" />
                        </div>
                        <div>
                          <p className="font-medium">
                            {course.track.title || course.track.name || course.track}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            {course.track.description ||
                              'A structured learning path'}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Instructor */}
                {course.instructor && (
                  <div>
                    <h3 className="text-lg font-semibold mb-4">Instructor</h3>
                    <div className="flex items-start gap-4">
                      <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center overflow-hidden">
                        {course.instructor.avatar ? (
                          <img
                            src={course.instructor.avatar}
                            alt={course.instructor.name}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <span className="text-2xl font-semibold text-muted-foreground">
                            {(course.instructor.name || 'I')[0].toUpperCase()}
                          </span>
                        )}
                      </div>
                      <div>
                        <p className="font-semibold">
                          {course.instructor.name || 'Instructor'}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {course.instructor.title || 'Course Creator'}
                        </p>
                        {course.instructor.bio && (
                          <p className="text-sm text-muted-foreground mt-2">
                            {course.instructor.bio}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </TabsContent>

            {/* Reviews Tab */}
            <TabsContent value="reviews" className="mt-0">
              <div className="space-y-6">
                {/* Rating Summary */}
                <div className="flex flex-col sm:flex-row gap-6 items-start">
                  <div className="text-center p-6 bg-muted/50 border border-border rounded-lg">
                    <div className="text-4xl font-bold text-foreground">
                      {course.rating_avg?.toFixed(1) || '0.0'}
                    </div>
                    <div className="flex items-center justify-center gap-1 my-2">
                      {[1, 2, 3, 4, 5].map((star) => (
                        <Star
                          key={star}
                          className={`w-5 h-5 ${
                            star <= Math.round(course.rating_avg || 0)
                              ? 'fill-amber-400 text-amber-400'
                              : 'text-muted-foreground'
                          }`}
                        />
                      ))}
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {course.rating_count || 0} reviews
                    </p>
                  </div>

                  {/* Rating Breakdown */}
                  <div className="flex-1 space-y-2">
                    {[5, 4, 3, 2, 1].map((rating) => {
                      const count = course.rating_breakdown?.[rating] || 0;
                      const percent =
                        course.rating_count > 0
                          ? (count / course.rating_count) * 100
                          : 0;
                      return (
                        <div key={rating} className="flex items-center gap-3">
                          <span className="text-sm w-3">{rating}</span>
                          <Star className="w-4 h-4 fill-amber-400 text-amber-400" />
                          <Progress value={percent} className="h-2 flex-1" />
                          <span className="text-xs text-muted-foreground w-8">
                            {count}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Reviews List */}
                {course.reviews && course.reviews.length > 0 ? (
                  <div className="space-y-4">
                    {course.reviews.map((review, i) => (
                      <div
                        key={review.id || i}
                        className="p-4 bg-card border border-border rounded-lg"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                              <span className="text-sm font-medium">
                                {(review.user?.username || 'U')[0].toUpperCase()}
                              </span>
                            </div>
                            <div>
                              <p className="text-sm font-medium">
                                {review.user?.username || 'Anonymous'}
                              </p>
                              <div className="flex items-center gap-1">
                                {[1, 2, 3, 4, 5].map((star) => (
                                  <Star
                                    key={star}
                                    className={`w-3 h-3 ${
                                      star <= review.rating
                                        ? 'fill-amber-400 text-amber-400'
                                        : 'text-muted-foreground'
                                    }`}
                                  />
                                ))}
                              </div>
                            </div>
                          </div>
                          <span className="text-xs text-muted-foreground">
                            {review.created_at &&
                              new Date(review.created_at).toLocaleDateString()}
                          </span>
                        </div>
                        {review.comment && (
                          <p className="text-sm text-muted-foreground">
                            {review.comment}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12 text-muted-foreground">
                    <Star className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>No reviews yet</p>
                    {hasAccess && (
                      <p className="text-sm mt-2">
                        Complete the course to leave a review
                      </p>
                    )}
                  </div>
                )}
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </section>

      {/* Payment Modal - Razorpay or Stripe */}
      <PurchaseModal
        isOpen={showPaymentModal}
        onClose={() => setShowPaymentModal(false)}
        course={course}
        onSuccess={handlePaymentSuccess}
      />
    </Layout>
  );
}
