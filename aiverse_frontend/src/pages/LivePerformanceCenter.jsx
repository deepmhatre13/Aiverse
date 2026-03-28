import { useState, useEffect, useMemo, forwardRef } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Activity,
  TrendingUp,
  TrendingDown,
  Trophy,
  Target,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Loader2,
  RefreshCw,
  Wifi,
  WifiOff,
  Zap,
  Flame,
  BarChart3,
  PieChart,
  Calendar,
  ChevronRight,
  Code,
  ArrowUp,
  ArrowDown,
  Circle,
} from 'lucide-react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import confetti from 'canvas-confetti';

import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Progress } from '../components/ui/progress';
import useLivePerformance, { formatTimeAgo, getStatusColor, getDeltaIndicator } from '../hooks/useLivePerformance';

// Animation variants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
};

const pulseVariants = {
  pulse: {
    scale: [1, 1.05, 1],
    transition: { duration: 2, repeat: Infinity },
  },
};

// Animated number component for rank/score
function AnimatedNumber({ value, prefix = '', suffix = '', className = '', zeroToDash = false }) {
  const normalizedValue = value ?? 0;
  const shouldDash = zeroToDash && (value === null || value === undefined || Number(normalizedValue) === 0);

  const [displayValue, setDisplayValue] = useState(shouldDash ? 0 : normalizedValue);
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    if (shouldDash) {
      setIsAnimating(false);
      setDisplayValue(0);
      return;
    }
    if (normalizedValue !== displayValue) {
      setIsAnimating(true);
      // Animate from current value to new value
      const start = displayValue;
      const end = normalizedValue;
      const duration = 500;
      const startTime = Date.now();

      const animate = () => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        // Easing function
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = Math.round(start + (end - start) * eased);
        setDisplayValue(current);

        if (progress < 1) {
          requestAnimationFrame(animate);
        } else {
          setIsAnimating(false);
        }
      };

      requestAnimationFrame(animate);
    }
  }, [normalizedValue, shouldDash, displayValue]);

  return (
    <motion.span
      className={`tabular-nums ${className}`}
      animate={isAnimating && !shouldDash ? { scale: [1, 1.1, 1] } : {}}
      transition={{ duration: 0.3 }}
    >
      {shouldDash ? `${prefix}—${suffix}` : `${prefix}${displayValue.toLocaleString()}${suffix}`}
    </motion.span>
  );
}

// Connection status indicator
function ConnectionIndicator({ status, wsUnavailable }) {
  const statusConfig = {
    connected: { icon: Wifi, color: 'text-green-500', label: 'Live', pulse: true },
    connecting: { icon: Loader2, color: 'text-yellow-500', label: 'Connecting...', spin: true },
    polling: { icon: RefreshCw, color: 'text-amber-500', label: 'Live metrics temporarily unavailable', pulse: false },
    disconnected: { icon: WifiOff, color: 'text-muted-foreground', label: 'Offline' },
  };

  const config = statusConfig[status] || statusConfig.disconnected;
  const Icon = config.icon;
  const label = wsUnavailable && (status === 'polling' || status === 'disconnected')
    ? 'Live metrics temporarily unavailable'
    : config.label;

  return (
    <div className="flex items-center gap-2" title={label}>
      <motion.div
        animate={config.pulse ? pulseVariants.pulse : {}}
        className={config.color}
      >
        <Icon className={`w-4 h-4 ${config.spin ? 'animate-spin' : ''}`} />
      </motion.div>
      <span className={`text-sm font-medium ${config.color}`}>{label}</span>
    </div>
  );
}

// Live event item in activity feed — wrapped with forwardRef for AnimatePresence
const LiveEventItem = forwardRef(function LiveEventItem({ event, index }, ref) {
  const eventConfig = {
    submission_created: {
      icon: Code,
      title: 'New Submission',
      color: 'border-blue-500',
      bgColor: 'bg-blue-500/10',
    },
    evaluation_started: {
      icon: Loader2,
      title: 'Evaluation Started',
      color: 'border-yellow-500',
      bgColor: 'bg-yellow-500/10',
    },
    evaluation_completed: {
      icon: CheckCircle2,
      title: 'Evaluation Complete',
      color: 'border-green-500',
      bgColor: 'bg-green-500/10',
    },
    rank_changed: {
      icon: Trophy,
      title: 'Rank Changed',
      color: 'border-primary',
      bgColor: 'bg-primary/10',
    },
    score_updated: {
      icon: TrendingUp,
      title: 'Score Updated',
      color: 'border-cyan-500',
      bgColor: 'bg-cyan-500/10',
    },
    streak_updated: {
      icon: Flame,
      title: 'Streak Updated',
      color: 'border-orange-500',
      bgColor: 'bg-orange-500/10',
    },
  };

  const config = eventConfig[event.type] || {
    icon: Activity,
    title: event.type,
    color: 'border-gray-500',
    bgColor: 'bg-gray-500/10',
  };

  const Icon = config.icon;

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
      className={`flex items-start gap-3 p-3 rounded-lg border-l-4 ${config.color} ${config.bgColor}`}
    >
      <div className="p-1.5 rounded-full bg-background">
        <Icon className="w-4 h-4" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium">{config.title}</p>
        {event.payload?.problem_title && (
          <p className="text-xs text-muted-foreground truncate">
            {event.payload.problem_title}
          </p>
        )}
        {event.payload?.delta !== undefined && (
          <p className={`text-xs font-medium ${getDeltaIndicator(event.payload.delta).color}`}>
            {getDeltaIndicator(event.payload.delta).text}
          </p>
        )}
      </div>
      <span className="text-xs text-muted-foreground whitespace-nowrap">
        {formatTimeAgo(event.timestamp)}
      </span>
    </motion.div>
  );
});

// Activity feed item (from REST API)
function ActivityFeedItem({ activity, index }) {
  const statusIcons = {
    accepted: CheckCircle2,
    failed: XCircle,
    wrong_answer: XCircle,
    pending: Clock,
    evaluating: Loader2,
    runtime_error: AlertCircle,
    time_limit_exceeded: Clock,
    memory_limit_exceeded: AlertCircle,
    compilation_error: XCircle,
  };

  const Icon = statusIcons[activity.status?.toLowerCase()] || Circle;
  const statusColors = getStatusColor(activity.status);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.03 }}
      className="flex items-center gap-3 p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
    >
      <div className={`p-1.5 rounded-full ${statusColors}`}>
        <Icon className={`w-4 h-4 ${activity.status?.toLowerCase() === 'evaluating' ? 'animate-spin' : ''}`} />
      </div>
      <div className="flex-1 min-w-0">
        <Link
          to={`/problems/${activity.problem_slug ?? activity.problem?.slug ?? activity.problem_id ?? '#'}`}
          className="text-sm font-medium hover:text-primary transition-colors line-clamp-1"
        >
          {activity.problem_title ?? activity.problem?.title ?? (activity.problem_id ? `Problem #${activity.problem_id}` : 'Unknown Problem')}
        </Link>
        <p className="text-xs text-muted-foreground">
          {activity.language} · {activity.score !== undefined && `${activity.score} pts`}
        </p>
      </div>
      <div className="text-right">
        <Badge variant="outline" className={statusColors}>
          {activity.status?.replace(/_/g, ' ')}
        </Badge>
        <p className="text-xs text-muted-foreground mt-1">
          {formatTimeAgo(activity.submitted_at)}
        </p>
      </div>
    </motion.div>
  );
}

// Stat card component
function StatCard({ title, value, delta, icon: Icon, trend, suffix = '', prefix = '', zeroToDash = false, animate = true }) {
  const deltaInfo = getDeltaIndicator(delta, trend !== 'down');

  return (
    <motion.div variants={itemVariants}>
      <Card className="h-full">
        <CardContent className="p-4">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                {title}
              </p>
              <div className="flex items-baseline gap-2 mt-1">
                {animate ? (
                  <AnimatedNumber
                    value={value}
                    prefix={prefix}
                    suffix={suffix}
                    zeroToDash={zeroToDash}
                    className="text-2xl font-bold"
                  />
                ) : (
                  <span className="text-2xl font-bold">
                    {prefix}{value ?? 0}{suffix}
                  </span>
                )}
                {delta !== undefined && delta !== 0 && (
                  <span className={`text-sm font-medium ${deltaInfo.color}`}>
                    {deltaInfo.text}
                  </span>
                )}
              </div>
            </div>
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              <Icon className="w-5 h-5" />
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

// Heatmap component
function ActivityHeatmap({ data }) {
  const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  
  // Generate heatmap grid (last 12 weeks)
  const heatmapData = useMemo(() => {
    const grid = [];
    const today = new Date();
    
    for (let week = 11; week >= 0; week--) {
      const weekData = [];
      for (let day = 0; day < 7; day++) {
        const date = new Date(today);
        date.setDate(date.getDate() - (week * 7 + (6 - day)));
        const dateStr = date.toISOString().split('T')[0];
        const activity = data?.find(d => d.date === dateStr);
        weekData.push({
          date: dateStr,
          count: activity?.count || 0,
          day: day,
        });
      }
      grid.push(weekData);
    }
    return grid;
  }, [data]);

  const getIntensity = (count) => {
    if (count === 0) return 'bg-muted';
    if (count <= 2) return 'bg-green-200 dark:bg-green-900';
    if (count <= 4) return 'bg-green-400 dark:bg-green-700';
    if (count <= 6) return 'bg-green-500 dark:bg-green-600';
    return 'bg-green-600 dark:bg-green-500';
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-1 text-xs text-muted-foreground mb-2">
        <span>Less</span>
        <div className="w-3 h-3 rounded-sm bg-muted" />
        <div className="w-3 h-3 rounded-sm bg-green-200 dark:bg-green-900" />
        <div className="w-3 h-3 rounded-sm bg-green-400 dark:bg-green-700" />
        <div className="w-3 h-3 rounded-sm bg-green-500 dark:bg-green-600" />
        <div className="w-3 h-3 rounded-sm bg-green-600 dark:bg-green-500" />
        <span>More</span>
      </div>
      <div className="flex gap-1">
        <div className="flex flex-col gap-1 text-xs text-muted-foreground mr-2">
          {days.map((day, i) => (
            <div key={day} className="h-3 flex items-center">
              {i % 2 === 1 && day}
            </div>
          ))}
        </div>
        {heatmapData.map((week, weekIndex) => (
          <div key={weekIndex} className="flex flex-col gap-1">
            {week.map((day, dayIndex) => (
              <motion.div
                key={`${weekIndex}-${dayIndex}`}
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: (weekIndex * 7 + dayIndex) * 0.005 }}
                className={`w-3 h-3 rounded-sm ${getIntensity(day.count)} cursor-pointer`}
                title={`${day.date}: ${day.count} submissions`}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

// Chart colors
const CHART_COLORS = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#06b6d4', '#8b5cf6'];

// Main component
export default function LivePerformanceCenter() {
  const {
    summary,
    activityFeed,
    analytics,
    liveEvents,
    isLoading,
    error,
    connectionStatus,
    lastUpdate,
    wsUnavailable,
    refreshData,
    clearLiveEvents,
  } = useLivePerformance();

  const [activeAnalyticsTab, setActiveAnalyticsTab] = useState('progression');

  // Celebrate rank improvements
  useEffect(() => {
    const rankChangeEvent = liveEvents.find(
      e => e.type === 'rank_changed' && e.payload?.delta < 0
    );
    if (rankChangeEvent) {
      confetti({
        particleCount: 100,
        spread: 70,
        origin: { y: 0.6 },
        colors: ['#ef4444', '#f97316', '#eab308'],
      });
    }
  }, [liveEvents]);

  if (isLoading && !summary) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <main className="container mx-auto px-4 py-24">
          <div className="flex items-center justify-center h-[60vh]">
            <div className="text-center">
              <Loader2 className="w-12 h-12 animate-spin text-primary mx-auto mb-4" />
              <p className="text-muted-foreground">Loading your performance data...</p>
            </div>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  if (error && !summary) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <main className="container mx-auto px-4 py-24">
          <div className="flex items-center justify-center h-[60vh]">
            <div className="text-center">
              <AlertCircle className="w-12 h-12 text-destructive mx-auto mb-4" />
              <p className="text-muted-foreground mb-2">Live metrics temporarily unavailable</p>
              <p className="text-sm text-muted-foreground/80 mb-4">
                {error}
              </p>
              <Button onClick={refreshData}>
                <RefreshCw className="w-4 h-4 mr-2" />
                Retry
              </Button>
            </div>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <main className="container mx-auto px-4 py-24">
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="space-y-6"
        >
          {/* Header */}
          <motion.div variants={itemVariants} className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold flex items-center gap-3">
                <Activity className="w-8 h-8 text-primary" />
                Live Performance Center
              </h1>
              <p className="text-muted-foreground mt-1">
                Real-time insights into your ML journey
              </p>
            </div>
            <div className="flex items-center gap-4">
              <ConnectionIndicator status={connectionStatus} wsUnavailable={wsUnavailable} />
              {lastUpdate && (
                <span className="text-xs text-muted-foreground">
                  Updated {formatTimeAgo(lastUpdate)}
                </span>
              )}
              <Button variant="outline" size="sm" onClick={refreshData}>
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </Button>
            </div>
          </motion.div>

          {/* Live Summary Panel */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            <StatCard
              title="Global Rank"
              value={summary?.rank ?? 0}
              delta={summary?.rank_delta}
              icon={Trophy}
              trend="down"
              prefix="#"
              zeroToDash
            />
            <StatCard
              title="Total Score"
              value={summary?.total_score || 0}
              delta={summary?.score_delta}
              icon={Target}
            />
            <StatCard
              title="Problems Solved"
              value={summary?.problems_solved || 0}
              delta={summary?.problems_delta}
              icon={CheckCircle2}
            />
            <StatCard
              title="Submissions"
              value={summary?.total_submissions || 0}
              delta={summary?.submissions_today}
              icon={Code}
            />
            <StatCard
              title="Success Rate"
              value={summary?.success_rate || 0}
              icon={TrendingUp}
              suffix="%"
              animate={false}
            />
            <StatCard
              title="Current Streak"
              value={summary?.current_streak || 0}
              icon={Flame}
              suffix=" days"
              animate={false}
            />
          </div>

          {/* Main Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Live Activity Feed */}
            <motion.div variants={itemVariants} className="lg:col-span-1">
              <Card className="h-full">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Zap className="w-5 h-5 text-primary" />
                      Live Activity
                    </CardTitle>
                    {liveEvents.length > 0 && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={clearLiveEvents}
                        className="text-xs"
                      >
                        Clear
                      </Button>
                    )}
                  </div>
                  <CardDescription>Real-time events as they happen</CardDescription>
                </CardHeader>
                <CardContent className="space-y-2 max-h-[400px] overflow-y-auto">
                  <AnimatePresence mode="popLayout">
                    {liveEvents.length > 0 ? (
                      liveEvents.map((event, index) => (
                        <LiveEventItem key={event.id} event={event} index={index} />
                      ))
                    ) : (
                      <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="text-center py-8 text-muted-foreground"
                      >
                        <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
                        <p className="text-sm">Waiting for activity...</p>
                        <p className="text-xs mt-1">Events will appear here in real-time</p>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </CardContent>
              </Card>
            </motion.div>

            {/* Recent Submissions Feed */}
            <motion.div variants={itemVariants} className="lg:col-span-2">
              <Card className="h-full">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <BarChart3 className="w-5 h-5 text-primary" />
                      Recent Submissions
                    </CardTitle>
                    <Link to="/submissions">
                      <Button variant="ghost" size="sm" className="text-xs">
                        View All <ChevronRight className="w-4 h-4 ml-1" />
                      </Button>
                    </Link>
                  </div>
                  <CardDescription>Your latest problem submissions</CardDescription>
                </CardHeader>
                <CardContent className="space-y-2 max-h-[400px] overflow-y-auto">
                  {activityFeed.length > 0 ? (
                    activityFeed.map((activity, index) => (
                      <ActivityFeedItem key={activity.id || index} activity={activity} index={index} />
                    ))
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      <Code className="w-8 h-8 mx-auto mb-2 opacity-50" />
                      <p className="text-sm">No submissions yet</p>
                      <Link to="/problems">
                        <Button variant="outline" size="sm" className="mt-2">
                          Start Solving
                        </Button>
                      </Link>
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          </div>

          {/* Performance Analytics */}
          <motion.div variants={itemVariants}>
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <PieChart className="w-5 h-5 text-primary" />
                  Performance Analytics
                </CardTitle>
                <CardDescription>Detailed breakdown of your performance metrics</CardDescription>
              </CardHeader>
              <CardContent>
                <Tabs value={activeAnalyticsTab} onValueChange={setActiveAnalyticsTab}>
                  <TabsList className="grid w-full grid-cols-4 mb-6">
                    <TabsTrigger value="progression">Score Progression</TabsTrigger>
                    <TabsTrigger value="difficulty">Difficulty Breakdown</TabsTrigger>
                    <TabsTrigger value="languages">Languages</TabsTrigger>
                    <TabsTrigger value="heatmap">Activity Heatmap</TabsTrigger>
                  </TabsList>

                  <TabsContent value="progression" className="h-[300px]">
                    {analytics?.score_progression?.length > 0 ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={analytics.score_progression}>
                          <defs>
                            <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                              <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                          <XAxis dataKey="date" className="text-xs" />
                          <YAxis className="text-xs" />
                          <Tooltip
                            contentStyle={{
                              backgroundColor: 'hsl(var(--background))',
                              border: '1px solid hsl(var(--border))',
                              borderRadius: '8px',
                            }}
                          />
                          <Area
                            type="monotone"
                            dataKey="cumulative_score"
                            stroke="#ef4444"
                            strokeWidth={2}
                            fill="url(#scoreGradient)"
                            name="Total Score"
                          />
                        </AreaChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="flex items-center justify-center h-full text-muted-foreground">
                        <p>No score data available yet</p>
                      </div>
                    )}
                  </TabsContent>

                  <TabsContent value="difficulty" className="h-[300px]">
                    {analytics?.difficulty_breakdown?.length > 0 ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={analytics.difficulty_breakdown} layout="vertical">
                          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                          <XAxis type="number" className="text-xs" />
                          <YAxis dataKey="difficulty" type="category" width={80} className="text-xs" />
                          <Tooltip
                            contentStyle={{
                              backgroundColor: 'hsl(var(--background))',
                              border: '1px solid hsl(var(--border))',
                              borderRadius: '8px',
                            }}
                          />
                          <Bar dataKey="solved" name="Solved" fill="#22c55e" radius={[0, 4, 4, 0]} />
                          <Bar dataKey="total" name="Total" fill="#ef4444" opacity={0.3} radius={[0, 4, 4, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="flex items-center justify-center h-full text-muted-foreground">
                        <p>No difficulty data available yet</p>
                      </div>
                    )}
                  </TabsContent>

                  <TabsContent value="languages" className="h-[300px]">
                    {analytics?.language_distribution?.length > 0 ? (
                      <div className="flex items-center justify-center h-full">
                        <ResponsiveContainer width="100%" height="100%">
                          <RechartsPieChart>
                            <Pie
                              data={analytics.language_distribution}
                              cx="50%"
                              cy="50%"
                              innerRadius={60}
                              outerRadius={100}
                              paddingAngle={2}
                              dataKey="count"
                              nameKey="language"
                              label={({ language, percent }) =>
                                `${language} ${(percent * 100).toFixed(0)}%`
                              }
                            >
                              {analytics.language_distribution.map((entry, index) => (
                                <Cell
                                  key={`cell-${index}`}
                                  fill={CHART_COLORS[index % CHART_COLORS.length]}
                                />
                              ))}
                            </Pie>
                            <Tooltip
                              contentStyle={{
                                backgroundColor: 'hsl(var(--background))',
                                border: '1px solid hsl(var(--border))',
                                borderRadius: '8px',
                              }}
                            />
                            <Legend />
                          </RechartsPieChart>
                        </ResponsiveContainer>
                      </div>
                    ) : (
                      <div className="flex items-center justify-center h-full text-muted-foreground">
                        <p>No language data available yet</p>
                      </div>
                    )}
                  </TabsContent>

                  <TabsContent value="heatmap">
                    <div className="flex items-center justify-center py-8">
                      <ActivityHeatmap data={analytics?.activity_heatmap} />
                    </div>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          </motion.div>

          {/* Quick Actions */}
          <motion.div variants={itemVariants}>
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Quick Actions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <Link to="/problems">
                    <Button variant="outline" className="w-full h-full py-6 flex flex-col gap-2">
                      <Code className="w-6 h-6 text-primary" />
                      <span>Solve Problems</span>
                    </Button>
                  </Link>
                  <Link to="/learn">
                    <Button variant="outline" className="w-full h-full py-6 flex flex-col gap-2">
                      <Target className="w-6 h-6 text-primary" />
                      <span>Continue Learning</span>
                    </Button>
                  </Link>
                  {/* <Link to="/leaderboard">
                    <Button variant="outline" className="w-full h-full py-6 flex flex-col gap-2">
                      <Trophy className="w-6 h-6 text-primary" />
                      <span>View Leaderboard</span>
                    </Button>
                  </Link> */}
                  <Link to="/mentor">
                    <Button variant="outline" className="w-full h-full py-6 flex flex-col gap-2">
                      <Zap className="w-6 h-6 text-primary" />
                      <span>Ask AI Mentor</span>
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>
      </main>

      <Footer />
    </div>
  );
}
