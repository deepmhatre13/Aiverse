import api from './axios';

/**
 * Unwrap the {success, data, error} envelope returned by the backend.
 * Falls back to raw response for non-enveloped endpoints.
 */
function unwrap(body) {
  if (body && typeof body === 'object' && 'success' in body && 'data' in body) {
    return body.data;
  }
  return body;
}

export const playgroundAPI = {
  getOptions: async () => {
    const response = await api.get('/api/playground/options/');
    return unwrap(response.data);
  },

  createJob: async (data) => {
    const response = await api.post('/api/playground/jobs/', data);
    return unwrap(response.data);
  },

  listJobs: async (page = 1, pageSize = 20) => {
    const response = await api.get('/api/playground/jobs/', {
      params: { page, page_size: pageSize },
    });
    const body = response.data;
    const inner = body?.results ?? body;
    return Array.isArray(inner) ? inner : unwrap(body);
  },

  getJob: async (jobId) => {
    const response = await api.get(`/api/playground/jobs/${jobId}/`);
    return unwrap(response.data);
  },

  getJobStatus: async (jobId) => {
    const response = await api.get(`/api/playground/jobs/${jobId}/status/`);
    return unwrap(response.data);
  },

  getMetrics: async (jobId, page = 1, pageSize = 100) => {
    const response = await api.get(`/api/playground/jobs/${jobId}/metrics/`, {
      params: { page, page_size: pageSize },
    });
    const body = response.data;
    const inner = unwrap(body);
    return inner?.results ?? (Array.isArray(inner) ? inner : []);
  },
};
