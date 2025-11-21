import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { configService } from '../lib/services/config';
import { useAuth } from '../contexts/AuthContext';

interface OOBEGuardProps {
  children: JSX.Element;
}

export const OOBEGuard: React.FC<OOBEGuardProps> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const checkStatus = async () => {
      try {
        // We can check status even if not authenticated, 
        // but usually OOBE happens before auth or with a temporary token.
        // For this MVP, let's assume we check it on root load.
        const status = await configService.getStatus();
        if (!status.is_configured && window.location.pathname !== '/setup') {
          navigate('/setup');
        }
      } catch (error) {
        console.error('Failed to check OOBE status', error);
      }
    };

    if (isAuthenticated) {
      checkStatus();
    }
  }, [isAuthenticated, navigate]);

  return children;
};

