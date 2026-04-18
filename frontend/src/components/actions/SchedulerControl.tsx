import React, { useState } from 'react';
import { schedulerService } from '../../lib/services/scheduler';
import { Device } from '../../types/device';
import { Brain } from 'lucide-react';
import { clsx } from 'clsx';
import toast from 'react-hot-toast';
import { useTranslation } from 'react-i18next';

interface SchedulerControlProps {
  device: Device;
  className?: string;
}

export const SchedulerControl: React.FC<SchedulerControlProps> = ({ device, className }) => {
  const { t } = useTranslation();
  const [isLoading, setIsLoading] = useState(false);

  const handleExecute = async () => {
    setIsLoading(true);
    const toastId = toast.loading(t('scheduler.analyzing'));
    try {
      const result = await schedulerService.executeStrategy(device.mac);

      if (result.success) {
        toast.success(t('scheduler.applied', { count: result.strategies_applied }), {
          id: toastId,
        });
      } else {
        toast.error(t('scheduler.failedWithError', { error: result.error }), { id: toastId });
      }
    } catch (error) {
      console.error(error);
      toast.error(t('scheduler.failed'), { id: toastId });
    } finally {
      setIsLoading(false);
    }
  };

  // Allow scheduler on all devices (removed router restriction)

  return (
    <button
      onClick={handleExecute}
      disabled={isLoading}
      title={t('scheduler.runTitle')}
      className={clsx(
        "btn-winui-secondary inline-flex items-center px-3 py-1.5 text-xs font-medium rounded-lg transition-all duration-200",
        className
      )}
      style={{ minHeight: '24px' }}
    >
      {isLoading ? (
        <span className="h-4 w-4 border-2 border-current border-t-transparent rounded-full animate-spin mr-1.5" />
      ) : (
        <Brain className="mr-1.5 h-3 w-3" style={{ color: '#9a4dff' }} />
      )}
      {t('scheduler.button')}
    </button>
  );
};
