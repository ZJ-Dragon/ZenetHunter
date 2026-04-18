import React from 'react';
import { useTranslation } from 'react-i18next';
import { Badge } from './Badge';
import { DeviceStatus } from '../../types/device';

interface DeviceStatusBadgeProps {
  status: DeviceStatus;
}

export const DeviceStatusBadge: React.FC<DeviceStatusBadgeProps> = ({
  status,
}) => {
  const { t } = useTranslation();
  const toneMap = {
    [DeviceStatus.ONLINE]: 'success',
    [DeviceStatus.OFFLINE]: 'neutral',
    [DeviceStatus.BLOCKED]: 'danger',
  } as const;

  const labelMap = {
    [DeviceStatus.ONLINE]: t('devices.statusOnline'),
    [DeviceStatus.OFFLINE]: t('devices.statusOffline'),
    [DeviceStatus.BLOCKED]: t('devices.statusBlocked'),
  };

  return <Badge tone={toneMap[status]}>{labelMap[status]}</Badge>;
};
