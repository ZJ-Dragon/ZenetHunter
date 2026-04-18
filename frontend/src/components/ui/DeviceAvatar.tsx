import React from 'react';
import { clsx } from 'clsx';
import {
  Laptop,
  Router,
  Shield,
  Smartphone,
  Wifi,
} from 'lucide-react';
import { DeviceStatus, DeviceType } from '../../types/device';

const typeMeta: Record<
  DeviceType,
  { icon: React.ElementType; color: string; background: string }
> = {
  [DeviceType.ROUTER]: {
    icon: Router,
    color: '#7c4dff',
    background: 'rgba(124, 77, 255, 0.14)',
  },
  [DeviceType.PC]: {
    icon: Laptop,
    color: '#0a64d8',
    background: 'rgba(10, 100, 216, 0.14)',
  },
  [DeviceType.MOBILE]: {
    icon: Smartphone,
    color: '#0f7b0f',
    background: 'rgba(15, 123, 15, 0.14)',
  },
  [DeviceType.IOT]: {
    icon: Wifi,
    color: '#b46900',
    background: 'rgba(180, 105, 0, 0.16)',
  },
  [DeviceType.UNKNOWN]: {
    icon: Shield,
    color: 'var(--text-tertiary)',
    background: 'var(--surface-inset)',
  },
};

interface DeviceAvatarProps {
  active?: boolean;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  status?: DeviceStatus;
  type: DeviceType;
}

const sizeMap = {
  sm: 'h-10 w-10 rounded-[1rem]',
  md: 'h-12 w-12 rounded-[1.1rem]',
  lg: 'h-14 w-14 rounded-[1.25rem]',
};

export const DeviceAvatar: React.FC<DeviceAvatarProps> = ({
  active = false,
  className,
  size = 'md',
  status,
  type,
}) => {
  const meta = typeMeta[type] || typeMeta[DeviceType.UNKNOWN];
  const Icon = meta.icon;
  const isBlocked = status === DeviceStatus.BLOCKED;

  return (
    <div
      className={clsx(
        'inline-flex items-center justify-center border',
        sizeMap[size],
        active && 'animate-pulse',
        className
      )}
      style={{
        background: isBlocked ? 'rgba(196, 43, 28, 0.14)' : meta.background,
        borderColor: 'var(--border)',
        color: isBlocked ? 'var(--danger)' : meta.color,
      }}
    >
      <Icon className={size === 'sm' ? 'h-4 w-4' : size === 'lg' ? 'h-6 w-6' : 'h-5 w-5'} />
    </div>
  );
};
