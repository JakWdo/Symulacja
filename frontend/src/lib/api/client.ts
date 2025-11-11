import axios from 'axios';

const baseUrl = import.meta.env.VITE_API_BASE_URL
  ? `${import.meta.env.VITE_API_BASE_URL.replace(/\/$/, '')}/api/v1`
  : '/api/v1';

export const api = axios.create({
  baseURL: baseUrl,
});

// Add auth interceptor - attach JWT token to all requests
// Add Accept-Language header for i18n support
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  // Add Accept-Language header based on user's language preference
  const language = localStorage.getItem('i18nextLng') || 'pl';
  // Normalize language code (remove region, e.g., 'pl-PL' -> 'pl')
  const normalizedLang = language.split('-')[0];
  config.headers['Accept-Language'] = normalizedLang;

  return config;
});

// Handle 401 errors globally - redirect to login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);
