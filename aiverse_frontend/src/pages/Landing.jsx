import React, { useState, useEffect, useRef, Suspense, lazy } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight, Brain, Code, BookOpen, MessageSquare, TrendingUp,
  Target, Zap, ChevronDown, Users, Award, Trophy, Flame, Crown,
  Star, BarChart2, Shield, Cpu, GitBranch, Layers, Swords
} from 'lucide-react';
import Layout from '../components/Layout';
import { motion, useScroll, useTransform, useInView } from 'framer-motion';
import api from '../api/axios';
import { GlowButton, SectionReveal, AnimatedCard } from '@/design-system';

const NeuralFieldHero = lazy(() => import('@/three-scenes/NeuralFieldHero'));

function AnimatedCounter({ target, duration = 2000, suffix = '' }) {
  const [count, setCount] = useState(0);
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });
  const startedRef = useRef(false);

  useEffect(() => {
    if (!isInView || startedRef.current) return;
    startedRef.current = true;

    const startTime = Date.now();
    const tick = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setCount(Math.floor(target * eased));
      if (progress < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }, [isInView, target, duration]);

  return (
    <span ref={ref}>{count.toLocaleString()}{suffix}</span>
  );
}

function HeroSection() {
  const { scrollY } = useScroll();
  const y = useTransform(scrollY, [0, 400], [0, 200]);
  const opacity = useTransform(scrollY, [0, 300], [1, 0]);

  return (
    <motion.section
      className="min-h-screen flex items-center justify-center relative overflow-hidden bg-background"
      style={{ y, opacity }}
    >
      {/* Neural network background (Three.js, lazy-loaded) */}
      <Suspense fallback={null}>
        <NeuralFieldHero />
      </Suspense>

      {/* Gradient overlays – red spectrum only */}
      <div className="absolute inset-0 pointer-events-none bg-gradient-to-b from-background/0 via-background/50 to-background" />
      <div className="absolute inset-0 pointer-events-none bg-[radial-gradient(circle_at_top,rgba(225,6,0,0.28),transparent_60%),radial-gradient(circle_at_bottom,rgba(198,40,40,0.35),transparent_65%)]" />

      {/* Grid overlay */}
      <div
        className="absolute inset-0 opacity-[0.06] mix-blend-screen pointer-events-none"
        style={{
          backgroundImage:
            'linear-gradient(rgba(148,163,184,0.25) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,0.25) 1px, transparent 1px)',
          backgroundSize: '64px 64px',
        }}
      />

      <div className="container mx-auto px-4 lg:px-8 relative z-10 py-20">
        <motion.div
          className="max-w-4xl mx-auto text-center"
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, ease: [0.22, 1, 0.36, 1] }}
        >
          {/* Top badge */}
          <motion.div
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-primary/25 bg-primary/10 text-primary text-xs font-mono tracking-wide mb-8"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.8 }}
          >
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            ML Engineering Platform for Serious Developers
          </motion.div>

          {/* Main heading */}
          <motion.h1
            className="text-5xl md:text-7xl font-bold text-foreground mb-6 leading-tight tracking-tight"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.8 }}
          >
            Train. Compete.
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary via-primary to-primary">
              Ship ML Systems.
            </span>
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto mb-10 leading-relaxed"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7, duration: 0.8 }}
          >
            18 real-world ML challenges. ELO-based ranking. Production constraints.
            Structured tracks from fundamentals to MLOps.
            Built for engineers who ship.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.9, duration: 0.8 }}
          >
            <Link to="/problems">
              <GlowButton className="px-8 py-3 text-base h-auto group">
                Start solving problems
                <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
              </GlowButton>
            </Link>
            <Link to="/tracks">
              <GlowButton
                variant="secondary"
                className="px-8 py-3 text-base h-auto group"
              >
                Explore learning tracks
                <GitBranch className="w-5 h-5 ml-2 group-hover:rotate-12 transition-transform" />
              </GlowButton>
            </Link>
          </motion.div>

          {/* Quick stats */}
          <motion.div
            className="flex items-center justify-center gap-8 mt-12 text-gray-500 text-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.2, duration: 0.8 }}
          >
            <span className="flex items-center gap-2">
              <Code className="w-4 h-4" />
              18 Problems
            </span>
            <span className="w-px h-4 bg-gray-700" />
            <span className="flex items-center gap-2">
              <Layers className="w-4 h-4" />
              4 Tracks
            </span>
            <span className="w-px h-4 bg-gray-700" />
            <span className="flex items-center gap-2">
              <Trophy className="w-4 h-4" />
              ELO Ranked
            </span>
          </motion.div>
        </motion.div>
      </div>

      {/* Scroll indicator */}
      <motion.div
        className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 text-gray-500"
        animate={{ y: [0, 10, 0] }}
        transition={{ duration: 2.5, repeat: Infinity }}
      >
        <span className="text-xs uppercase tracking-widest font-mono">Scroll</span>
        <ChevronDown className="w-4 h-4" />
      </motion.div>
    </motion.section>
  );
}

function StatsSection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });

  const stats = [
    { value: 18, suffix: '', label: 'ML Problems', icon: Code },
    { value: 4, suffix: '', label: 'Learning Tracks', icon: GitBranch },
    { value: 2000, suffix: '+', label: 'Rating Ceiling', icon: Trophy },
    { value: 5, suffix: '', label: 'Metric Types', icon: Target },
  ];

  return (
    <section className="py-20 bg-background border-b border-border" ref={ref}>
      <div className="container mx-auto px-4 lg:px-8">
        <motion.div
          className="grid grid-cols-2 md:grid-cols-4 gap-8"
          initial="hidden"
          animate={isInView ? "visible" : "hidden"}
          variants={{
            hidden: { opacity: 0 },
            visible: { opacity: 1, transition: { staggerChildren: 0.15 } },
          }}
        >
          {stats.map((stat, idx) => {
            const Icon = stat.icon;
            return (
              <motion.div
                key={idx}
                className="text-center"
                variants={{
                  hidden: { opacity: 0, y: 20 },
                  visible: { opacity: 1, y: 0 },
                }}
              >
                <Icon className="w-6 h-6 text-primary mx-auto mb-3 opacity-60" />
                <div className="text-4xl font-bold text-foreground mb-1 font-mono">
                  <AnimatedCounter target={stat.value} suffix={stat.suffix} />
                </div>
                <div className="text-sm text-muted-foreground">{stat.label}</div>
              </motion.div>
            );
          })}
        </motion.div>
      </div>
    </section>
  );
}

function PlatformSection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });

  const pillars = [
    {
      icon: Code, title: 'Real-World Problems',
      description: 'Credit risk, fraud detection, time series, recommender systems. Messy datasets with missing values, outliers, and class imbalance.',
      link: '/problems',
    },
    {
      icon: Trophy, title: 'ELO Rating System',
      description: 'Competitive ranking based on problem difficulty. Solve harder problems to climb faster. Global leaderboard sorted by rating.',
      link: '/leaderboard',
    },
    {
      icon: BookOpen, title: 'Courses',
      description: 'Free courses with lessons and progress tracking. Earn points and certificates upon completion.',
      link: '/learn',
    },
    {
      icon: MessageSquare, title: 'AI Mentor',
      description: 'Problem-aware AI assistant. Analyzes your progress, suggests learning paths, and helps with concepts. Never gives full solutions.',
      link: '/mentor',
    },
    {
      icon: Cpu, title: 'ML Playground',
      description: 'Upload datasets, run model comparisons, get feature importance charts. Cross-validation scoring with multiple algorithms.',
      link: '/playground',
    },
    {
      icon: BarChart2, title: 'Analytics Dashboard',
      description: 'Rating progression graph, submission trends, weak area detection, and personalized problem recommendations.',
      link: '/dashboard',
    },
  ];

  return (
    <section className="py-24 bg-secondary/30" ref={ref}>
      <div className="container mx-auto px-4 lg:px-8">
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
        >
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
            A Complete ML Engineering Ecosystem
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Not a tutorial site. A training and competitive evaluation platform
            for engineers building production ML systems.
          </p>
        </motion.div>

        <motion.div
          className="grid md:grid-cols-2 lg:grid-cols-4 gap-6"
          initial="hidden"
          animate={isInView ? "visible" : "hidden"}
          variants={{
            hidden: { opacity: 0 },
            visible: { opacity: 1, transition: { staggerChildren: 0.08 } },
          }}
        >
          {pillars.map((pillar, idx) => {
            const Icon = pillar.icon;
            return (
              <motion.div
                key={idx}
                variants={{
                  hidden: { opacity: 0, y: 20 },
                  visible: { opacity: 1, y: 0 },
                }}
              >
                <Link
                  to={pillar.link}
                  className="card-elevated p-6 h-full group hover:border-primary/30 transition-all duration-300 block"
                >
                  <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center mb-4 group-hover:bg-primary/20 transition-colors">
                    <Icon className="w-5 h-5 text-primary" />
                  </div>
                  <h3 className="font-bold text-foreground mb-2">{pillar.title}</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">{pillar.description}</p>
                </Link>
              </motion.div>
            );
          })}
        </motion.div>
      </div>
    </section>
  );
}

function DifficultyTiersSection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });

  const tiers = [
    {
      icon: Star, label: 'Easy', rating: 800, color: 'text-emerald-500', bg: 'bg-emerald-500/10',
      accent: 'border-emerald-500/30',
      problems: ['Linear Classification', 'Regression Basics', 'Imbalanced F1'],
    },
    {
      icon: Zap, label: 'Medium', rating: 1200, color: 'text-amber-500', bg: 'bg-amber-500/10',
      accent: 'border-amber-500/30',
      problems: ['Credit Risk', 'Fraud Detection', 'Customer Churn', 'Loan Default', 'House Prices'],
    },
    {
      icon: Flame, label: 'Hard', rating: 1600, color: 'text-orange-500', bg: 'bg-orange-500/10',
      accent: 'border-orange-500/30',
      problems: ['Time Series', 'Sentiment Analysis', 'Multi-Class', 'Feature Selection', 'Recommender'],
    },
    {
      icon: Crown, label: 'Expert', rating: 2000, color: 'text-red-500', bg: 'bg-red-500/10',
      accent: 'border-red-500/30',
      problems: ['Explainability', 'Hyperparameter Opt.', 'Prod Inference', 'Drift Detection', 'Pipeline Opt.'],
    },
  ];

  return (
    <section className="py-24" ref={ref}>
      <div className="container mx-auto px-4 lg:px-8">
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
        >
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
            Four Difficulty Tiers
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Problems rated by ELO difficulty. Solve harder problems to earn more rating points.
          </p>
        </motion.div>

        <motion.div
          className="grid md:grid-cols-2 lg:grid-cols-4 gap-6"
          initial="hidden"
          animate={isInView ? "visible" : "hidden"}
          variants={{
            hidden: { opacity: 0 },
            visible: { opacity: 1, transition: { staggerChildren: 0.12 } },
          }}
        >
          {tiers.map((tier, idx) => {
            const Icon = tier.icon;
            return (
              <motion.div
                key={idx}
                className={`p-6 rounded-xl border ${tier.accent} ${tier.bg} transition-all hover:scale-[1.02]`}
                variants={{
                  hidden: { opacity: 0, y: 30 },
                  visible: { opacity: 1, y: 0 },
                }}
              >
                <div className="flex items-center gap-3 mb-4">
                  <Icon className={`w-6 h-6 ${tier.color}`} />
                  <div>
                    <h3 className="font-bold text-foreground">{tier.label}</h3>
                    <span className="text-xs font-mono text-muted-foreground">{tier.rating} rating</span>
                  </div>
                </div>
                <ul className="space-y-2">
                  {tier.problems.map((p, i) => (
                    <li key={i} className="text-sm text-muted-foreground flex items-center gap-2">
                      <div className={`w-1.5 h-1.5 rounded-full ${tier.color.replace('text-', 'bg-')}`} />
                      {p}
                    </li>
                  ))}
                </ul>
              </motion.div>
            );
          })}
        </motion.div>
      </div>
    </section>
  );
}

function LeaderboardPreview() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });
  const [leaderboard, setLeaderboard] = useState([]);

  useEffect(() => {
    api.get('/api/leaderboard/global/')
      .then(res => {
        const data = res.data?.results || res.data || [];
        setLeaderboard(data.slice(0, 5));
      })
      .catch(() => {
        // Use placeholder data
        setLeaderboard([
          { rank: 1, username: '---', total_points: 0, problems_solved: 0 },
        ]);
      });
  }, []);

  return (
    <section className="py-24 bg-secondary/30" ref={ref}>
      <div className="container mx-auto px-4 lg:px-8">
        <motion.div
          className="max-w-2xl mx-auto"
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
        >
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-foreground mb-4">Live Leaderboard</h2>
            <p className="text-muted-foreground">Top performers ranked by ELO rating</p>
          </div>

          <AnimatedCard className="overflow-hidden">
            <div className="grid grid-cols-4 p-4 text-xs font-medium text-muted-foreground border-b border-border bg-muted/30">
              <div>Rank</div>
              <div>Engineer</div>
              <div className="text-right">Rating</div>
              <div className="text-right">Solved</div>
            </div>
            {leaderboard.length > 0 ? (
              leaderboard.map((entry, idx) => (
                <div key={idx} className="grid grid-cols-4 p-4 border-b border-border/50 last:border-0 hover:bg-muted/20 transition-colors">
                  <div className="font-mono font-bold">
                    {idx === 0 ? <Trophy className="w-4 h-4 text-amber-500 inline" /> : `#${entry.rank || idx + 1}`}
                  </div>
                  <div className="font-medium text-foreground">{entry.username || entry.user}</div>
                  <div className="text-right font-mono">{entry.total_points || entry.rating || 0}</div>
                  <div className="text-right text-muted-foreground">{entry.problems_solved || 0}</div>
                </div>
              ))
            ) : (
              <div className="p-8 text-center text-muted-foreground">
                No rankings yet. Be the first to solve a problem.
              </div>
            )}
          </AnimatedCard>

          <div className="text-center mt-6">
            {/* <Link to="/leaderboard">
              <GlowButton
                variant="secondary"
                className="group px-6 py-2 text-sm h-auto"
              >
                <span>View Full Leaderboard</span>
                <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
              </GlowButton>
            </Link> */}
          </div>
        </motion.div>
      </div>
    </section>
  );
}

function CTASection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });

  return (
    <section className="py-24" ref={ref}>
      <div className="container mx-auto px-4 lg:px-8">
        <motion.div
          className="max-w-4xl mx-auto text-center"
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
        >
          <div className="p-12 lg:p-16 rounded-2xl bg-gradient-to-br from-primary to-accent text-primary-foreground relative overflow-hidden">
            {/* Background pattern */}
            <div className="absolute inset-0 opacity-10" style={{
              backgroundImage: 'radial-gradient(circle at 2px 2px, white 1px, transparent 0)',
              backgroundSize: '40px 40px',
            }} />

            <div className="relative z-10">
              <h2 className="text-3xl md:text-4xl font-bold mb-4">
                Ready to Build Real ML Skills?
              </h2>
              <p className="text-lg opacity-90 mb-8 max-w-2xl mx-auto">
                Join engineers who solve production-grade ML problems,
                compete in ranked challenges, and ship models that work.
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <Link to="/register">
                  <GlowButton
                    size="lg"
                    variant="secondary"
                    className="bg-background text-primary hover:bg-background/90 text-base px-8 py-6 h-auto font-bold"
                  >
                    <span>Create Free Account</span>
                    <ArrowRight className="w-5 h-5 ml-2" />
                  </GlowButton>
                </Link>
                <Link to="/problems">
                  <GlowButton
                    size="lg"
                    variant="tertiary"
                    className="border-2 border-white/30 text-white hover:bg-white/10 text-base px-8 py-6 h-auto"
                  >
                    <span>Browse Problems</span>
                  </GlowButton>
                </Link>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

export default function Landing() {
  return (
    <Layout>
      <HeroSection />
      <StatsSection />
      <PlatformSection />
      <DifficultyTiersSection />
      <LeaderboardPreview />
      <CTASection />
    </Layout>
  );
}
