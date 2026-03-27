import { useMemo, useState, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '../api/axios';
import { useAuth } from '../contexts/AuthContext';

const POLLING_INTERVAL = 10000;

export function useLivePerformance() {
  const { user, isAuthenticated } = useAuth();
  const [lastUpdate, setLastUpdate] = useState(null);
  const [liveEvents, setLiveEvents] = useState([]);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['performance', user?.id],
    queryFn: async () => {
      const response = await api.get('/api/performance/');
      setLastUpdate(new Date());
      return response.data;
    },
    enabled: isAuthenticated,
    refetchInterval: POLLING_INTERVAL,
    refetchOnWindowFocus: true,
    staleTime: 3000,
    retry: 1,
  });

  const summary = useMemo(() => {
    if (!data) return null;
    return {
      rank: data.global_rank ?? null,
      total_score: data.total_score ?? 0,
      problems_solved: data.problems_solved ?? 0,
      total_submissions: data.submissions ?? 0,
      success_rate: data.success_rate ?? 0,
      current_streak: data.current_streak ?? 0,
    };
  }, [data]);

  const activityFeed = useMemo(() => {
    if (!data?.recent_submissions) return [];
    return data.recent_submissions.map((sub) => ({
      id: sub.id,
      problem_title: sub.problem_name,
      problem_slug: sub.problem_slug,
      submitted_at: sub.created_at,
      status: (sub.status || 'FAILED').toLowerCase() === 'accepted' ? 'accepted' : 'failed',
      score: sub.score,
      language: 'python',
    }));
  }, [data]);

  const analytics = useMemo(() => {
    if (!data) return null;
    return {
      score_progression: data.score_progression || [],
      difficulty_breakdown: data.difficulty_breakdown || [],
      language_distribution: data.language_distribution || [],
      activity_heatmap: data.activity_heatmap || [],
    };
  }, [data]);

  const refreshData = useCallback(async () => {
    await refetch();
    setLastUpdate(new Date());
  }, [refetch]);

  const clearLiveEvents = useCallback(() => {
    setLiveEvents([]);
  }, []);

  return {
    summary,
    activityFeed,
    analytics,
    liveEvents,
    isLoading,
    error: error?.response?.data?.detail || error?.message || null,
    connectionStatus: 'polling',
    lastUpdate,
    wsUnavailable: false,
    refreshData,
    clearLiveEvents,
    reconnect: refreshData,
    disconnect: () => {},
  };
}

export function formatTimeAgo(date) {
  if (!date) return '';

  const now = new Date();
  const diff = now - new Date(date);
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (seconds < 60) return 'just now';
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 7) return `${days}d ago`;

  return new Date(date).toLocaleDateString();
}

export function getStatusColor(status) {
  const colors = {
    accepted: 'text-green-500 bg-green-500/10',
    failed: 'text-red-500 bg-red-500/10',
    wrong_answer: 'text-red-500 bg-red-500/10',
    runtime_error: 'text-red-500 bg-red-500/10',
    time_limit_exceeded: 'text-red-500 bg-red-500/10',
    compilation_error: 'text-red-500 bg-red-500/10',
  };
  return colors[status?.toLowerCase()] || 'text-muted-foreground bg-muted';
}

export function getDeltaIndicator(value, isPositiveGood = true) {
  if (value === 0 || value === undefined || value === null) {
    return { text: '0', color: 'text-muted-foreground' };
  }

  const isPositive = value > 0;
  const text = isPositive ? `+${value}` : `${value}`;

  let color;
  if (isPositiveGood) {
    color = isPositive ? 'text-green-500' : 'text-red-500';
  } else {
    color = isPositive ? 'text-red-500' : 'text-green-500';
  }

  return { text, color };
}

export default useLivePerformance;
