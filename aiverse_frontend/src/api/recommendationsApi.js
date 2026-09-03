import api from './axios';

export const getRecommendations = (params = {}) =>
  api.get('/api/recommendations/', { params });

export const getPersonalisedRecommendations = () =>
  api.get('/api/recommendations/personalised/');

export const getAfterProblemRecommendations = (slug) =>
  api.get(`/api/recommendations/after-problem/${slug}/`);

export const triggerDKTMastery = () => api.post('/api/recommendations/dkt-mastery/');

export const getIRTAbility = () => api.get('/api/recommendations/irt-ability/');
