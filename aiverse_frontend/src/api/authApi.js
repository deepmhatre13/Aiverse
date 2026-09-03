import api from './axios';

export const login = (email, password) =>
  api.post('/api/users/login/', { email, password });

export const register = (payload) => api.post('/api/users/register/', payload);

export const getMe = () => api.get('/api/users/me/');

export const googleLogin = (credential) =>
  api.post('/api/auth/google/', { credential });

export const refreshToken = (refresh) =>
  api.post('/api/users/refresh/', { refresh });
