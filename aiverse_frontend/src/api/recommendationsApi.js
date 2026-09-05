import api from './axios';

export const getRecommendations = (params = {}) =>
  api.get('/api/recommendations/', { params });

export const getPersonalisedRecommendations = () =>
  api.get('/api/recommendations/personalised/');

/**
 * Phase 3: Personalized Learn experience.
 * Backed by the existing recommendation engine
 * (GET /api/learn/recommendations/ -> build_personalized_learn_response).
 */
export const getPersonalizedLearn = () =>
  api.get('/api/learn/recommendations/').then((r) => r.data);

export const getAfterProblemRecommendations = (slug) =>
  api.get(`/api/recommendations/after-problem/${slug}/`);

export const triggerDKTMastery = () => api.post('/api/recommendations/dkt-mastery/');

export const getIRTAbility = () => api.get('/api/recommendations/irt-ability/');
