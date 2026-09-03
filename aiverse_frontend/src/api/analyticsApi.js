import api from './axios';

export const getAnalyticsDashboard = () => api.get('/api/analytics/dashboard/');
