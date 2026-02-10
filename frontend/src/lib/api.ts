import axios from 'axios';

const rawApiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// Normalize to always include /api suffix without duplication
const normalizeApiBase = (url: string): string => {
  const trimmed = url.replace(/\/+$/, '');
  if (trimmed.endsWith('/api')) {
    return trimmed;
  }
  return `${trimmed}/api`;
};

export const api = axios.create({
  baseURL: normalizeApiBase(rawApiUrl),
  timeout: 30000, // Increased to 30s for operations like scanning
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for API calls
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for API calls
api.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    if (error.response && error.response.status === 401) {
      // Auto-logout on 401 - clear token and redirect to login
      localStorage.removeItem('token');
      // Dispatch custom event for AuthContext to handle
      window.dispatchEvent(new CustomEvent('auth:logout'));
      // If we're not already on login page, redirect
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);
