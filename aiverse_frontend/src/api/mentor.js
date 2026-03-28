/**
 * Mentor API Service
 *
 * Centralized service for all mentor-related API calls.
 * Uses authenticated axios instance ONLY.
 */

import api from './axios';

export const mentorAPI = {
  /* -----------------------------
   * Session management
   * ----------------------------- */

  createSession: async () => {
    const res = await api.post('api/mentor/session/start/');
    return res;
  },

  listSessions: async () => {
    const res = await api.get('api/mentor/sessions/');
    return res;
  },

  /* -----------------------------
   * Asking questions
   * ----------------------------- */

  askQuestion: async (sessionId, question) => {
    console.debug('[MentorAPI] askQuestion', {
      sessionId,
      hasToken: Boolean(localStorage.getItem('access') || localStorage.getItem('access_token')),
    });
    const res = await api.post(
      `api/mentor/session/${sessionId}/ask/`,
      { question }
    );
    console.debug('[MentorAPI] askQuestion response', res.data);
    return res;
  },

  /* -----------------------------
   * Task polling
   * ----------------------------- */

  checkTaskStatus: async (taskId) => {
    try {
      console.debug('[MentorAPI] checkTaskStatus', {
        taskId,
        hasToken: Boolean(localStorage.getItem('access') || localStorage.getItem('access_token')),
      });
      const res = await api.get(
        `api/mentor/task/${taskId}/status/`
      );
      console.debug('[MentorAPI] checkTaskStatus response', res.data);
      return res;
    } catch (err) {
      console.error('[MentorAPI] Task status failed', err);
      throw err;
    }
  },

  /* -----------------------------
   * Messages
   * ----------------------------- */

  getMessages: async (sessionId) => {
    const res = await api.get(
      `api/mentor/session/${sessionId}/messages/`
    );
    return res;
  },
};
