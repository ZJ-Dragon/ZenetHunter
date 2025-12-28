import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { scanService } from '../../lib/services/scan';
import { RefreshCw, Play } from 'lucide-react';
import { clsx } from 'clsx';
import toast from 'react-hot-toast';
import { useWebSocketEvent } from '../../contexts/WebSocketContext';
import { WSEventType } from '../../types/websocket';

export const ScanButton: React.FC<{ className?: string }> = ({ className }) => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [isScanning, setIsScanning] = useState(false);
  const currentScanIdRef = useRef<string | null>(null);

  // Listen for scan completion events
  useWebSocketEvent(WSEventType.SCAN_COMPLETED, (data: { id: string; status: string; error?: string; error_type?: string; devices_found?: number }) => {
    if (currentScanIdRef.current && data.id === currentScanIdRef.current) {
      setIsScanning(false);
      currentScanIdRef.current = null;

      if (data.status === 'failed') {
        const errorMsg = data.error || 'Unknown error';
        const errorType = data.error_type || '';
        toast.error(
          `Scan failed: ${errorMsg}${errorType ? ` (${errorType})` : ''}`,
          { duration: 6000 }
        );
      } else if (data.status === 'completed') {
        toast.success(
          `Scan completed. Found ${data.devices_found || 0} devices.`,
          { duration: 4000 }
        );
      }
    }
  });

  const handleScan = async () => {
    if (isScanning) return;

    // Check authentication before scanning
    if (!isAuthenticated) {
      toast.error('请先登录以使用扫描功能', { duration: 3000 });
      navigate('/login');
      return;
    }

    setIsScanning(true);
    const toastId = toast.loading('Starting network scan...');

    try {
      const result = await scanService.startScan();
      currentScanIdRef.current = result.id;
      toast.success(`Scan initiated (ID: ${result.id.substring(0, 8)}...)`, { id: toastId, duration: 3000 });
      // Keep scanning state true until WebSocket event arrives
    } catch (error: unknown) {
      console.error('Scan failed:', error);
      let errorMessage = 'Unknown error';
      let errorCode: string | number | undefined;

      // Handle axios error format
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { data?: { detail?: string; error_code?: string }; status?: number }; message?: string };
        errorMessage = axiosError.response?.data?.detail || axiosError.message || 'Unknown error';
        errorCode = axiosError.response?.data?.error_code || axiosError.response?.status;
      } else if (error instanceof Error) {
        errorMessage = error.message;
      }

      // Provide user-friendly error messages
      if (errorCode === 401 || errorMessage.toLowerCase().includes('credentials') || errorMessage.toLowerCase().includes('unauthorized')) {
        errorMessage = '认证失败：请先登录。如果已登录，请重新登录以刷新 token。';
        // Clear invalid token and redirect to login
        localStorage.removeItem('token');
        window.location.href = '/login';
      } else if (errorMessage.toLowerCase().includes('network') || errorMessage.toLowerCase().includes('network error')) {
        errorMessage = 'Network Error: Please check Docker configuration. Network scanning requires host network mode and NET_RAW/NET_ADMIN capabilities. See README for details.';
      } else if (error && typeof error === 'object' && 'code' in error) {
        const codeError = error as { code?: string | number; message?: string };
        if (codeError.code === 'ECONNREFUSED' || (codeError.message && String(codeError.message).includes('Failed to fetch'))) {
          errorMessage = 'Connection Error: Cannot reach backend server. Please check if the backend is running.';
        }
      }

      toast.error(
        `Failed to start scan: ${errorMessage}${errorCode ? ` (${errorCode})` : ''}`,
        { id: toastId, duration: 6000 }
      );
      setIsScanning(false);
      currentScanIdRef.current = null;
    }
  };

  return (
    <button
      onClick={handleScan}
      disabled={isScanning}
      className={clsx(
        "btn-winui inline-flex items-center px-4 py-2 text-sm font-medium rounded-lg text-white transition-all duration-200 disabled:opacity-75 disabled:cursor-not-allowed",
        className
      )}
      style={{
        backgroundColor: isScanning ? 'var(--winui-accent-hover)' : 'var(--winui-accent)'
      }}
      onMouseEnter={(e) => {
        if (!isScanning) e.currentTarget.style.backgroundColor = 'var(--winui-accent-hover)';
      }}
      onMouseLeave={(e) => {
        if (!isScanning) e.currentTarget.style.backgroundColor = 'var(--winui-accent)';
      }}
    >
      {isScanning ? (
        <>
          <RefreshCw className="animate-spin -ml-1 mr-2 h-4 w-4" />
          Scanning...
        </>
      ) : (
        <>
          <Play className="-ml-1 mr-2 h-4 w-4" />
          Start Scan
        </>
      )}
    </button>
  );
};
