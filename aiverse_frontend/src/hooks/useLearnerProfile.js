import { useLearner } from '../contexts/LearnerContext';

export function useLearnerProfile() {
  const { profile, masteries, loading, refetch, getMasteryForConcept, isWeakConcept } =
    useLearner();
  return { profile, masteries, loading, refetch, getMasteryForConcept, isWeakConcept };
}
