import React, { useRef, useState } from 'react';
import { Play, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { Button } from '../ui/Button';
import { useAuth } from '../../contexts/AuthContext';
import { useWebSocketEvent } from '../../contexts/WebSocketContext';
import { scanService } from '../../lib/services/scan';
import { WSEventType } from '../../types/websocket';

export const ScanButton: React.FC<{ className?: string }> = ({ className }) => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [isScanning, setIsScanning] = useState(false);
  const currentScanIdRef = useRef<string | null>(null);

  useWebSocketEvent(
    WSEventType.SCAN_COMPLETED,
    (data: {
      id: string;
      status: string;
      error?: string;
      error_type?: string;
      devices_found?: number;
    }) => {
      if (currentScanIdRef.current && data.id === currentScanIdRef.current) {
        setIsScanning(false);
        currentScanIdRef.current = null;

        if (data.status === 'failed') {
          const errorMsg = data.error || t('scan.unknownError');
          const errorType = data.error_type || '';
          toast.error(
            t('scan.failed', {
              error: `${errorMsg}${errorType ? ` (${errorType})` : ''}`,
            }),
            { duration: 6000 }
          );
        } else if (data.status === 'completed') {
          toast.success(
            t('scan.completed', { count: data.devices_found || 0 }),
            { duration: 4000 }
          );
        }
      }
    }
  );

  const handleScan = async () => {
    if (isScanning) {
      return;
    }

    if (!isAuthenticated) {
      toast.error(t('scan.loginRequired'), { duration: 3000 });
      navigate('/login');
      return;
    }

    setIsScanning(true);
    const toastId = toast.loading(t('scan.starting'));

    try {
      const result = await scanService.startScan();
      currentScanIdRef.current = result.id;
      toast.success(t('scan.started', { id: result.id.substring(0, 8) }), {
        duration: 3000,
        id: toastId,
      });
    } catch (error: unknown) {
      console.error('Scan failed:', error);
      let errorMessage = t('scan.unknownError');
      let errorCode: string | number | undefined;

      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as {
          response?: { data?: { detail?: string; error_code?: string }; status?: number };
          message?: string;
        };
        errorMessage =
          axiosError.response?.data?.detail || axiosError.message || t('scan.unknownError');
        errorCode =
          axiosError.response?.data?.error_code || axiosError.response?.status;
      } else if (error instanceof Error) {
        errorMessage = error.message;
      }

      if (
        errorCode === 401 ||
        errorMessage.toLowerCase().includes('credentials') ||
        errorMessage.toLowerCase().includes('unauthorized')
      ) {
        errorMessage = t('scan.authFailed');
        localStorage.removeItem('token');
        window.location.href = '/login';
      } else if (
        errorMessage.toLowerCase().includes('network') ||
        errorMessage.toLowerCase().includes('network error')
      ) {
        errorMessage =
          t('scan.networkError');
      } else if (error && typeof error === 'object' && 'code' in error) {
        const codeError = error as { code?: string | number; message?: string };
        if (
          codeError.code === 'ECONNREFUSED' ||
          (codeError.message &&
            String(codeError.message).includes('Failed to fetch'))
        ) {
          errorMessage = t('scan.connectionError');
        }
      }

      toast.error(t('scan.startFailed', {
        error: `${errorMessage}${errorCode ? ` (${errorCode})` : ''}`,
      }), { duration: 6000, id: toastId });
      setIsScanning(false);
      currentScanIdRef.current = null;
    }
  };

  return (
    <Button
      className={className}
      leadingIcon={
        isScanning ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />
      }
      onClick={handleScan}
    >
      {isScanning ? t('scan.scanning') : t('scan.start')}
    </Button>
  );
};
