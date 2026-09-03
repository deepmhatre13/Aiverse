import api from './axios';

export const Events = {
  LESSON_OPENED: 'LESSON_OPENED',
  LESSON_COMPLETED: 'LESSON_COMPLETED',
  VIDEO_STARTED: 'VIDEO_STARTED',
  VIDEO_COMPLETED: 'VIDEO_COMPLETED',
  VIDEO_SKIPPED: 'VIDEO_SKIPPED',
  QUIZ_STARTED: 'QUIZ_STARTED',
  QUIZ_SUBMITTED: 'QUIZ_SUBMITTED',
  QUIZ_PASSED: 'QUIZ_PASSED',
  QUIZ_FAILED: 'QUIZ_FAILED',
  CODE_SUBMITTED: 'CODE_SUBMITTED',
  CODE_PASSED: 'CODE_PASSED',
  CODE_FAILED: 'CODE_FAILED',
  MENTOR_QUERIED: 'MENTOR_QUERIED',
  PROBLEM_OPENED: 'PROBLEM_OPENED',
  PROBLEM_SOLVED: 'PROBLEM_SOLVED',
  PLAYGROUND_RUN: 'PLAYGROUND_RUN',
};

const getSessionId = () => {
  let sessionId = sessionStorage.getItem('aiverse_session');
  if (!sessionId) {
    sessionId = `sess_${Date.now()}_${Math.random().toString(36).slice(2, 11)}`;
    sessionStorage.setItem('aiverse_session', sessionId);
  }
  return sessionId;
};

export const trackEvent = async (eventType, contentType, contentId, metadata = {}) => {
  try {
    await api.post('/api/tracking/track/', {
      event_type: eventType,
      content_type: contentType,
      content_id: contentId,
      metadata,
      session_id: getSessionId(),
    });
  } catch (e) {
    console.warn('Tracking failed:', e.message);
  }
};

export const trackBatch = async (events) => {
  try {
    await api.post('/api/tracking/track/batch/', { events });
  } catch (e) {
    console.warn('Batch tracking failed:', e.message);
  }
};
