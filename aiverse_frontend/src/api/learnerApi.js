import api from './axios';

export const getLearnerProfile = () => api.get('/api/learner/profile/');

export const getConceptMastery = () => api.get('/api/learner/mastery/');

export const getMasteryHistory = (concept) =>
  api.get('/api/learner/mastery-history/', { params: { concept } });
export const estimateLearnerAbility = (problemResponses) =>
  api.post('/api/learner/ability-estimate/', { problem_responses: problemResponses });
export const submitOnboarding = (answers) =>
  api.post('/api/learner/onboarding/', answers);
