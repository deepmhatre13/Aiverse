import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Eye, Clock, CheckCircle, XCircle, Code } from 'lucide-react';
import Layout from '../components/Layout';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import LoadingSpinner from '../components/LoadingSpinner';
import EmptyState from '../components/EmptyState';
import ErrorState from '../components/ErrorState';
import api from '../api/axios';

const statusColors = {
  accepted: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  rejected: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  pending: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  failed: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  success: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  completed: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
};

export default function Submissions() {
  const [submissions, setSubmissions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchSubmissions();
  }, []);

  const fetchSubmissions = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await api.get('/api/ml/submissions/');
      // Handle both array and paginated responses
      setSubmissions(response.data.results || response.data || []);
    } catch (err) {
      // Handle 401/403 gracefully - show empty state instead of error
      if (err.response?.status === 401 || err.response?.status === 403) {
        setSubmissions([]);
        setError(null); // Don't show error for auth issues
      } else {
        const errorMessage = err.response?.data?.message || err.response?.data?.detail || 'Failed to load submissions';
        setError(errorMessage);
      }
      console.error('Error fetching submissions:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return '-';
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return '-';
    }
  };
  
  const normalizeStatus = (status) => {
    if (!status) return 'pending';
    const statusLower = status.toLowerCase();
    // Backend uses: 'pending', 'processing', 'completed', 'failed'
    if (statusLower === 'completed') return 'accepted';
    if (statusLower === 'failed') return 'rejected';
    if (statusLower === 'processing') return 'pending';
    return statusLower;
  };

  return (
    <Layout>
      <div className="container mx-auto px-4 lg:px-8 py-12">
        <div className="mb-8">
          <h1 className="heading-primary text-foreground mb-2">My Submissions</h1>
          <p className="text-muted-foreground">Track your problem-solving progress</p>
        </div>

        {isLoading ? (
          <LoadingSpinner text="Loading submissions..." />
        ) : error ? (
          <ErrorState message={error} onRetry={fetchSubmissions} />
        ) : submissions.length === 0 ? (
          <EmptyState
            icon={Code}
            title="No submissions yet"
            message="Start solving problems to see your submissions here"
            action={
              <Link to="/problems">
                <Button className="btn-wine mt-4">Browse Problems</Button>
              </Link>
            }
          />
        ) : (
          <div className="card-elevated overflow-hidden">
            <table className="w-full">
              <thead className="bg-muted/50">
                <tr>
                  <th className="text-left px-6 py-4 text-sm font-medium text-muted-foreground">Problem</th>
                  <th className="text-left px-6 py-4 text-sm font-medium text-muted-foreground">Status</th>
                  <th className="text-left px-6 py-4 text-sm font-medium text-muted-foreground">Score</th>
                  <th className="text-left px-6 py-4 text-sm font-medium text-muted-foreground">Submitted</th>
                  <th className="text-right px-6 py-4 text-sm font-medium text-muted-foreground">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {submissions.map((submission) => (
                  <tr key={submission.id} className="hover:bg-muted/30 transition-colors">
                    <td className="px-6 py-4">
                      <Link
                        to={`/problems/${submission.problem_slug || submission.problem?.slug || submission.slug}`}
                        className="font-medium text-foreground hover:text-primary transition-colors"
                      >
                        {submission.problem_title || submission.problem?.title || submission.title || 'Untitled Problem'}
                      </Link>
                    </td>
                    <td className="px-6 py-4">
                      {(() => {
                        const normalizedStatus = normalizeStatus(submission.status);
                        const statusDisplay = submission.status || normalizedStatus;
                        return (
                          <Badge className={statusColors[normalizedStatus] || statusColors.pending}>
                            <span className="flex items-center gap-1">
                              {normalizedStatus === 'accepted' ? (
                                <CheckCircle className="w-3 h-3" />
                              ) : normalizedStatus === 'rejected' ? (
                                <XCircle className="w-3 h-3" />
                              ) : (
                                <Clock className="w-3 h-3" />
                              )}
                              {statusDisplay}
                            </span>
                          </Badge>
                        );
                      })()}
                    </td>
                    <td className="px-6 py-4 font-mono text-sm">
                      {submission.public_score !== null && submission.public_score !== undefined 
                        ? (typeof submission.public_score === 'number' ? submission.public_score.toFixed(4) : submission.public_score)
                        : (submission.score !== null && submission.score !== undefined 
                          ? (typeof submission.score === 'number' ? submission.score.toFixed(4) : submission.score)
                          : '-')}
                    </td>
                    <td className="px-6 py-4 text-sm text-muted-foreground">
                      {formatDate(submission.created_at || submission.submitted_at || submission.timestamp)}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Button variant="ghost" size="sm">
                        <Eye className="w-4 h-4 mr-1" />
                        View
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Layout>
  );
}