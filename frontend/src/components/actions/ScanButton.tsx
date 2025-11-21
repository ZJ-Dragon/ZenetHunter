import React, { useState } from 'react';
import { scanService } from '../../lib/services/scan';
import { RefreshCw, Play } from 'lucide-react';
import { clsx } from 'clsx';
import toast from 'react-hot-toast';

export const ScanButton: React.FC<{ className?: string }> = ({ className }) => {
  const [isScanning, setIsScanning] = useState(false);

  const handleScan = async () => {
    if (isScanning) return;
    
    setIsScanning(true);
    const toastId = toast.loading('Starting network scan...');

    try {
      await scanService.startScan();
      toast.success('Scan initiated successfully', { id: toastId });
      // Note: We don't set isScanning to false immediately if we want to wait for WS event
      // But for UX responsiveness, we might reset it after a timeout or let WS handle it.
      // For now, we'll reset after a short delay to allow re-triggering if needed.
      setTimeout(() => setIsScanning(false), 2000);
    } catch (error: unknown) {
      console.error(error);
      toast.error('Failed to start scan', { id: toastId });
      setIsScanning(false);
    }
  };

  return (
    <button
      onClick={handleScan}
      disabled={isScanning}
      className={clsx(
        "inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-500 disabled:opacity-75 disabled:cursor-not-allowed transition-all",
        isScanning ? "bg-brand-400" : "bg-brand-600 hover:bg-brand-700",
        className
      )}
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

