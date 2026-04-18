import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { configService } from '../../lib/services/config';
import { useAuth } from '../../contexts/AuthContext';
import { LoadingScreen } from '../ui/LoadingScreen';

interface InitialRouteGuardProps {
  children: JSX.Element;
}

/**
 * Guard that checks system configuration status on initial load.
 * If system is not configured, redirects to /setup.
 * If system is configured but user is not authenticated, allows RequireAuth to handle redirect.
 */
export const InitialRouteGuard: React.FC<InitialRouteGuardProps> = ({ children }) => {
  const { isLoading: authLoading, isLimitedAdmin } = useAuth();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    const checkInitialStatus = async () => {
      // Limited admin: always land on settings, skip OOBE checks
      if (isLimitedAdmin) {
        if (location.pathname !== '/settings') {
          navigate('/settings', { replace: true });
        } else {
          setIsChecking(false);
        }
        return;
      }

      // Skip check if already on setup or login page
      if (location.pathname === '/setup' || location.pathname === '/login') {
        setIsChecking(false);
        return;
      }

      try {
        const status = await configService.getStatus();
        if (!status.first_run_completed) {
          navigate('/setup', { replace: true });
          return;
        }
      } catch (error) {
        // If status check fails (e.g., network error), allow normal flow
        // For MVP, if status endpoint fails, assume system is configured and proceed
        console.error('Failed to check system status:', error);
      } finally {
        setIsChecking(false);
      }
    };

    // Don't wait for auth - check status immediately on mount
    checkInitialStatus();
  }, [isLimitedAdmin, location.pathname, navigate]);

  // Show loading while checking initial status
  if (isChecking || authLoading) {
    return <LoadingScreen message={t('loading.checkingSystemStatus')} />;
  }

  return children;
};
