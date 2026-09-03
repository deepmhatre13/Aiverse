import { useLearner } from '../contexts/LearnerContext';

export function useRecommendations() {
  const { recommendations, loading, refetch } = useLearner();
  return { recommendations, loading, refetch };
}
