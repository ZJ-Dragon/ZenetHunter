import React, { useCallback, useEffect, useState } from 'react';
import {
  Activity,
  ArrowRight,
  LayoutDashboard,
  Network,
  RefreshCw,
  Shield,
  ShieldAlert,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { ScanButton } from '../components/actions/ScanButton';
import { Button } from '../components/ui/Button';
import { DeviceAvatar } from '../components/ui/DeviceAvatar';
import { DeviceStatusBadge } from '../components/ui/DeviceStatusBadge';
import { EmptyState } from '../components/ui/EmptyState';
import { PageHeader } from '../components/ui/PageHeader';
import { StatCard } from '../components/ui/StatCard';
import { Surface } from '../components/ui/Surface';
import { useWebSocketEvent } from '../contexts/WebSocketContext';
import { attackService } from '../lib/services/attack';
import { deviceService } from '../lib/services/device';
import { Device } from '../types/device';
import { WSEventType } from '../types/websocket';

const getDeviceName = (device: Device, fallback: string) =>
  device.display_name ||
  device.manual_profile?.manual_name ||
  device.name ||
  device.alias ||
  device.model ||
  device.model_guess ||
  fallback;

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [devices, setDevices] = useState<Device[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [stats, setStats] = useState({
    totalDevices: 0,
    onlineDevices: 0,
    blockedDevices: 0,
    recentAttacks: 0,
  });

  const fetchDevices = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await deviceService.getDevices();
      setDevices(data);

      const online = data.filter((device) => device.status === 'online').length;
      const blocked = data.filter((device) => device.status === 'blocked').length;

      setStats({
        totalDevices: data.length,
        onlineDevices: online,
        blockedDevices: blocked,
        recentAttacks: data.filter((device) => device.attack_status === 'running').length,
      });
    } catch (error) {
      console.error('Failed to fetch devices:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDevices();
  }, [fetchDevices]);

  useWebSocketEvent(WSEventType.DEVICE_ADDED, fetchDevices);
  useWebSocketEvent(WSEventType.DEVICE_STATUS_CHANGED, fetchDevices);
  useWebSocketEvent(WSEventType.DEVICE_RECOGNITION_UPDATED, fetchDevices);

  const recentDevices = [...devices]
    .sort(
      (left, right) =>
        new Date(right.last_seen).getTime() - new Date(left.last_seen).getTime()
    )
    .slice(0, 6);

  const attackedDevices = devices.filter(
    (device) => device.attack_status === 'running'
  );

  return (
    <div className="zh-page">
      <PageHeader
        actions={
          <>
            <ScanButton />
            <Button
              leadingIcon={
                <RefreshCw className={isLoading ? 'h-4 w-4 animate-spin' : 'h-4 w-4'} />
              }
              onClick={fetchDevices}
              variant="secondary"
            >
              {t('dashboard.refresh')}
            </Button>
          </>
        }
        eyebrow="Overview"
        icon={LayoutDashboard}
        subtitle={t('dashboard.subtitle')}
        title={t('dashboard.title')}
      />

      <div className="zh-stat-grid">
        <StatCard
          hint={stats.totalDevices > 0 ? 'Visible in current inventory' : 'Run a scan to populate'}
          icon={Network}
          label={t('dashboard.totalDevices')}
          value={stats.totalDevices}
        />
        <StatCard
          hint={stats.totalDevices > 0 ? `${stats.onlineDevices}/${stats.totalDevices} currently active` : 'Awaiting discovery'}
          icon={Activity}
          label={t('dashboard.onlineDevices')}
          tone="var(--success)"
          value={stats.onlineDevices}
        />
        <StatCard
          hint={stats.blockedDevices > 0 ? 'Review blocked hosts and policies' : 'No host is currently blocked'}
          icon={Shield}
          label={t('dashboard.blockedDevices')}
          tone="var(--danger)"
          value={stats.blockedDevices}
        />
        <StatCard
          hint={attackedDevices.length > 0 ? 'Intervention in progress' : 'System idle'}
          icon={ShieldAlert}
          label={t('dashboard.runningAttacks')}
          tone="var(--warning)"
          value={stats.recentAttacks}
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <Surface className="p-6 lg:p-7" tone="raised">
          <p className="zh-kicker">{t('dashboard.quickActions')}</p>
          <h2 className="mt-2 text-2xl font-semibold" style={{ color: 'var(--text-primary)' }}>
            Operator shortcuts
          </h2>
          <p className="mt-3 text-sm leading-7" style={{ color: 'var(--text-secondary)' }}>
            Move between inventory, topology, and response pages without losing context.
          </p>
          <div className="mt-6 grid gap-3">
            <ScanButton className="w-full" />
            <Button
              fullWidth
              leadingIcon={<Network className="h-4 w-4" />}
              onClick={() => navigate('/devices')}
              trailingIcon={<ArrowRight className="h-4 w-4" />}
              variant="secondary"
            >
              {t('dashboard.viewDevices')}
            </Button>
            <Button
              fullWidth
              leadingIcon={<Activity className="h-4 w-4" />}
              onClick={() => navigate('/topology')}
              trailingIcon={<ArrowRight className="h-4 w-4" />}
              variant="secondary"
            >
              {t('dashboard.viewTopology')}
            </Button>
            <Button
              fullWidth
              leadingIcon={<Shield className="h-4 w-4" />}
              onClick={() => navigate('/attacks')}
              trailingIcon={<ArrowRight className="h-4 w-4" />}
              variant="secondary"
            >
              {t('dashboard.viewAttacks')}
            </Button>
          </div>
        </Surface>

        <Surface className="p-6 lg:p-7" tone="raised">
          <div className="zh-toolbar zh-toolbar--spread">
            <div>
              <p className="zh-kicker">{t('dashboard.recentDevices')}</p>
              <h2 className="mt-2 text-2xl font-semibold" style={{ color: 'var(--text-primary)' }}>
                Live inventory snapshot
              </h2>
            </div>
            <Button onClick={() => navigate('/devices')} variant="ghost">
              {t('dashboard.viewDevices')}
            </Button>
          </div>
          <div className="mt-6">
            {recentDevices.length === 0 ? (
              <EmptyState
                action={<ScanButton />}
                description={t('dashboard.noDevices')}
                icon={Network}
                title="No recent devices"
              />
            ) : (
              <div className="zh-list">
                {recentDevices.map((device) => (
                  <div className="zh-list-item" key={device.mac}>
                    <DeviceAvatar status={device.status} type={device.type} />
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <p
                          className="truncate text-sm font-semibold"
                          style={{ color: 'var(--text-primary)' }}
                        >
                          {getDeviceName(device, device.mac)}
                        </p>
                        <DeviceStatusBadge status={device.status} />
                      </div>
                      <p className="mt-1 text-sm" style={{ color: 'var(--text-secondary)' }}>
                        {device.ip} • {device.display_vendor || device.vendor || device.vendor_guess || t('common.unknown')}
                      </p>
                      <p className="mt-1 text-xs" style={{ color: 'var(--text-tertiary)' }}>
                        Last seen {new Date(device.last_seen).toLocaleString()}
                      </p>
                    </div>
                    {device.attack_status === 'running' ? (
                      <Button
                        onClick={async () => {
                          try {
                            await attackService.stopAttack(device.mac);
                            fetchDevices();
                          } catch (error) {
                            console.error('Failed to stop attack:', error);
                          }
                        }}
                        size="sm"
                        variant="danger"
                      >
                        {t('dashboard.stop')}
                      </Button>
                    ) : null}
                  </div>
                ))}
              </div>
            )}
          </div>
        </Surface>
      </div>

      <Surface className="p-6 lg:p-7" tone="raised">
        <div className="zh-toolbar zh-toolbar--spread">
          <div>
            <p className="zh-kicker">Response</p>
            <h2 className="mt-2 text-2xl font-semibold" style={{ color: 'var(--text-primary)' }}>
              Active interventions
            </h2>
          </div>
          <Button onClick={() => navigate('/attacks')} variant="secondary">
            Open operations
          </Button>
        </div>
        <div className="mt-6">
          {attackedDevices.length === 0 ? (
            <EmptyState
              description={t('dashboard.noDevices')}
              icon={Shield}
              title="No running interventions"
            />
          ) : (
            <div className="zh-list">
              {attackedDevices.map((device) => (
                <div className="zh-list-item" key={device.mac}>
                  <DeviceAvatar active status={device.status} type={device.type} />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                      {getDeviceName(device, device.mac)}
                    </p>
                    <p className="mt-1 text-sm" style={{ color: 'var(--text-secondary)' }}>
                      {device.ip} • {device.attack_status}
                    </p>
                  </div>
                  <Button
                    onClick={async () => {
                      try {
                        await attackService.stopAttack(device.mac);
                        fetchDevices();
                      } catch (error) {
                        console.error('Failed to stop attack:', error);
                      }
                    }}
                    size="sm"
                    variant="danger"
                  >
                    {t('dashboard.stop')}
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>
      </Surface>
    </div>
  );
};
