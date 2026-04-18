import React from 'react';
import { Badge } from './Badge';
import { DeviceStatus } from '../../types/device';

interface DeviceStatusBadgeProps {
  status: DeviceStatus;
}

export const DeviceStatusBadge: React.FC<DeviceStatusBadgeProps> = ({
  status,
}) => {
  const toneMap = {
    [DeviceStatus.ONLINE]: 'success',
    [DeviceStatus.OFFLINE]: 'neutral',
    [DeviceStatus.BLOCKED]: 'danger',
  } as const;

  return <Badge tone={toneMap[status]}>{status}</Badge>;
};
