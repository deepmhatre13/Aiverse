import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLearner } from '../contexts/LearnerContext';
import { useState, useEffect } from 'react';
import {
  Menu, X, ChevronDown, User, LogOut, BookOpen, Code, MessageSquare,
  BarChart3, Trophy, Activity, Database, Zap, Settings, HelpCircle, Flame,
} from 'lucide-react';
import { motion } from 'framer-motion';
import { Button } from './ui/button';
import ThemeToggle from './ThemeToggle';
import api from '../api/axios';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from './ui/dropdown-menu';

const baseNavLinks = [
  { name: 'Problems', href: '/problems', icon: Code, key: 'problems' },
  { name: 'Learn', href: '/learn', icon: BookOpen, key: 'learn' },
  { name: 'Mentor', href: '/mentor', icon: MessageSquare, key: 'mentor' },
  { name: 'Playground', href: '/playground', icon: Zap, key: 'playground' },
  { name: 'Discussions', href: '/discussions', icon: MessageSquare, key: 'discussions' },
  { name: 'Live', href: '/live', icon: Activity, key: 'live' },
];

const authNavLinks = [
  { name: 'Dashboard', href: '/dashboard', icon: BarChart3, key: 'dashboard' },
  { name: 'Skills', href: '/skills', icon: Database, key: 'skills' },
];

function NavLinkItem({ link, isActive, badge, showDot, dotColor = 'bg-red-500' }) {
  return (
    <Link
      to={link.href}
      className={`relative px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
        isActive(link.href)
          ? 'bg-primary/10 text-primary'
          : 'text-muted-foreground hover:text-foreground hover:bg-muted'
      }`}
    >
      <span className="flex items-center gap-2">
        {link.name}
        {showDot && (
          <span className={`w-2 h-2 rounded-full ${dotColor} ${link.key === 'learn' ? 'animate-pulse' : ''}`} />
        )}
        {badge && (
          <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-primary/15 text-primary font-semibold">
            {badge}
          </span>
        )}
      </span>
    </Link>
  );
}

export default function Navbar() {
  const { isAuthenticated, user, logout } = useAuth();
  const { profile, recommendations } = useLearner();
  const location = useLocation();
  const navigate = useNavigate();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [courseProgress, setCourseProgress] = useState(null);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const isActive = (path) => location.pathname.startsWith(path);
  const onLearnPage = location.pathname.startsWith('/learn');

  const recommendedProblemsCount = isAuthenticated
    ? recommendations.filter((r) =>
        r.recommendation_type === 'coding_problem' ||
        r.recommendation_type === 'practice' ||
        r.content_type === 'problem'
      ).length
    : 0;

  const nextLessonRec = recommendations.find((r) =>
    r.recommendation_type === 'next_lesson' || r.recommendation_type === 'next'
  );
  const frustrationHigh = (profile?.frustration_score || 0) > 0.6;

  useEffect(() => {
    if (!isAuthenticated || !onLearnPage) {
      setCourseProgress(null);
      return;
    }
    api.get('/api/learn/progress/summary/')
      .then((res) => setCourseProgress(res.data))
      .catch(() => setCourseProgress(null));
  }, [isAuthenticated, onLearnPage, location.pathname]);

  const navLinks = isAuthenticated
    ? [...baseNavLinks.slice(0, 2), ...authNavLinks, ...baseNavLinks.slice(2)]
    : baseNavLinks;

  const getNavBadge = (key) => {
    if (!isAuthenticated) return null;
    if (key === 'problems' && recommendedProblemsCount >= 3) {
      return `${recommendedProblemsCount} for you`;
    }
    if (key === 'learn' && nextLessonRec) return 'Resume';
    if (key === 'mentor' && frustrationHigh) return 'Help available';
    return null;
  };

  const getNavDot = (key) => {
    if (!isAuthenticated) return false;
    if (key === 'problems' && recommendedProblemsCount >= 3) return true;
    if (key === 'learn' && profile?.last_activity_at) {
      const hoursSince = (Date.now() - new Date(profile.last_activity_at).getTime()) / 3600000;
      if (hoursSince >= 48) return true;
    }
    if (key === 'mentor' && frustrationHigh) return true;
    return false;
  };

  const getDotColor = (key) => (key === 'mentor' ? 'bg-orange-500' : 'bg-red-500');

  const displayName = user?.full_name || user?.name || user?.username || 'User';
  const avatarInitial = (displayName[0] || 'U').toUpperCase();

  const progressPercent = courseProgress?.progress_percent || 0;
  const progressLabel = courseProgress?.total
    ? `${courseProgress.completed}/${courseProgress.total} lessons`
    : null;

  const highRisk = (profile?.dropout_risk || 0) > 0.5;
  const streakDays = profile?.streak_days ?? 0;

  return (
    <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-border/50">
      <nav className="container mx-auto px-4 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-2 group">
            <div className="w-8 h-8 rounded-lg gradient-wine flex items-center justify-center">
              <span className="text-primary-foreground font-serif font-bold text-lg">A</span>
            </div>
            <span className="font-serif text-xl font-semibold text-foreground group-hover:text-primary transition-colors">
              Aiverse
            </span>
          </Link>

          <div className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => (
              <NavLinkItem
                key={link.name}
                link={link}
                isActive={isActive}
                badge={getNavBadge(link.key)}
                showDot={getNavDot(link.key)}
                dotColor={getDotColor(link.key)}
              />
            ))}
          </div>

          <div className="hidden md:flex items-center gap-3">
            <ThemeToggle />
            {isAuthenticated ? (
              <>
                {streakDays > 0 && (
                  <motion.div
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    className="flex items-center gap-1 text-xs text-orange-400 cursor-default"
                  >
                    <Flame className="w-3.5 h-3.5" />
                    <span>{streakDays}d</span>
                  </motion.div>
                )}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="flex items-center gap-2">
                    <div className="relative">
                      <div className="w-8 h-8 rounded-full bg-[#E8392A] flex items-center justify-center">
                        <span className="text-white font-bold text-sm">{avatarInitial}</span>
                      </div>
                      {highRisk && (
                        <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-red-500 rounded-full animate-pulse z-10" />
                      )}
                    </div>
                    <span className="text-sm font-medium">{displayName}</span>
                    <ChevronDown className="w-4 h-4 text-muted-foreground" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuItem asChild>
                    <Link to="/dashboard" className="flex items-center gap-2">
                      <BarChart3 className="w-4 h-4" />
                      Dashboard
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link to="/skills" className="flex items-center gap-2">
                      <Database className="w-4 h-4" />
                      My Skills
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link to="/leaderboard" className="flex items-center gap-2">
                      <Trophy className="w-4 h-4" />
                      Leaderboard
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild>
                    <Link to="/settings" className="flex items-center gap-2">
                      <Settings className="w-4 h-4" />
                      Settings
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link to="/help" className="flex items-center gap-2">
                      <HelpCircle className="w-4 h-4" />
                      Help
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleLogout} className="text-destructive">
                    <LogOut className="w-4 h-4 mr-2" />
                    Sign out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
              </>
            ) : (
              <>
                <Link to="/login">
                  <Button variant="ghost" size="sm">Sign In</Button>
                </Link>
                <Link to="/register">
                  <Button size="sm" className="btn-wine">Get Started</Button>
                </Link>
              </>
            )}
          </div>

          <button
            className="md:hidden p-2 rounded-lg hover:bg-muted transition-colors"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          >
            {isMobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {onLearnPage && isAuthenticated && progressPercent > 0 && (
          <div className="relative h-0.5 bg-muted/50">
            <div
              className="absolute inset-y-0 left-0 bg-[#E8392A] transition-all duration-500"
              style={{ width: `${progressPercent}%` }}
              title={progressLabel || undefined}
            />
          </div>
        )}

        {isMobileMenuOpen && (
          <div className="md:hidden py-4 border-t border-border/50">
            <div className="flex flex-col gap-2">
              {navLinks.map((link) => (
                <Link
                  key={link.name}
                  to={link.href}
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all ${
                    isActive(link.href)
                      ? 'bg-primary/10 text-primary'
                      : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                  }`}
                >
                  <link.icon className="w-5 h-5" />
                  {link.name}
                  {getNavBadge(link.key) && (
                    <span className="ml-auto text-[10px] px-2 py-0.5 rounded-full bg-primary/15 text-primary">
                      {getNavBadge(link.key)}
                    </span>
                  )}
                </Link>
              ))}
              <div className="border-t border-border/50 my-2" />
              {isAuthenticated ? (
                <>
                  <Link to="/dashboard" onClick={() => setIsMobileMenuOpen(false)} className="flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted">
                    <BarChart3 className="w-5 h-5" /> Dashboard
                  </Link>
                  <Link to="/skills" onClick={() => setIsMobileMenuOpen(false)} className="flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted">
                    <Database className="w-5 h-5" /> Skills
                  </Link>
                  <Link to="/leaderboard" onClick={() => setIsMobileMenuOpen(false)} className="flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted">
                    <Trophy className="w-5 h-5" /> Leaderboard
                  </Link>
                  <button
                    onClick={() => { handleLogout(); setIsMobileMenuOpen(false); }}
                    className="flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-destructive hover:bg-destructive/10"
                  >
                    <LogOut className="w-5 h-5" /> Sign out
                  </button>
                </>
              ) : (
                <div className="flex flex-col gap-2 px-4">
                  <Link to="/login" onClick={() => setIsMobileMenuOpen(false)}>
                    <Button variant="outline" className="w-full">Sign In</Button>
                  </Link>
                  <Link to="/register" onClick={() => setIsMobileMenuOpen(false)}>
                    <Button className="w-full btn-wine">Get Started</Button>
                  </Link>
                </div>
              )}
            </div>
          </div>
        )}
      </nav>
    </header>
  );
}
