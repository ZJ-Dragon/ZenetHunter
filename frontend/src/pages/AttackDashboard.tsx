import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Activity,
  Play,
  RefreshCw,
  Shield,
  ShieldAlert,
  Square,
  Terminal,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { useTranslation } from 'react-i18next';
import { Button } from '../components/ui/Button';
import { DeviceAvatar } from '../components/ui/DeviceAvatar';
import { Badge } from '../components/ui/Badge';
import { EmptyState } from '../components/ui/EmptyState';
import { PageHeader } from '../components/ui/PageHeader';
import { StatCard } from '../components/ui/StatCard';
import { Surface } from '../components/ui/Surface';
import { useWebSocketEvent } from '../contexts/WebSocketContext';
import { attackService, AttackType } from '../lib/services/attack';
import { deviceService } from '../lib/services/device';
import { AttackStatus, Device } from '../types/device';
import {
  ActiveDefenseLogEntry,
  ActiveDefenseStartedData,
  ActiveDefenseStoppedData,
  WSEventType,
} from '../types/websocket';

interface AttackTypeMeta {
  label: string;
  tone: 'accent' | 'warning' | 'danger' | 'neutral' | 'success';
}

const attackTypeMetadata: Record<AttackType, AttackTypeMeta> = {
  [AttackType.KICK]: { label: 'WiFi Deauth', tone: 'warning' },
  [AttackType.BLOCK]: { label: 'ARP Jam', tone: 'danger' },
  [AttackType.DHCP_SPOOF]: { label: 'DHCP Spoof', tone: 'accent' },
  [AttackType.DNS_SPOOF]: { label: 'DNS Spoof', tone: 'accent' },
  [AttackType.ICMP_REDIRECT]: { label: 'ICMP Redirect', tone: 'warning' },
  [AttackType.PORT_SCAN]: { label: 'Port Scan', tone: 'success' },
  [AttackType.TRAFFIC_SHAPE]: { label: 'Traffic Shape', tone: 'warning' },
  [AttackType.MAC_FLOOD]: { label: 'MAC Flood', tone: 'danger' },
  [AttackType.VLAN_HOP]: { label: 'VLAN Hop', tone: 'neutral' },
  [AttackType.BEACON_FLOOD]: { label: 'Beacon Flood', tone: 'warning' },
};

interface ActiveAttackInfo {
  device?: Device;
  duration: number;
  intensity: number;
  mac: string;
  start_time: string;
  type: string;
}

const getDeviceName = (device: Device, fallback: string) =>
  device.display_name ||
  device.manual_profile?.manual_name ||
  device.name ||
  device.alias ||
  device.model ||
  device.model_guess ||
  fallback;

const logTone = (level: string) => {
  if (level === 'success') {
    return 'success';
  }
  if (level === 'warning') {
    return 'warning';
  }
  if (level === 'error') {
    return 'danger';
  }
  return 'neutral';
};

export const AttackDashboard: React.FC = () => {
  const { t } = useTranslation();
  const [devices, setDevices] = useState<Device[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeAttacks, setActiveAttacks] = useState<Map<string, ActiveAttackInfo>>(
    new Map()
  );
  const [logs, setLogs] = useState<ActiveDefenseLogEntry[]>([]);
  const [stoppingMacs, setStoppingMacs] = useState<Set<string>>(new Set());
  const [globalIntensity, setGlobalIntensity] = useState(5);
  const [globalDuration, setGlobalDuration] = useState(60);
  const [selectedAttackType, setSelectedAttackType] = useState<AttackType>(
    AttackType.BLOCK
  );
  const [searchQuery, setSearchQuery] = useState('');
  const [launchingMacs, setLaunchingMacs] = useState<Set<string>>(new Set());

  const fetchDevices = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await deviceService.getAll();
      setDevices(data);

      setActiveAttacks((previous) => {
        const updated = new Map(previous);
        updated.forEach((attack, mac) => {
          const device = data.find(
            (candidate) => candidate.mac.toLowerCase() === mac.toLowerCase()
          );
          if (device) {
            attack.device = device;
          }
        });
        return updated;
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

  useWebSocketEvent(
    WSEventType.ACTIVE_DEFENSE_STARTED,
    (data: ActiveDefenseStartedData) => {
      const device = devices.find(
        (candidate) => candidate.mac.toLowerCase() === data.mac.toLowerCase()
      );
      setActiveAttacks((previous) => {
        const updated = new Map(previous);
        updated.set(data.mac.toLowerCase(), {
          device,
          duration: data.duration,
          intensity: data.intensity,
          mac: data.mac,
          start_time: data.start_time,
          type: data.type,
        });
        return updated;
      });
      setLaunchingMacs((previous) => {
        const updated = new Set(previous);
        updated.delete(data.mac.toLowerCase());
        return updated;
      });
      fetchDevices();
    }
  );

  useWebSocketEvent(
    WSEventType.ACTIVE_DEFENSE_STOPPED,
    (data: ActiveDefenseStoppedData) => {
      setActiveAttacks((previous) => {
        const updated = new Map(previous);
        updated.delete(data.mac.toLowerCase());
        return updated;
      });
      setStoppingMacs((previous) => {
        const updated = new Set(previous);
        updated.delete(data.mac.toLowerCase());
        return updated;
      });
      fetchDevices();
    }
  );

  useWebSocketEvent(
    WSEventType.ACTIVE_DEFENSE_LOG,
    (data: ActiveDefenseLogEntry) => {
      setLogs((previous) => {
        const isDuplicate = previous.some(
          (log) =>
            log.message === data.message &&
            log.mac === data.mac &&
            Math.abs(
              new Date(log.timestamp).getTime() -
                new Date(data.timestamp).getTime()
            ) < 2000
        );

        if (isDuplicate) {
          return previous;
        }

        return [data, ...previous].slice(0, 100);
      });
    }
  );

  useWebSocketEvent(WSEventType.ATTACK_STARTED, fetchDevices);
  useWebSocketEvent(WSEventType.ATTACK_STOPPED, fetchDevices);
  useWebSocketEvent(WSEventType.ATTACK_FINISHED, fetchDevices);
  useWebSocketEvent(WSEventType.DEVICE_UPDATED, fetchDevices);
  useWebSocketEvent(WSEventType.DEVICE_RECOGNITION_UPDATED, fetchDevices);
  useWebSocketEvent(WSEventType.DEVICE_ADDED, fetchDevices);
  useWebSocketEvent(WSEventType.DEVICE_STATUS_CHANGED, fetchDevices);

  const devicesWithAttacks = devices.filter(
    (device) => device.attack_status === AttackStatus.RUNNING
  );

  const displayAttacks = activeAttacks.size
    ? Array.from(activeAttacks.values())
    : devicesWithAttacks.map((device) => ({
        device,
        duration: 0,
        intensity: 0,
        mac: device.mac,
        start_time: '',
        type: 'unknown',
      }));

  const filteredDevices = useMemo(() => {
    if (!searchQuery) {
      return devices;
    }

    const query = searchQuery.toLowerCase();
    return devices.filter((device) => {
      const names = [
        device.display_name,
        device.name,
        device.alias,
        device.model,
        device.model_guess,
        device.manual_profile?.manual_name,
      ].filter(Boolean) as string[];
      const vendors = [
        device.display_vendor,
        device.vendor,
        device.vendor_guess,
        device.manual_profile?.manual_vendor,
      ].filter(Boolean) as string[];

      return (
        names.some((name) => name.toLowerCase().includes(query)) ||
        vendors.some((vendor) => vendor.toLowerCase().includes(query)) ||
        device.ip.toLowerCase().includes(query) ||
        device.mac.toLowerCase().includes(query)
      );
    });
  }, [devices, searchQuery]);

  const isDeviceUnderAttack = (mac: string) =>
    activeAttacks.has(mac.toLowerCase()) ||
    devices.find((device) => device.mac.toLowerCase() === mac.toLowerCase())
      ?.attack_status === AttackStatus.RUNNING;

  const handleStopAttack = async (mac: string) => {
    setStoppingMacs((previous) => new Set(previous).add(mac.toLowerCase()));
    const toastId = toast.loading(t('attack.stopping'));

    try {
      await attackService.stopAttack(mac);
      toast.success(t('attack.stopped'), { id: toastId });
      setActiveAttacks((previous) => {
        const updated = new Map(previous);
        updated.delete(mac.toLowerCase());
        return updated;
      });
      fetchDevices();
    } catch (error) {
      console.error('Failed to stop attack:', error);
      toast.error(t('attack.stopFailed'), { id: toastId });
    } finally {
      setStoppingMacs((previous) => {
        const updated = new Set(previous);
        updated.delete(mac.toLowerCase());
        return updated;
      });
    }
  };

  const handleLaunchAttack = async (device: Device) => {
    setLaunchingMacs((previous) => new Set(previous).add(device.mac.toLowerCase()));
    const metadata = attackTypeMetadata[selectedAttackType];
    const toastId = toast.loading(
      t('attack.launching', {
        target: getDeviceName(device, t('common.unknown')),
        type: metadata.label,
      })
    );

    try {
      await attackService.startAttack(
        device.mac,
        selectedAttackType,
        globalDuration,
        globalIntensity
      );
      toast.success(t('attack.started', { type: metadata.label }), { id: toastId });
    } catch (error) {
      console.error('Failed to start attack:', error);
      toast.error(t('attack.startFailed'), { id: toastId });
      setLaunchingMacs((previous) => {
        const updated = new Set(previous);
        updated.delete(device.mac.toLowerCase());
        return updated;
      });
    }
  };

  return (
    <div className="zh-page">
      <PageHeader
        actions={
          <Button
            leadingIcon={<RefreshCw className={isLoading ? 'h-4 w-4 animate-spin' : 'h-4 w-4'} />}
            onClick={fetchDevices}
            variant="secondary"
          >
            {t('attack.refresh')}
          </Button>
        }
        eyebrow="Response"
        icon={ShieldAlert}
        subtitle={t('attack.subtitle')}
        title={t('attack.title')}
      />

      <div className="zh-stat-grid">
        <StatCard
          hint="Currently active interventions"
          icon={ShieldAlert}
          label={t('attack.activeOps')}
          tone="var(--danger)"
          value={displayAttacks.length}
        />
        <StatCard
          hint="Observed devices available as targets"
          icon={Shield}
          label={t('attack.totalDevices')}
          value={devices.length}
        />
        <StatCard
          hint={logs.length > 0 ? 'Realtime events streaming in' : 'No live events yet'}
          icon={Terminal}
          label={t('attack.logs')}
          tone="var(--accent)"
          value={logs.length}
        />
        <StatCard
          hint="Backend connection and WebSocket event flow are active"
          icon={Activity}
          label={t('attack.systemStatus')}
          tone="var(--success)"
          value={t('attack.operational')}
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <div className="space-y-6">
          <Surface className="p-6 lg:p-7" tone="raised">
            <div className="zh-toolbar zh-toolbar--spread">
              <div>
                <p className="zh-kicker">{t('attack.targets')}</p>
                <h2 className="mt-2 text-2xl font-semibold" style={{ color: 'var(--text-primary)' }}>
                  Active operations
                </h2>
              </div>
            </div>
            <div className="mt-6">
              {displayAttacks.length > 0 ? (
                <div className="zh-list">
                  {displayAttacks.map((attack) => {
                    const device =
                      attack.device ||
                      devices.find(
                        (candidate) =>
                          candidate.mac.toLowerCase() === attack.mac.toLowerCase()
                      );
                    const isStopping = stoppingMacs.has(attack.mac.toLowerCase());
                    return (
                      <div className="zh-list-item" key={attack.mac}>
                        {device ? (
                          <DeviceAvatar
                            active
                            size="lg"
                            status={device.status}
                            type={device.type}
                          />
                        ) : (
                          <div />
                        )}
                        <div className="min-w-0 flex-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <p className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                              {device
                                ? getDeviceName(device, t('common.unknown'))
                                : attack.mac}
                            </p>
                            <Badge
                              tone={
                                attack.type in attackTypeMetadata
                                  ? attackTypeMetadata[attack.type as AttackType].tone
                                  : 'danger'
                              }
                            >
                              {attack.type in attackTypeMetadata
                                ? attackTypeMetadata[attack.type as AttackType].label
                                : attack.type}
                            </Badge>
                          </div>
                          <p className="mt-1 text-sm" style={{ color: 'var(--text-secondary)' }}>
                            {device?.ip || t('common.unknown')} • {attack.mac}
                          </p>
                          <div className="mt-2 flex flex-wrap gap-2">
                            {attack.duration > 0 ? (
                              <Badge tone="neutral">{attack.duration}s duration</Badge>
                            ) : null}
                            {attack.intensity > 0 ? (
                              <Badge tone="warning">
                                {t('attack.intensity', { value: attack.intensity })}
                              </Badge>
                            ) : null}
                          </div>
                        </div>
                        <Button
                          loading={isStopping}
                          onClick={() => handleStopAttack(attack.mac)}
                          size="sm"
                          variant="danger"
                        >
                          {t('attack.stop')}
                        </Button>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <EmptyState
                  description={t('attack.noActiveHint')}
                  icon={ShieldAlert}
                  title={t('attack.noActiveTitle')}
                />
              )}
            </div>
          </Surface>

          <Surface className="p-6 lg:p-7" tone="raised">
            <div className="zh-toolbar zh-toolbar--spread">
              <div>
                <p className="zh-kicker">{t('attack.logs')}</p>
                <h2 className="mt-2 text-2xl font-semibold" style={{ color: 'var(--text-primary)' }}>
                  Operation timeline
                </h2>
              </div>
              <Badge tone="neutral">{logs.length}</Badge>
            </div>
            <div className="mt-6">
              {logs.length > 0 ? (
                <div className="space-y-3">
                  {logs.map((log, index) => (
                    <Surface
                      className="p-4"
                      key={`${log.timestamp}-${index}`}
                      tone={index === 0 ? 'subtle' : 'inset'}
                    >
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge tone={logTone(log.level)}>{log.level.toUpperCase()}</Badge>
                        <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </span>
                        {log.mac ? (
                          <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
                            {log.mac}
                          </span>
                        ) : null}
                      </div>
                      <p className="mt-3 text-sm leading-6" style={{ color: 'var(--text-primary)' }}>
                        {log.message}
                      </p>
                    </Surface>
                  ))}
                </div>
              ) : (
                <EmptyState
                  description={t('attack.logsEmpty')}
                  icon={Terminal}
                  title="No live operation logs"
                />
              )}
            </div>
          </Surface>
        </div>

        <Surface className="p-6 lg:p-7" tone="raised">
          <div>
            <p className="zh-kicker">{t('attack.allDevices')}</p>
            <h2 className="mt-2 text-2xl font-semibold" style={{ color: 'var(--text-primary)' }}>
              Attack control center
            </h2>
            <p className="mt-3 text-sm leading-7" style={{ color: 'var(--text-secondary)' }}>
              {t('attack.allDevicesHint')}
            </p>
          </div>

          <Surface className="mt-6 p-4" tone="subtle">
            <div className="grid gap-4">
              <div>
                <label className="mb-2 block text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                  {t('attack.attackType')}
                </label>
                <select
                  className="zh-field"
                  onChange={(event) =>
                    setSelectedAttackType(event.target.value as AttackType)
                  }
                  value={selectedAttackType}
                >
                  {Object.entries(attackTypeMetadata).map(([value, metadata]) => (
                    <option key={value} value={value}>
                      {metadata.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <div className="mb-2 flex items-center justify-between gap-2">
                  <label className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                    {t('attack.intensityLabel')}
                  </label>
                  <Badge tone="warning">{globalIntensity}/10</Badge>
                </div>
                <input
                  className="w-full accent-[var(--accent)]"
                  max="10"
                  min="1"
                  onChange={(event) => setGlobalIntensity(parseInt(event.target.value, 10))}
                  type="range"
                  value={globalIntensity}
                />
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                  {t('attack.duration')}
                </label>
                <select
                  className="zh-field"
                  onChange={(event) => setGlobalDuration(parseInt(event.target.value, 10))}
                  value={globalDuration}
                >
                  <option value={30}>30s</option>
                  <option value={60}>60s</option>
                  <option value={120}>2min</option>
                  <option value={300}>5min</option>
                  <option value={600}>10min</option>
                </select>
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                  {t('attack.searchPlaceholder')}
                </label>
                <input
                  className="zh-field"
                  onChange={(event) => setSearchQuery(event.target.value)}
                  placeholder={t('attack.searchPlaceholder')}
                  type="text"
                  value={searchQuery}
                />
              </div>
            </div>
          </Surface>

          <div className="mt-6">
            {filteredDevices.length > 0 ? (
              <div className="zh-list">
                {filteredDevices.map((device) => {
                  const underAttack = isDeviceUnderAttack(device.mac);
                  const isLaunching = launchingMacs.has(device.mac.toLowerCase());
                  const isStopping = stoppingMacs.has(device.mac.toLowerCase());
                  const metadata = attackTypeMetadata[selectedAttackType];

                  return (
                    <div className="zh-list-item" key={device.mac}>
                      <DeviceAvatar
                        active={underAttack}
                        status={device.status}
                        type={device.type}
                      />
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <p className="truncate text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                            {getDeviceName(device, t('common.unknown'))}
                          </p>
                          {underAttack ? <Badge tone="danger">{t('attack.active')}</Badge> : null}
                        </div>
                        <p className="mt-1 text-sm" style={{ color: 'var(--text-secondary)' }}>
                          {device.ip} •{' '}
                          {device.display_vendor ||
                            device.manual_profile?.manual_vendor ||
                            device.vendor ||
                            device.vendor_guess ||
                            t('devices.unknownVendor')}
                        </p>
                        <p className="mt-1 text-xs" style={{ color: 'var(--text-tertiary)' }}>
                          {device.mac}
                        </p>
                      </div>
                      {underAttack ? (
                        <Button
                          loading={isStopping}
                          onClick={() => handleStopAttack(device.mac)}
                          size="sm"
                          variant="danger"
                        >
                          <Square className="h-4 w-4" />
                          {t('attack.stop')}
                        </Button>
                      ) : (
                        <Button
                          loading={isLaunching}
                          onClick={() => handleLaunchAttack(device)}
                          size="sm"
                          variant="secondary"
                        >
                          <Play className="h-4 w-4" />
                          {metadata.label}
                        </Button>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : (
              <EmptyState
                description={searchQuery ? t('attack.searchHint') : t('attack.emptyHint')}
                icon={Shield}
                title={searchQuery ? t('attack.searchEmpty') : t('attack.emptyTitle')}
              />
            )}
          </div>
        </Surface>
      </div>
    </div>
  );
};
