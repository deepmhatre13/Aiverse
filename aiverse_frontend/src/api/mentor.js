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
    const res = await api.post(
      `api/mentor/session/${sessionId}/ask/`,
      { question }
    );
    return res;
  },

  /* -----------------------------
   * Task polling (NO AUTH REQUIRED)
   * ----------------------------- */

  checkTaskStatus: async (taskId) => {
    try {
      const res = await api.get(
        `api/mentor/task/${taskId}/status/`
      );
      return res;
    } catch (err) {
      /**
       * IMPORTANT:
       * - Polling endpoint has no auth requirement
       * - Any error should break polling loop
       * - Log and re-throw for Mentor.jsx to handle
       */
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
