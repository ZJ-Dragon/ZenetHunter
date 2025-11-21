import React, { useState } from 'react';
import { attackService, AttackType } from '../../lib/services/attack';
import { AttackStatus, Device } from '../../types/device';
import { Shield, ShieldOff, AlertTriangle } from 'lucide-react';
import { clsx } from 'clsx';
import toast from 'react-hot-toast';

interface AttackControlProps {
  device: Device;
  className?: string;
}

export const AttackControl: React.FC<AttackControlProps> = ({ device, className }) => {
  const [isLoading, setIsLoading] = useState(false);
  const isUnderAttack = device.attack_status === AttackStatus.RUNNING;

  const toggleAttack = async () => {
    setIsLoading(true);
    const toastId = toast.loading(isUnderAttack ? 'Stopping interference...' : 'Initiating interference...');

    try {
      if (isUnderAttack) {
        await attackService.stopAttack(device.mac);
        toast.success('Interference stopped', { id: toastId });
      } else {
        // Default to KICK attack for 60 seconds
        await attackService.startAttack(device.mac, AttackType.KICK, 60);
        toast.success('Interference started', { id: toastId });
      }
    } catch (error: unknown) {
      console.error(error);
      toast.error(isUnderAttack ? 'Failed to stop' : 'Failed to start', { id: toastId });
    } finally {
      setIsLoading(false);
    }
  };

  // If device is us (Router or Gateway), disable attack for safety
  // This logic ideally comes from backend "is_safe" flag, but frontend check helps UX
  const isSafeDevice = device.type === 'router'; 

  if (isSafeDevice) return null;

  return (
    <button
      onClick={toggleAttack}
      disabled={isLoading}
      className={clsx(
        "inline-flex items-center px-3 py-1.5 border text-xs font-medium rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors",
        isUnderAttack
          ? "border-transparent text-white bg-red-600 hover:bg-red-700 focus:ring-red-500"
          : "border-gray-300 text-gray-700 bg-white hover:bg-gray-50 focus:ring-brand-500",
        isLoading && "opacity-50 cursor-not-allowed",
        className
      )}
    >
      {isLoading ? (
        <span className="h-4 w-4 border-2 border-current border-t-transparent rounded-full animate-spin mr-1.5" />
      ) : isUnderAttack ? (
        <ShieldOff className="mr-1.5 h-3 w-3" />
      ) : (
        <AlertTriangle className="mr-1.5 h-3 w-3 text-orange-500" />
      )}
      {isLoading ? 'Processing...' : isUnderAttack ? 'Stop Attack' : 'Interfere'}
    </button>
  );
};

