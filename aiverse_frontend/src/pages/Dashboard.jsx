import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { AlertTriangle, TrendingUp } from 'lucide-react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import Layout from '../components/Layout';
import LoadingSpinner from '../components/LoadingSpinner';
import { useLearner } from '../contexts/LearnerContext';
import { useAuth } from '../contexts/AuthContext';
import { getMasteryHistory } from '../api/learnerApi';
import MasteryRadar from '../components/dashboard/MasteryRadar';
import RecommendationCard from '../components/dashboard/RecommendationCard';
import ContinueCard from '../components/dashboard/ContinueCard';
import WeakConceptsPanel from '../components/dashboard/WeakConceptsPanel';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';

const pageVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.4 },
  },
};

const recommendationVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.07 },
  },
};

export default function Dashboard() {
  const { user, isAuthenticated } = useAuth();
  const { profile, masteries, recommendations, loading, getMasteryHistory } = useLearner();
  const navigate = useNavigate();
  const [selectedConcept, setSelectedConcept] = useState('');
  const [masteryHistory, setMasteryHistory] = useState([]);

  useEffect(() => {
    if (!isAuthenticated) navigate('/login');
  }, [isAuthenticated, navigate]);

  const conceptOptions = useMemo(
    () => masteries.map((mastery) => mastery.concept_tag),
    [masteries]
  );

  useEffect(() => {
    if (!selectedConcept && profile?.weak_concepts?.length) {
      setSelectedConcept(profile.weak_concepts[0]);
      return;
    }
    if (!selectedConcept && conceptOptions.length) {
      setSelectedConcept(conceptOptions[0]);
    }
  }, [profile?.weak_concepts, conceptOptions, selectedConcept]);

  useEffect(() => {
    if (!selectedConcept || !isAuthenticated) return;

    let cancelled = false;
    const fetchHistory = async () => {
      try {
        const data = await getMasteryHistory(selectedConcept);
        const trace = data?.trace || [];
        const normalized = trace.map((v, i) => ({
          step: i,
          mastery: v,
          score: Math.round(v * 100),
          label: `Step ${i}`,
        }));
        if (!cancelled) {
          setMasteryHistory(normalized);
        }
      } catch {
        if (!cancelled) {
          setMasteryHistory([]);
        }
      }
    };

    fetchHistory();
    return () => {
      cancelled = true;
    };
  }, [selectedConcept, isAuthenticated, getMasteryHistory]);

  const skillColor =
    {
      beginner: 'text-blue-400',
      intermediate: 'text-yellow-400',
      advanced: 'text-green-400',
    }[profile?.estimated_skill_level] || 'text-gray-400';

  if (loading) {
    return (
      <Layout>
        <LoadingSpinner text="Loading your dashboard..." />
      </Layout>
    );
  }

  const stats = [
    {
      label: 'Lessons completed',
      value: profile?.total_lessons_completed ?? 0,
    },
    {
      label: 'Problems solved',
      value: profile?.total_problems_solved ?? 0,
    },
    {
      label: 'Quizzes passed',
      value: profile?.total_quizzes_passed ?? 0,
    },
    {
      label: 'Learner ability',
      value: `${Math.round((profile?.learner_ability ?? 0) * 100)}%`,
    },
    {
      label: 'Dropout risk',
      value: `${((profile?.dropout_risk || 0) * 100).toFixed(0)}%`,
      warn: (profile?.dropout_risk || 0) > 0.5,
    },
    {
      label: 'Learning Velocity',
      value: profile?.learning_velocity
        ? `${Number(profile.learning_velocity).toFixed(1)}/wk`
        : '—',
      velocity: true,
    },
  ];

  return (
    <Layout>
      <motion.div
        variants={pageVariants}
        initial="hidden"
        animate="visible"
        className="min-h-screen bg-[#0a0a0a] text-white px-6 py-10 max-w-7xl mx-auto"
      >
        <motion.div variants={itemVariants} className="mb-8">
          <div className="flex items-center gap-3 mb-1 flex-wrap">
            <h1 className="text-3xl font-bold">
              Welcome back, {user?.full_name || user?.name || user?.username || 'Learner'}
            </h1>
            <span
              className={`text-sm font-medium px-3 py-1 rounded-full border ${skillColor} border-current capitalize`}
            >
              {profile?.estimated_skill_level || 'beginner'}
            </span>
          </div>
          <p className="text-gray-400">
            Overall mastery: {((profile?.overall_mastery || 0) * 100).toFixed(0)}% • Engagement:{' '}
            {((profile?.engagement_score || 0) * 100).toFixed(0)}%
            {profile?.learner_ability != null && (
              <> • Ability: {Math.round((profile.learner_ability || 0) * 100)}%</>
            )}
          </p>
        </motion.div>

        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-4 mb-8">
          {stats.map((stat) => (
            <motion.div
              key={stat.label}
              variants={itemVariants}
              className={`bg-[#111111] border border-[#222222] rounded-xl p-4 relative ${
                stat.warn ? 'animate-pulse ring-2 ring-red-500/50 ring-offset-2 ring-offset-[#111]' : ''
              }`}
              style={
                stat.velocity
                  ? {
                      background:
                        'linear-gradient(#111,#111) padding-box, linear-gradient(135deg,#E8392A,#f97316) border-box',
                      border: '1px solid transparent',
                    }
                  : undefined
              }
            >
              {stat.velocity && (
                <TrendingUp className="w-4 h-4 text-[#f97316] absolute top-4 right-4" />
              )}
              <p className="text-gray-500 text-xs mb-1">{stat.label}</p>
              <p
                className={`text-2xl font-bold ${stat.warn ? 'text-red-400' : 'text-white'}`}
              >
                {stat.value}
              </p>
              {stat.warn && (
                <div className="mt-3 text-xs text-red-300 bg-red-950/50 border border-red-900/60 rounded-lg px-2.5 py-2 flex items-start gap-2">
                  <AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                  <span>High dropout risk detected — keep your streak going!</span>
                </div>
              )}
            </motion.div>
          ))}
        </div>

        <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="lg:col-span-2 space-y-6">
            <MasteryRadar masteries={masteries} />
            <motion.div
              initial={{ opacity: 0, scaleY: 0.95 }}
              animate={{ opacity: 1, scaleY: 1 }}
              transition={{ duration: 0.5 }}
              className="bg-[#111111] border border-[#222222] rounded-xl p-6"
            >
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-5">
                <div>
                  <h3 className="text-base font-semibold text-gray-200">Mastery Trajectory</h3>
                  <p className="text-sm text-gray-400">
                    Track how your concept understanding improves over time.
                  </p>
                </div>
                <Select value={selectedConcept} onValueChange={setSelectedConcept}>
                  <SelectTrigger className="w-full md:w-[220px] bg-[#0d0d0d] border-[#222222]">
                    <SelectValue placeholder="Select concept" />
                  </SelectTrigger>
                  <SelectContent>
                    {conceptOptions.map((concept) => (
                      <SelectItem key={concept} value={concept}>
                        {concept.replace(/_/g, ' ')}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {masteryHistory.length > 0 ? (
                <div className="h-[260px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={masteryHistory}>
                      <defs>
                        <linearGradient id="masteryGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#E8392A" stopOpacity={0.45} />
                          <stop offset="100%" stopColor="#E8392A" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid stroke="#222222" strokeDasharray="3 3" />
                      <XAxis dataKey="label" stroke="#9ca3af" tick={{ fontSize: 11 }} />
                      <YAxis
                        stroke="#9ca3af"
                        tick={{ fontSize: 11 }}
                        domain={[0, 100]}
                        tickFormatter={(value) => `${value}%`}
                      />
                      <Tooltip
                        contentStyle={{
                          background: '#111111',
                          border: '1px solid #222222',
                          borderRadius: 12,
                          color: '#ffffff',
                        }}
                        formatter={(value) => [`${value}%`, 'Mastery']}
                      />
                      <Area
                        type="monotone"
                        dataKey="score"
                        stroke="#E8392A"
                        fill="url(#masteryGradient)"
                        strokeWidth={2}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <p className="text-sm text-gray-500">
                  No mastery history available for this concept yet.
                </p>
              )}
            </motion.div>
          </div>
          <div>
            <ContinueCard />
          </div>
        </motion.div>

        <motion.div variants={itemVariants} className="mb-8">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#E8392A] inline-block" />
            Recommended for you
          </h2>
          <motion.div
            variants={recommendationVariants}
            initial="hidden"
            animate="visible"
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
          >
            {recommendations.slice(0, 6).map((rec) => (
              <motion.div
                key={rec.id}
                variants={itemVariants}
                whileHover={{ y: -4, boxShadow: '0 8px 30px rgba(232,57,42,0.15)' }}
                whileTap={{ scale: 0.98 }}
              >
                <RecommendationCard rec={rec} />
              </motion.div>
            ))}
            {recommendations.length === 0 && (
              <p className="text-gray-500 col-span-3">
                Complete your onboarding to get personalized recommendations.
              </p>
            )}
          </motion.div>
        </motion.div>

        {profile?.weak_concepts?.length > 0 && (
          <motion.div variants={itemVariants}>
            <WeakConceptsPanel concepts={profile.weak_concepts} />
          </motion.div>
        )}
      </motion.div>
    </Layout>
  );
}
