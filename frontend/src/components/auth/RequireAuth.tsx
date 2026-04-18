import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import toast from 'react-hot-toast';
import { useTranslation } from 'react-i18next';
import { LoadingScreen } from '../ui/LoadingScreen';

export const RequireAuth: React.FC<{ children: JSX.Element }> = ({ children }) => {
  const { isAuthenticated, isLoading, isLimitedAdmin } = useAuth();
  const location = useLocation();
  const { t } = useTranslation();

  if (isLoading) {
    return <LoadingScreen message="Restoring session..." />;
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
