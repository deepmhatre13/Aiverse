import axios from 'axios';

// Default to http://127.0.0.1:8000 (WITHOUT /api suffix)
// Paths must include /api prefix for routing
const BASE_API_URL =
  import.meta.env.VITE_API_BASE_URL ||
  import.meta.env.VITE_BASE_API_URL ||
  'http://127.0.0.1:8000';

const getAccessToken = () => localStorage.getItem('access');
const getRefreshToken = () => localStorage.getItem('refresh');

const setAccessToken = (token) => {
  localStorage.setItem('access', token);
};

const setRefreshToken = (token) => {
  localStorage.setItem('refresh', token);
};

const api = axios.create({
  baseURL: BASE_API_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 60000, // 60s for Mentor/ML model calls
});

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  console.log('Token:', token);
  console.debug('[API][request]', {
    method: config.method,
    url: config.url,
    hasToken: Boolean(token),
  });
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => {
    console.log('Response:', response.data);
    console.debug('[API][response]', {
      method: response.config?.method,
      url: response.config?.url,
      status: response.status,
    });
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    console.debug('[API][error]', {
      method: originalRequest?.method,
      url: originalRequest?.url,
      status: error.response?.status,
      data: error.response?.data,
    });

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const refresh = getRefreshToken();
      if (!refresh) {
        window.location.href = '/login';
        return Promise.reject(error);
      }

      try {
        const res = await axios.post(
          `${BASE_API_URL}/api/users/refresh/`,
          { refresh }
        );

        if (res.data?.refresh) {
          setRefreshToken(res.data.refresh);
        }
        setAccessToken(res.data.access);
        originalRequest.headers.Authorization = `Bearer ${res.data.access}`;
        return api(originalRequest);
      } catch {
        localStorage.removeItem('access');
        localStorage.removeItem('refresh');
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

export default api;
