import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import toast from 'react-hot-toast';
import { useTranslation } from 'react-i18next';

export const RequireAuth: React.FC<{ children: JSX.Element }> = ({ children }) => {
  const { isAuthenticated, isLoading, isLimitedAdmin } = useAuth();
  const location = useLocation();
  const { t } = useTranslation();

  if (isLoading) {
    // Simple loading spinner
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-brand-600"></div>
      </div>
    );
  }

  if (isLimitedAdmin && location.pathname !== '/settings') {
    toast.error(t('auth.accessDenied'));
    return <Navigate to="/settings" replace />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
};
