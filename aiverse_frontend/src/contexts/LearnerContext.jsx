import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useAuth } from './AuthContext';
import { getLearnerProfile, getConceptMastery } from '../api/learnerApi';
import { getPersonalisedRecommendations } from '../api/recommendationsApi';
import api from '../api/axios';

const LearnerContext = createContext(null);

export function LearnerProvider({ children }) {
  const { user, isAuthenticated } = useAuth();
  const [profile, setProfile] = useState(null);
  const [masteries, setMasteries] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [modelVersion, setModelVersion] = useState(null);
  const [isPersonalised, setIsPersonalised] = useState(false);
  const [learnerAbility, setLearnerAbility] = useState(0);
  const [loading, setLoading] = useState(false);
  const [masteryHistoryCache, setMasteryHistoryCache] = useState({});

  const fetchProfile = useCallback(async () => {
    if (!isAuthenticated) {
      setProfile(null);
      setMasteries([]);
      setRecommendations([]);
      setModelVersion(null);
      setIsPersonalised(false);
      setLearnerAbility(0);
      setMasteryHistoryCache({});
      return;
    }

    setLoading(true);
    try {
      const [profileRes, masteryRes, recRes, abilityRes] = await Promise.all([
        getLearnerProfile(),
        getConceptMastery(),
        getPersonalisedRecommendations(),
        api.get('/api/recommendations/irt-ability/').catch(() => null),
      ]);
      setProfile(profileRes.data);
      setMasteries(Array.isArray(masteryRes.data) ? masteryRes.data : []);
      const recData = recRes.data || {};
      setRecommendations(recData.recommendations || []);
      setModelVersion(recData.model_version || null);
      setIsPersonalised(recData.is_personalised ?? false);
      if (abilityRes?.data?.estimated_ability !== undefined) {
        setLearnerAbility(abilityRes.data.estimated_ability);
      } else {
        setLearnerAbility(recData.learner_ability ?? profileRes.data?.learner_ability ?? 0);
      }
    } catch (e) {
      console.error('Failed to fetch learner data', e);
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile, user?.id]);

  const getMasteryForConcept = (conceptTag) => {
    if (!conceptTag) return 0;
    const m = masteries.find((item) => item.concept_tag === conceptTag);
    return m ? m.mastery_score : 0;
  };

  const isWeakConcept = (conceptTag) =>
    profile?.weak_concepts?.includes(conceptTag) ?? false;

  const getMasteryHistory = useCallback(async (conceptTag) => {
    if (masteryHistoryCache[conceptTag]) {
      return masteryHistoryCache[conceptTag];
    }
    try {
      const res = await api.get(`/api/learner/mastery-history/?concept=${conceptTag}`);
      setMasteryHistoryCache((prev) => ({ ...prev, [conceptTag]: res.data }));
      return res.data;
    } catch {
      return { trace: [], current_mastery: 0 };
    }
  }, [masteryHistoryCache]);

  const triggerDKTUpdate = useCallback(async () => {
    try {
      await api.post('/api/recommendations/dkt-mastery/');
      await fetchProfile();
    } catch (e) {
      console.error('DKT update failed', e);
    }
  }, [fetchProfile]);

  return (
    <LearnerContext.Provider
      value={{
        profile,
        masteries,
        recommendations,
        modelVersion,
        isPersonalised,
        learnerAbility,
        loading,
        refetch: fetchProfile,
        getMasteryForConcept,
        isWeakConcept,
        getMasteryHistory,
        triggerDKTUpdate,
      }}
    >
      {children}
    </LearnerContext.Provider>
  );
}

export function useLearner() {
  const ctx = useContext(LearnerContext);
  if (!ctx) throw new Error('useLearner must be used within LearnerProvider');
  return ctx;
}
