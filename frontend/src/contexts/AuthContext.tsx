import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from '../lib/api';

interface AuthContextType {
  token: string | null;
  isAuthenticated: boolean;
  login: (token: string, options?: { limitedAdmin?: boolean }) => void;
  logout: () => void;
  isLoading: boolean;
  isLimitedAdmin: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isLimitedAdmin, setIsLimitedAdmin] = useState<boolean>(() => localStorage.getItem('limited_admin') === 'true');

  const logout = useCallback(() => {
    localStorage.removeItem('token');
    localStorage.removeItem('limited_admin');
    setToken(null);
    setIsLimitedAdmin(false);
    delete api.defaults.headers.common['Authorization'];
  }, []);

  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    if (storedToken) {
      setToken(storedToken);
      // Ensure API default header is set on mount
      api.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
    }
    setIsLoading(false);

    // Listen for logout events from API interceptor
    const handleLogout = () => {
      logout();
    };
    window.addEventListener('auth:logout', handleLogout);

    return () => {
      window.removeEventListener('auth:logout', handleLogout);
    };
  }, [logout]);

  const login = (newToken: string, options?: { limitedAdmin?: boolean }) => {
    localStorage.setItem('token', newToken);
    const limited = options?.limitedAdmin ?? false;
    if (limited) {
      localStorage.setItem('limited_admin', 'true');
    } else {
      localStorage.removeItem('limited_admin');
    }
    setIsLimitedAdmin(limited);
    setToken(newToken);
    // Setup default header immediately
    api.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
  };

  const value = {
    token,
    isAuthenticated: !!token,
    login,
    logout,
    isLoading,
    isLimitedAdmin,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
