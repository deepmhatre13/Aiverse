import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  ArrowLeft, 
  Play, 
  Send, 
  FileText, 
  CheckCircle, 
  XCircle, 
  Clock, 
  AlertCircle, 
  Database, 
  Shield, 
  TrendingUp, 
  Zap, 
  HardDrive,
  Target,
  Code,
  Activity
} from 'lucide-react';
import Editor from '@monaco-editor/react';
import Layout from '../components/Layout';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorState from '../components/ErrorState';
import api from '../api/axios';
import { toast } from 'sonner';

// Blank starter code - no model hints, no imports, no solution direction
// Users must solve problems from scratch like a real competitive coding environment
const BLANK_STARTER_CODE = `def train_and_predict(X_train, y_train, X_test):
    pass
`;

// Difficulty rating colors
const difficultyColors = {
  800: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
  1200: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
  1600: 'bg-orange-500/10 text-orange-400 border-orange-500/30',
  2000: 'bg-red-500/10 text-red-400 border-red-500/30',
};

const difficultyLabels = {
  800: 'Easy',
  1200: 'Medium',
  1600: 'Hard',
  2000: 'Expert',
};

// Error banner component for better error display
function ErrorBanner({ error }) {
  if (!error) return null;
  
  return (
    <div className="border-2 border-red-500/50 bg-red-500/5 p-4 mb-4">
      <div className="flex items-start gap-3">
        <XCircle className="w-5 h-5 text-red-400 mt-0.5 shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="font-mono text-sm font-bold text-red-400 mb-1">
            {error.error_type || 'ERROR'}
          </div>
          <p className="font-mono text-sm text-red-300/90 whitespace-pre-wrap break-words">
            {error.message}
          </p>
          {error.stack_trace && process.env.NODE_ENV === 'development' && (
            <details className="mt-3">
              <summary className="font-mono text-xs text-red-400/70 cursor-pointer hover:text-red-400">
                Stack Trace (Dev Mode)
              </summary>
              <pre className="mt-2 text-xs text-red-400/60 whitespace-pre-wrap overflow-x-auto">
                {error.stack_trace}
              </pre>
            </details>
          )}
        </div>
      </div>
    </div>
  );
}

// Evaluation result panel
function EvaluationPanel({ results, problem }) {
  if (!results) return null;
  
  const isSuccess = results.status === 'success' || results.status === 'accepted';
  const isRejected = results.status === 'rejected';
  const isError = !isSuccess && !isRejected;
  
  const borderColor = isSuccess 
    ? 'border-emerald-500/50' 
    : isRejected 
    ? 'border-orange-500/50'
    : 'border-red-500/50';
  
  const bgColor = isSuccess 
    ? 'bg-emerald-500/5' 
    : isRejected 
    ? 'bg-orange-500/5'
    : 'bg-red-500/5';
  
  const statusColor = isSuccess 
    ? 'text-emerald-400' 
    : isRejected 
    ? 'text-orange-400'
    : 'text-red-400';

  if (isError && results.error_type) {
    return <ErrorBanner error={results} />;
  }

  return (
    <div className={`border-2 ${borderColor} ${bgColor} p-4 mb-4`}>
      {/* Status Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          {isSuccess ? (
            <CheckCircle className="w-5 h-5 text-emerald-400" />
          ) : (
            <XCircle className={`w-5 h-5 ${statusColor}`} />
          )}
          <span className={`font-mono font-bold text-sm uppercase tracking-wider ${statusColor}`}>
            {isSuccess ? 'SUCCESS' : isRejected ? 'BELOW THRESHOLD' : 'ERROR'}
          </span>
        </div>
        {results.meets_threshold !== undefined && (
          <Badge className={`font-mono text-xs ${results.meets_threshold ? 'bg-emerald-500/20 text-emerald-400' : 'bg-orange-500/20 text-orange-400'}`}>
            {results.meets_threshold ? 'Threshold Met' : 'Threshold Not Met'}
          </Badge>
        )}
      </div>
      
      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {results.score !== undefined && results.score !== null && (
          <div className="bg-foreground/5 dark:bg-black/20 p-3 border border-border/30">
            <div className="text-[10px] text-muted-foreground uppercase tracking-wider font-mono mb-1">Score</div>
            <div className="text-lg font-mono font-bold text-foreground">
              {typeof results.score === 'number' ? results.score.toFixed(4) : results.score}
            </div>
          </div>
        )}
        
        {(results.threshold || problem?.submission_threshold) && (
          <div className="bg-foreground/5 dark:bg-black/20 p-3 border border-border/30">
            <div className="text-[10px] text-muted-foreground uppercase tracking-wider font-mono mb-1">Threshold</div>
            <div className="text-lg font-mono font-bold text-foreground">
              {problem?.higher_is_better ? '≥' : '≤'} {(results.threshold || problem?.submission_threshold)?.toFixed(2)}
            </div>
          </div>
        )}
        
        {results.latency_ms !== undefined && results.latency_ms !== null && (
          <div className="bg-foreground/5 dark:bg-black/20 p-3 border border-border/30">
            <div className="text-[10px] text-muted-foreground uppercase tracking-wider font-mono mb-1 flex items-center gap-1">
              <Zap className="w-3 h-3" /> Latency
            </div>
            <div className="text-lg font-mono font-bold text-foreground">
              {results.latency_ms.toFixed(0)}ms
            </div>
          </div>
        )}
        
        {results.memory_mb !== undefined && results.memory_mb !== null && (
          <div className="bg-foreground/5 dark:bg-black/20 p-3 border border-border/30">
            <div className="text-[10px] text-muted-foreground uppercase tracking-wider font-mono mb-1 flex items-center gap-1">
              <HardDrive className="w-3 h-3" /> Memory
            </div>
            <div className="text-lg font-mono font-bold text-foreground">
              {results.memory_mb.toFixed(1)}MB
            </div>
          </div>
        )}
      </div>
      
      {/* Reason (if rejected) */}
      {results.reason && (
        <div className="mt-3 pt-3 border-t border-white/5">
          <p className="font-mono text-xs text-muted-foreground">{results.reason}</p>
        </div>
      )}
    </div>
  );
}

export default function ProblemDetail() {
  const { slug } = useParams();
  const [problem, setProblem] = useState(null);
  const [code, setCode] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [results, setResults] = useState(null);
  const [submissions, setSubmissions] = useState([]);
  const [selectedSubmission, setSelectedSubmission] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedMetric, setSelectedMetric] = useState('default');
  const [canSubmit, setCanSubmit] = useState(false);

  useEffect(() => {
    fetchProblem();
    fetchSubmissionHistory();
  }, [slug]);

  useEffect(() => {
    if (problem) {
      // Set blank starter code - no model hints or solution direction
      // Competitive ML environment: users solve from scratch
      setCode(BLANK_STARTER_CODE);
      setCanSubmit(false);
      setResults(null);
    }
  }, [problem]);

  useEffect(() => {
    setCanSubmit(false);
  }, [code]);

  const fetchProblem = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await api.get(`/api/ml/problems/${slug}/`);
      setProblem(response.data);
    } catch (err) {
      const errorMessage = err.response?.data?.message || err.response?.data?.detail || err.message || 'Failed to load problem';
      setError(errorMessage);
      console.error('Error fetching problem:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchSubmissionHistory = async () => {
    try {
      const response = await api.get(`/api/ml/problems/${slug}/submissions/`);
      setSubmissions(response.data.submissions || []);
    } catch (err) {
      console.error('Error fetching submission history:', err);
      setSubmissions([]);
    }
  };

  const fetchSubmissionDetails = async (submissionId) => {
    try {
      const response = await api.get(`/api/ml/submissions/${submissionId}/`);
      setSelectedSubmission(response.data);
    } catch (err) {
      toast.error('Failed to load submission details');
      console.error('Error fetching submission details:', err);
    }
  };

  const handleEvaluate = async () => {
    try {
      setIsEvaluating(true);
      setResults(null);
      
      const payload = { code };
      if (selectedMetric && selectedMetric !== 'default') {
        payload.metric = selectedMetric;
      }
      
      const response = await api.post(`/api/ml/problems/${slug}/evaluate/`, payload);
      setResults(response.data);
      setActiveTab('submissions');

      if (response.data.status === 'success') {
        const meets = response.data.meets_threshold ?? false;
        setCanSubmit(meets);
        toast.success(meets ? 'Evaluation passed! You can submit.' : 'Evaluation complete but below threshold.');
      } else {
        setCanSubmit(false);
        // Don't toast on structured errors - ErrorBanner will show them
        if (!response.data.error_type) {
          toast.error(response.data.message || 'Evaluation failed');
        }
      }
    } catch (err) {
      setCanSubmit(false);
      // Create structured error result for ErrorBanner
      const errorResult = {
        status: 'error',
        error_type: err.response?.data?.error_type || 'NETWORK_ERROR',
        message: err.response?.data?.message || err.response?.data?.detail || 'Failed to connect to evaluation server'
      };
      setResults(errorResult);
      setActiveTab('submissions');
      console.error('Evaluation error:', err);
    } finally {
      setIsEvaluating(false);
    }
  };

  const handleSubmit = async () => {
    if (!canSubmit) {
      toast.error('Please run Evaluate and meet the threshold before submitting.');
      return;
    }

    try {
      setIsSubmitting(true);
      setResults(null);

      const payload = { code };
      if (selectedMetric && selectedMetric !== 'default') {
        payload.metric = selectedMetric;
      }
      
      const response = await api.post(`/api/ml/problems/${slug}/submit/`, payload);
      setResults(response.data);
      setActiveTab('submissions');

      if (response.data.status === 'accepted') {
        toast.success(`Submission accepted! Score: ${response.data.score?.toFixed(4)}`);
        await fetchSubmissionHistory();
        window.dispatchEvent(new CustomEvent('submission-completed', { 
          detail: { problemSlug: slug, status: 'accepted' } 
        }));
      } else if (response.data.status === 'rejected') {
        // Don't show toast for rejected - ErrorBanner/Panel shows reason
      } else if (response.data.error_type) {
        // Don't toast on structured errors - ErrorBanner will show them
      } else {
        toast.error(response.data.message || 'Submission failed');
      }
    } catch (err) {
      // Create structured error result for ErrorBanner
      const errorResult = {
        status: 'error',
        error_type: err.response?.data?.error_type || 'NETWORK_ERROR',
        message: err.response?.data?.message || err.response?.data?.detail || 'Failed to connect to submission server'
      };
      setResults(errorResult);
      setActiveTab('submissions');
      console.error('Submission error:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <Layout showFooter={false}>
        <div className="min-h-[80vh] flex items-center justify-center bg-card dark:bg-[#0a0a0a]">
          <LoadingSpinner text="Loading problem..." />
        </div>
      </Layout>
    );
  }

  if (error || !problem) {
    return (
      <Layout showFooter={false}>
        <div className="container mx-auto px-4 py-12 bg-card dark:bg-[#0a0a0a]">
          <ErrorState message={error || 'Problem not found'} onRetry={fetchProblem} />
        </div>
      </Layout>
    );
  }

  const difficultyRating = problem.difficulty_rating || 800;
  const ratingColor = difficultyColors[difficultyRating] || difficultyColors[800];
  const ratingLabel = difficultyLabels[difficultyRating] || 'Easy';
  const metricName = problem.metric || problem.default_metric || 'accuracy';
  const threshold = problem.submission_threshold || problem.threshold;

  return (
    <Layout showFooter={false}>
      <div className="h-screen flex flex-col overflow-hidden bg-background">
        {/* Header */}
        <div className="border-b border-border bg-card dark:bg-[#0a0a0a] px-6 py-3 shrink-0">
          <div className="container mx-auto flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link to="/problems" className="text-muted-foreground hover:text-foreground transition-colors">
                <ArrowLeft className="w-5 h-5" />
              </Link>
              <div>
                <div className="flex items-center gap-3">
                  <h1 className="font-mono text-lg font-bold text-foreground tracking-tight">{problem.title}</h1>
                  <Badge className={`${ratingColor} border font-mono text-[10px] px-2 py-0.5`}>
                    {ratingLabel} ({difficultyRating})
                  </Badge>
                </div>
                <div className="flex items-center gap-4 mt-1">
                  <span className="text-[10px] text-muted-foreground uppercase tracking-wider font-mono">
                    {problem.problem_type || problem.task_type}
                  </span>
                  <div className="flex items-center gap-1.5">
                    <Target className="w-3 h-3 text-muted-foreground" />
                    <span className="text-[10px] text-muted-foreground font-mono uppercase">
                      {metricName}
                    </span>
                  </div>
                  {threshold && (
                    <div className="flex items-center gap-1.5">
                      <Activity className="w-3 h-3 text-muted-foreground" />
                      <span className="text-[10px] text-muted-foreground font-mono">
                        {problem.higher_is_better ? '≥' : '≤'} {threshold}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleEvaluate}
                disabled={isEvaluating || isSubmitting || !code.trim()}
                className="border-border text-foreground/80 hover:bg-muted dark:bg-zinc-800 hover:text-foreground font-mono text-xs h-8"
              >
                {isEvaluating ? (
                  <Clock className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                ) : (
                  <Play className="w-3.5 h-3.5 mr-1.5" />
                )}
                Evaluate
              </Button>
              <Button
                size="sm"
                onClick={handleSubmit}
                disabled={isEvaluating || isSubmitting || !canSubmit}
                className="bg-white text-black hover:bg-zinc-200 font-mono text-xs font-bold h-8"
              >
                {isSubmitting ? (
                  <Clock className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                ) : (
                  <Send className="w-3.5 h-3.5 mr-1.5" />
                )}
                Submit
              </Button>
            </div>
          </div>
        </div>

        {/* Main Content: flex-1 min-h-0 is critical for overflow to work */}
        <div className="flex flex-col lg:flex-row flex-1 min-h-0 overflow-hidden">
          {/* Left Panel - TabsList fixed, TabsContent scrolls */}
          <div className="w-full lg:w-1/2 border-r border-border flex flex-col min-h-0 overflow-hidden bg-card dark:bg-[#080808]">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="flex flex-col flex-1 min-h-0">
              <TabsList className="justify-start rounded-none border-b border-border bg-card dark:bg-[#0a0a0a] px-4 h-10 shrink-0">
                <TabsTrigger value="overview" className="data-[state=active]:bg-muted dark:bg-zinc-800 data-[state=active]:text-foreground text-muted-foreground font-mono text-[11px] h-7 px-3">
                  <FileText className="w-3 h-3 mr-1.5" />
                  Overview
                </TabsTrigger>
                <TabsTrigger value="dataset" className="data-[state=active]:bg-muted dark:bg-zinc-800 data-[state=active]:text-foreground text-muted-foreground font-mono text-[11px] h-7 px-3">
                  <Database className="w-3 h-3 mr-1.5" />
                  Dataset
                </TabsTrigger>
                <TabsTrigger value="constraints" className="data-[state=active]:bg-muted dark:bg-zinc-800 data-[state=active]:text-foreground text-muted-foreground font-mono text-[11px] h-7 px-3">
                  <Shield className="w-3 h-3 mr-1.5" />
                  Constraints
                </TabsTrigger>
                <TabsTrigger value="submissions" className="data-[state=active]:bg-muted dark:bg-zinc-800 data-[state=active]:text-foreground text-muted-foreground font-mono text-[11px] h-7 px-3">
                  <TrendingUp className="w-3 h-3 mr-1.5" />
                  Results
                </TabsTrigger>
              </TabsList>

              {/* Overview Tab */}
              <TabsContent value="overview" className="flex-1 overflow-y-auto min-h-0 p-6 m-0 data-[state=inactive]:hidden">
                <div className="space-y-6">
                  {/* Full Description */}
                  {problem.description && (
                    <section>
                      <h2 className="font-mono text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">Description</h2>
                      <div className="prose prose-invert prose-sm max-w-none">
                        <pre className="whitespace-pre-wrap font-sans text-foreground/80 leading-relaxed text-sm bg-transparent p-0 m-0">
                          {problem.description}
                        </pre>
                      </div>
                    </section>
                  )}
                  {problem.short_description && !problem.description && (
                    <section>
                      <h2 className="font-mono text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">Context</h2>
                      <p className="text-foreground/80 leading-relaxed text-sm">
                        {problem.short_description}
                      </p>
                    </section>
                  )}
                  {!problem.description && !problem.short_description && (
                    <section>
                      <h2 className="font-mono text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">Context</h2>
                      <p className="text-foreground/80 leading-relaxed text-sm">
                        Build a machine learning model to solve this problem.
                      </p>
                    </section>
                  )}

                  {/* Task Section */}
                  <section>
                    <h2 className="font-mono text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">Task</h2>
                    <ul className="space-y-2 text-sm">
                      <li className="flex items-start gap-2">
                        <Code className="w-4 h-4 text-muted-foreground mt-0.5 shrink-0" />
                        <span className="text-foreground/80">
                          Implement <code className="bg-muted dark:bg-zinc-800 px-1.5 py-0.5 rounded text-emerald-400 text-xs font-mono">train_and_predict(X_train, y_train, X_test)</code>
                        </span>
                      </li>
                      <li className="flex items-start gap-2">
                        <Target className="w-4 h-4 text-muted-foreground mt-0.5 shrink-0" />
                        <span className="text-foreground/80">
                          Achieve {metricName} {problem.higher_is_better ? '≥' : '≤'} <code className="bg-muted dark:bg-zinc-800 px-1.5 py-0.5 rounded text-yellow-400 text-xs font-mono">{threshold}</code>
                        </span>
                      </li>
                      <li className="flex items-start gap-2">
                        <Activity className="w-4 h-4 text-muted-foreground mt-0.5 shrink-0" />
                        <span className="text-foreground/80">
                          Return predictions as numpy array or list
                        </span>
                      </li>
                    </ul>
                  </section>

                  {/* Evaluation Box */}
                  <section className="border border-border bg-card dark:bg-zinc-900/50 p-4">
                    <h2 className="font-mono text-xs font-bold text-muted-foreground uppercase tracking-wider mb-4">Evaluation Criteria</h2>
                    <div className="grid grid-cols-3 gap-4">
                      <div className="text-center p-3 bg-foreground/5 dark:bg-black/30 border border-border">
                        <div className="text-[10px] text-muted-foreground uppercase tracking-wider font-mono mb-1">Metric</div>
                        <div className="text-xl font-mono font-bold text-foreground uppercase">{metricName}</div>
                      </div>
                      <div className="text-center p-3 bg-foreground/5 dark:bg-black/30 border border-border">
                        <div className="text-[10px] text-muted-foreground uppercase tracking-wider font-mono mb-1">Threshold</div>
                        <div className="text-xl font-mono font-bold text-emerald-400">
                          {problem.higher_is_better ? '≥' : '≤'} {threshold || 'N/A'}
                        </div>
                      </div>
                      <div className="text-center p-3 bg-foreground/5 dark:bg-black/30 border border-border">
                        <div className="text-[10px] text-muted-foreground uppercase tracking-wider font-mono mb-1">Direction</div>
                        <div className="text-xl font-mono font-bold text-foreground">
                          {problem.higher_is_better ? '↑ Higher' : '↓ Lower'}
                        </div>
                      </div>
                    </div>
                  </section>

                  {/* Metric Selector */}
                  {problem.allowed_metrics && problem.allowed_metrics.length > 1 && (
                    <section className="border border-border bg-card dark:bg-zinc-900/50 p-4">
                      <label className="text-[10px] font-mono font-bold text-muted-foreground mb-2 block uppercase tracking-wider">
                        Select Metric
                      </label>
                      <Select value={selectedMetric} onValueChange={setSelectedMetric}>
                        <SelectTrigger className="w-full bg-card dark:bg-black border-border text-foreground font-mono text-xs h-9">
                          <SelectValue placeholder={`Default: ${problem.default_metric}`} />
                        </SelectTrigger>
                        <SelectContent className="bg-card dark:bg-zinc-900 border-border">
                          <SelectItem value="default" className="font-mono text-xs">
                            Default ({problem.default_metric})
                          </SelectItem>
                          {problem.allowed_metrics.map((metric) => (
                            <SelectItem key={metric} value={metric} className="font-mono text-xs">
                              {metric.charAt(0).toUpperCase() + metric.slice(1)}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </section>
                  )}
                </div>
              </TabsContent>

              {/* Dataset Tab */}
              <TabsContent value="dataset" className="flex-1 overflow-y-auto min-h-0 p-6 m-0 data-[state=inactive]:hidden">
                <div className="space-y-4">
                  <h2 className="font-mono text-xs font-bold text-muted-foreground uppercase tracking-wider">Dataset Information</h2>
                  
                  {problem.dataset_metadata && Object.keys(problem.dataset_metadata).length > 0 ? (
                    <div className="space-y-3">
                      {Object.entries(problem.dataset_metadata).map(([key, value]) => (
                        <div key={key} className="border border-border bg-card dark:bg-zinc-900/50 p-3">
                          <div className="text-[10px] text-muted-foreground uppercase tracking-wider font-mono mb-1">
                            {key.replace(/_/g, ' ')}
                          </div>
                          <div className="text-sm font-mono text-foreground">
                            {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="border border-border bg-card dark:bg-zinc-900/50 p-8 text-center">
                      <Database className="w-8 h-8 text-muted-foreground/70 mx-auto mb-3" />
                      <p className="text-muted-foreground font-mono text-sm">Dataset split: 80% train, 20% test</p>
                      <p className="text-muted-foreground/70 font-mono text-xs mt-2">Deterministic random_state=42 split</p>
                    </div>
                  )}
                </div>
              </TabsContent>

              {/* Constraints Tab */}
              <TabsContent value="constraints" className="flex-1 overflow-y-auto min-h-0 p-6 m-0 data-[state=inactive]:hidden">
                <div className="space-y-4">
                  <h2 className="font-mono text-xs font-bold text-muted-foreground uppercase tracking-wider">Sandbox Constraints</h2>
                  
                  <div className="space-y-2">
                    <div className="flex items-center gap-3 p-3 border border-border bg-card dark:bg-zinc-900/50">
                      <Shield className="w-4 h-4 text-emerald-500" />
                      <span className="font-mono text-sm text-foreground/80">Allowed: numpy, pandas, sklearn</span>
                    </div>
                    <div className="flex items-center gap-3 p-3 border border-border bg-card dark:bg-zinc-900/50">
                      <XCircle className="w-4 h-4 text-red-500" />
                      <span className="font-mono text-sm text-foreground/80">Forbidden: os, sys, subprocess, network</span>
                    </div>
                    <div className="flex items-center gap-3 p-3 border border-border bg-card dark:bg-zinc-900/50">
                      <Code className="w-4 h-4 text-yellow-500" />
                      <span className="font-mono text-sm text-foreground/80">Imports must be inside function body</span>
                    </div>
                    <div className="flex items-center gap-3 p-3 border border-border bg-card dark:bg-zinc-900/50">
                      <Clock className="w-4 h-4 text-blue-500" />
                      <span className="font-mono text-sm text-foreground/80">Timeout: 5 seconds max execution</span>
                    </div>
                  </div>

                  {problem.constraints && Object.keys(problem.constraints).length > 0 && (
                    <div className="mt-6">
                      <h3 className="font-mono text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">Additional Limits</h3>
                      <div className="space-y-2">
                        {Object.entries(problem.constraints).map(([key, value]) => (
                          <div key={key} className="flex items-center gap-3 p-3 border border-border bg-card dark:bg-zinc-900/50">
                            {key.includes('latency') ? <Zap className="w-4 h-4 text-yellow-500" /> : <HardDrive className="w-4 h-4 text-primary" />}
                            <span className="font-mono text-sm text-foreground/80">
                              {key.replace(/_/g, ' ')}: {value}{key.includes('latency') ? 'ms' : key.includes('memory') ? ' bytes' : ''}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </TabsContent>

              {/* Submissions Tab */}
              <TabsContent value="submissions" className="flex-1 overflow-y-auto min-h-0 p-6 m-0 data-[state=inactive]:hidden">
                <div className="space-y-6">
                  {/* Latest Evaluation Result */}
                  <EvaluationPanel results={results} problem={problem} />

                  {/* Submission History */}
                  <div>
                    <h3 className="font-mono text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">Submission History</h3>
                    {submissions.length > 0 ? (
                      <div className="space-y-2">
                        {submissions.map((sub) => (
                          <button
                            key={sub.id}
                            onClick={() => fetchSubmissionDetails(sub.id)}
                            className={`w-full text-left p-3 border transition-all hover:border-zinc-600 ${
                              sub.status === 'ACCEPTED'
                                ? 'border-emerald-500/30 bg-emerald-500/5'
                                : sub.status === 'REJECTED'
                                ? 'border-orange-500/30 bg-orange-500/5'
                                : 'border-red-500/30 bg-red-500/5'
                            }`}
                          >
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center gap-2">
                                {sub.status === 'ACCEPTED' ? (
                                  <CheckCircle className="w-4 h-4 text-emerald-400" />
                                ) : (
                                  <XCircle className="w-4 h-4 text-orange-400" />
                                )}
                                <span className={`text-xs font-mono font-bold ${
                                  sub.status === 'ACCEPTED' ? 'text-emerald-400' : 'text-orange-400'
                                }`}>
                                  {sub.status}
                                </span>
                              </div>
                              <span className="text-[10px] text-muted-foreground font-mono">
                                {new Date(sub.created_at).toLocaleString()}
                              </span>
                            </div>
                            <div className="grid grid-cols-3 gap-3 text-xs font-mono">
                              <div>
                                <div className="text-muted-foreground/70 mb-0.5">Score</div>
                                <div className="text-foreground font-bold">{sub.score?.toFixed(4) || 'N/A'}</div>
                              </div>
                              {sub.latency_ms && (
                                <div>
                                  <div className="text-muted-foreground/70 mb-0.5">Latency</div>
                                  <div className="text-foreground font-bold">{sub.latency_ms.toFixed(0)}ms</div>
                                </div>
                              )}
                              {sub.rank && (
                                <div>
                                  <div className="text-muted-foreground/70 mb-0.5">Rank</div>
                                  <div className="text-foreground font-bold">#{sub.rank}</div>
                                </div>
                              )}
                            </div>
                          </button>
                        ))}
                      </div>
                    ) : (
                      <div className="border border-border bg-card dark:bg-zinc-900/50 p-8 text-center">
                        <AlertCircle className="w-8 h-8 text-muted-foreground/70 mx-auto mb-3" />
                        <p className="text-muted-foreground font-mono text-sm">No submissions yet</p>
                      </div>
                    )}
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </div>

          {/* Right Panel - independent scroll */}
          <div className="w-full lg:w-1/2 overflow-y-auto min-h-0 flex flex-col bg-[#1e1e1e]">
            {/* Editor Header */}
            <div className="px-4 py-2 border-b border-border flex items-center justify-between shrink-0 bg-[#252526]">
              <span className="text-xs text-muted-foreground font-mono">solution.py</span>
              <span className="text-[10px] text-muted-foreground font-mono">Competitive ML Environment</span>
            </div>

            {/* Editor Area - h-full min-h-0 for proper scroll */}
            <div className="flex-1 min-h-0 relative h-full">
              {code.trim() === '' && (
                <div className="absolute inset-0 flex items-center justify-center bg-[#1e1e1e]/98 z-10 pointer-events-none">
                  <div className="text-center max-w-lg px-8">
                    <Code className="w-10 h-10 text-muted-foreground/70 mx-auto mb-4" />
                    <p className="text-muted-foreground mb-4 text-sm font-mono">Implement the function signature below</p>
                    <div className="bg-[#252526] rounded p-4 text-left border border-border mb-4">
                      <pre className="text-xs text-muted-foreground font-mono whitespace-pre-wrap">
{`def train_and_predict(X_train, y_train, X_test):
    pass`}
                      </pre>
                    </div>
                    <p className="text-[10px] text-muted-foreground/70 font-mono">
                      Allowed imports: numpy, pandas, sklearn (inside function)
                    </p>
                  </div>
                </div>
              )}
              <Editor
                height="100%"
                defaultLanguage="python"
                theme="vs-dark"
                value={code}
                onChange={(value) => setCode(value || '')}
                options={{
                  fontSize: 13,
                  fontFamily: 'JetBrains Mono, Menlo, Monaco, Consolas, monospace',
                  minimap: { enabled: false },
                  scrollBeyondLastLine: false,
                  padding: { top: 16 },
                  automaticLayout: true,
                  tabSize: 4,
                  insertSpaces: true,
                  lineNumbers: 'on',
                  lineDecorationsWidth: 10,
                  renderLineHighlight: 'line',
                }}
                loading={
                  <div className="flex items-center justify-center h-full bg-[#1e1e1e] text-muted-foreground font-mono">
                    Loading editor...
                  </div>
                }
              />
            </div>
          </div>
        </div>

        {/* Submission Details Modal */}
        {selectedSubmission && (
          <div className="fixed inset-0 bg-black/50 dark:bg-black/90 flex items-center justify-center z-50 p-4" onClick={() => setSelectedSubmission(null)}>
            <div className="bg-card dark:bg-[#0f0f0f] border border-border rounded max-w-4xl max-h-[90vh] overflow-auto w-full" onClick={(e) => e.stopPropagation()}>
              <div className="sticky top-0 bg-card dark:bg-[#0a0a0a] border-b border-border px-6 py-4 flex items-center justify-between">
                <div>
                  <h2 className="font-mono text-lg font-bold text-foreground">Submission #{selectedSubmission.id}</h2>
                  <p className="text-xs text-muted-foreground mt-1 font-mono">
                    {new Date(selectedSubmission.created_at).toLocaleString()}
                  </p>
                </div>
                <button
                  onClick={() => setSelectedSubmission(null)}
                  className="text-muted-foreground hover:text-foreground font-mono text-xl w-8 h-8 flex items-center justify-center hover:bg-muted dark:bg-zinc-800 rounded"
                >
                  ×
                </button>
              </div>
              <div className="p-6 space-y-6">
                {/* Status and Metrics */}
                <div className={`border-2 p-4 ${
                  selectedSubmission.status === 'ACCEPTED'
                    ? 'border-emerald-500/50 bg-emerald-500/5'
                    : selectedSubmission.status === 'REJECTED'
                    ? 'border-orange-500/50 bg-orange-500/5'
                    : 'border-red-500/50 bg-red-500/5'
                }`}>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm font-mono">
                    <div>
                      <div className="text-muted-foreground mb-1 text-xs">Status</div>
                      <div className={`font-bold ${
                        selectedSubmission.status === 'ACCEPTED' ? 'text-emerald-400' : 'text-orange-400'
                      }`}>
                        {selectedSubmission.status}
                      </div>
                    </div>
                    <div>
                      <div className="text-muted-foreground mb-1 text-xs">Score</div>
                      <div className="text-foreground font-bold">{selectedSubmission.score?.toFixed(4) || 'N/A'}</div>
                    </div>
                    {selectedSubmission.latency_ms && (
                      <div>
                        <div className="text-muted-foreground mb-1 text-xs">Latency</div>
                        <div className="text-foreground font-bold">{selectedSubmission.latency_ms.toFixed(0)}ms</div>
                      </div>
                    )}
                    {selectedSubmission.rank && (
                      <div>
                        <div className="text-muted-foreground mb-1 text-xs">Rank</div>
                        <div className="text-foreground font-bold">#{selectedSubmission.rank}</div>
                      </div>
                    )}
                  </div>
                  {selectedSubmission.reason && (
                    <div className="mt-3 pt-3 border-t border-border/30">
                      <p className="text-xs text-muted-foreground font-mono">{selectedSubmission.reason}</p>
                    </div>
                  )}
                </div>

                {/* Submitted Code */}
                <div>
                  <h3 className="font-mono text-xs font-bold text-muted-foreground mb-3 uppercase tracking-wider">Submitted Code</h3>
                  <pre className="bg-[#1e1e1e] rounded p-4 overflow-x-auto max-h-96 overflow-y-auto border border-border">
                    <code className="text-foreground/80 text-sm font-mono">{selectedSubmission.code}</code>
                  </pre>
                </div>

                {/* Error Log (if any) */}
                {selectedSubmission.error_log && (
                  <div>
                    <h3 className="font-mono text-xs font-bold text-red-400 mb-3 uppercase tracking-wider">Error Log</h3>
                    <pre className="bg-red-500/5 rounded p-4 overflow-x-auto max-h-48 overflow-y-auto border border-red-500/30">
                      <code className="text-red-400 text-sm font-mono">{selectedSubmission.error_log}</code>
                    </pre>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
