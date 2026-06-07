import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:9000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for caching
api.interceptors.response.use(
  (response) => {
    // Cache successful GET requests
    if (response.config.method === 'get' && response.status === 200) {
      const cacheKey = `cache:${response.config.url}`;
      const cacheData = {
        data: response.data,
        timestamp: Date.now(),
      };
      localStorage.setItem(cacheKey, JSON.stringify(cacheData));
    }
    return response;
  },
  (error) => {
    // On error, try to return cached data for GET requests
    if (error.config?.method === 'get') {
      const cacheKey = `cache:${error.config.url}`;
      const cached = localStorage.getItem(cacheKey);
      if (cached) {
        const cacheData = JSON.parse(cached);
        // Return cached data if less than 5 minutes old
        if (Date.now() - cacheData.timestamp < 5 * 60 * 1000) {
          return Promise.resolve({
            ...error.response,
            data: cacheData.data,
            _cached: true,
          });
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;
