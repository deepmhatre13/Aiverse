import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Search, Filter, Code, BarChart2, Layers, ChevronRight, Trophy, Zap, Flame, Crown, Star } from 'lucide-react';
import Layout from '../components/Layout';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorState from '../components/ErrorState';
import EmptyState from '../components/EmptyState';
import api from '../api/axios';

const difficultyConfig = {
  easy: {
    color: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
    icon: Star,
    rating: 800,
    label: 'Easy',
    border: 'border-emerald-200 dark:border-emerald-800',
  },
  medium: {
    color: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
    icon: Zap,
    rating: 1200,
    label: 'Medium',
    border: 'border-amber-200 dark:border-amber-800',
  },
  hard: {
    color: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
    icon: Flame,
    rating: 1600,
    label: 'Hard',
    border: 'border-orange-200 dark:border-orange-800',
  },
  expert: {
    color: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    icon: Crown,
    rating: 2000,
    label: 'Expert',
    border: 'border-red-200 dark:border-red-800',
  },
};

const categoryLabels = {
  fundamentals: 'Fundamentals',
  finance: 'Finance',
  business: 'Business',
  real_estate: 'Real Estate',
  forecasting: 'Forecasting',
  nlp: 'NLP',
  manufacturing: 'Manufacturing',
  biomedical: 'Biomedical',
  recommendations: 'Recommendations',
  mlops: 'MLOps',
  optimization: 'Optimization',
  production: 'Production',
  engineering: 'Engineering',
  general: 'General',
};

const typeIcons = {
  classification: Layers,
  regression: BarChart2,
  clustering: Code,
};

function ProblemCard({ problem }) {
  const problemType = problem.problem_type || problem.type;
  const TypeIcon = typeIcons[problemType] || Code;
  const difficulty = problem.difficulty || 'easy';
  const config = difficultyConfig[difficulty] || difficultyConfig.easy;
  const DiffIcon = config.icon;
  const category = categoryLabels[problem.category] || problem.category || '';
  const hasConstraints = problem.constraints && Object.keys(problem.constraints).length > 0;

  return (
    <Link
      to={`/problems/${problem.slug}`}
      className={`card-elevated p-6 group hover:border-primary/30 transition-all duration-300 relative overflow-hidden`}
    >
      {/* Difficulty accent bar */}
      <div className={`absolute top-0 left-0 right-0 h-1 ${difficulty === 'easy' ? 'bg-emerald-500' : difficulty === 'medium' ? 'bg-amber-500' : difficulty === 'hard' ? 'bg-orange-500' : 'bg-red-500'}`} />

      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
            <TypeIcon className="w-5 h-5 text-primary" />
          </div>
          <div>
            <span className="label-text capitalize text-xs">{problemType}</span>
            {category && (
              <span className="text-xs text-muted-foreground ml-2 opacity-70">{category}</span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {hasConstraints && (
            <Badge variant="outline" className="text-xs border-primary/30 text-primary">
              <Zap className="w-3 h-3 mr-1" />
              Constrained
            </Badge>
          )}
          {problem.has_hidden_tests && (
            <Badge variant="outline" className="text-xs border-primary/30 text-primary dark:text-primary">
              Hidden Tests
            </Badge>
          )}
          <Badge className={`${config.color} flex items-center gap-1`}>
            <DiffIcon className="w-3 h-3" />
            {config.label}
          </Badge>
        </div>
      </div>

      <h3 className="font-serif text-lg font-medium text-foreground mb-2 group-hover:text-primary transition-colors">
        {problem.title}
      </h3>

      <div className="flex items-center justify-between mt-4">
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          {problem.metric && (
            <span className="flex items-center gap-1">
              <Trophy className="w-3 h-3" />
              {problem.metric.toUpperCase()}
            </span>
          )}
          {problem.difficulty_rating && (
            <span className="font-mono text-xs font-medium">
              {problem.difficulty_rating} pts
            </span>
          )}
        </div>
        <ChevronRight className="w-4 h-4 text-muted-foreground group-hover:text-primary group-hover:translate-x-1 transition-all" />
      </div>
    </Link>
  );
}

export default function Problems() {
  const [problems, setProblems] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDifficulty, setSelectedDifficulty] = useState('all');
  const [selectedType, setSelectedType] = useState('all');
  const [selectedCategory, setSelectedCategory] = useState('all');

  useEffect(() => {
    fetchProblems();
  }, []);

  const fetchProblems = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await api.get('/api/ml/problems/');
      setProblems(response.data.results || response.data || []);
    } catch (err) {
      if (err.response?.status === 401 || err.response?.status === 403) {
        setProblems([]);
        setError(null);
      } else {
        const errorMessage = err.response?.data?.message || err.response?.data?.detail || 'Failed to load problems';
        setError(errorMessage);
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Extract unique categories from problems
  const categories = [...new Set(problems.map(p => p.category).filter(Boolean))];

  const filteredProblems = problems.filter((problem) => {
    const problemType = problem.problem_type || problem.type;
    const matchesSearch = problem.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (problem.description && problem.description.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesDifficulty = selectedDifficulty === 'all' || !problem.difficulty || problem.difficulty === selectedDifficulty;
    const matchesType = selectedType === 'all' || problemType === selectedType;
    const matchesCategory = selectedCategory === 'all' || problem.category === selectedCategory;
    return matchesSearch && matchesDifficulty && matchesType && matchesCategory;
  });

  // Group by difficulty for section display
  const groupedProblems = {
    easy: filteredProblems.filter(p => p.difficulty === 'easy'),
    medium: filteredProblems.filter(p => p.difficulty === 'medium'),
    hard: filteredProblems.filter(p => p.difficulty === 'hard'),
    expert: filteredProblems.filter(p => p.difficulty === 'expert'),
  };

  const totalCount = filteredProblems.length;
  const showGrouped = selectedDifficulty === 'all' && !searchQuery;

  return (
    <Layout>
      <div className="container mx-auto px-4 lg:px-8 py-12">
        {/* Header */}
        <div className="mb-12">
          <h1 className="heading-primary text-foreground mb-4">ML Problems</h1>
          <p className="body-large text-muted-foreground max-w-2xl">
            {totalCount} real-world machine learning challenges across {Object.keys(difficultyConfig).length} difficulty tiers.
            Solve problems, earn rating points, climb the leaderboard.
          </p>
        </div>

        {/* Difficulty Stats Bar */}
        <div className="grid grid-cols-4 gap-4 mb-8">
          {Object.entries(difficultyConfig).map(([key, config]) => {
            const count = problems.filter(p => p.difficulty === key).length;
            const DIcon = config.icon;
            return (
              <button
                key={key}
                onClick={() => setSelectedDifficulty(selectedDifficulty === key ? 'all' : key)}
                className={`p-4 rounded-lg border transition-all ${
                  selectedDifficulty === key
                    ? `${config.border} bg-primary/5 shadow-sm`
                    : 'border-border hover:border-primary/20'
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <DIcon className="w-4 h-4" />
                  <span className="text-sm font-medium">{config.label}</span>
                </div>
                <div className="text-2xl font-bold">{count}</div>
                <div className="text-xs text-muted-foreground">{config.rating} rating</div>
              </button>
            );
          })}
        </div>

        {/* Filters */}
        <div className="flex flex-col lg:flex-row gap-4 mb-8">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
            <Input
              placeholder="Search problems..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 h-11"
            />
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Type:</span>
            </div>
            <div className="flex gap-2">
              {['all', 'classification', 'regression'].map((type) => (
                <Button
                  key={type}
                  variant={selectedType === type ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setSelectedType(type)}
                  className={selectedType === type ? 'btn-wine' : ''}
                >
                  {type === 'all' ? 'All' : type.charAt(0).toUpperCase() + type.slice(1)}
                </Button>
              ))}
            </div>
          </div>

          {categories.length > 0 && (
            <div className="flex items-center gap-3">
              <span className="text-sm text-muted-foreground">Category:</span>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="h-9 rounded-md border border-input bg-background px-3 text-sm"
              >
                <option value="all">All Categories</option>
                {categories.map((cat) => (
                  <option key={cat} value={cat}>
                    {categoryLabels[cat] || cat}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {/* Content */}
        {isLoading ? (
          <LoadingSpinner text="Loading problems..." />
        ) : error ? (
          <ErrorState message={error} onRetry={fetchProblems} />
        ) : filteredProblems.length === 0 ? (
          <EmptyState
            icon={Code}
            title="No problems found"
            message={searchQuery ? "Try adjusting your search or filters" : "Problems will appear here once available"}
          />
        ) : showGrouped ? (
          // Grouped view by difficulty
          <div className="space-y-12">
            {Object.entries(groupedProblems).map(([difficulty, probs]) => {
              if (probs.length === 0) return null;
              const config = difficultyConfig[difficulty];
              const DIcon = config.icon;
              return (
                <div key={difficulty}>
                  <div className="flex items-center gap-3 mb-6">
                    <DIcon className="w-5 h-5" />
                    <h2 className="text-xl font-bold">{config.label}</h2>
                    <Badge variant="outline" className="text-xs">{config.rating} rating</Badge>
                    <span className="text-sm text-muted-foreground">{probs.length} problems</span>
                  </div>
                  <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {probs.map((problem) => (
                      <ProblemCard key={problem.id || problem.slug} problem={problem} />
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          // Flat grid view (when filtered)
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredProblems.map((problem) => (
              <ProblemCard key={problem.id || problem.slug} problem={problem} />
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
