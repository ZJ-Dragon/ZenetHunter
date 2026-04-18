import React, { useEffect, useMemo, useState } from 'react';
import {
  FileJson,
  Filter,
  Loader2,
  Network,
  RefreshCw,
  Search,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { useTranslation } from 'react-i18next';
import { ScanButton } from '../components/actions/ScanButton';
import { Button } from '../components/ui/Button';
import { DeviceAvatar } from '../components/ui/DeviceAvatar';
import { Badge } from '../components/ui/Badge';
import { DeviceStatusBadge } from '../components/ui/DeviceStatusBadge';
import { EmptyState } from '../components/ui/EmptyState';
import { PageHeader } from '../components/ui/PageHeader';
import { Surface } from '../components/ui/Surface';
import { useWebSocketEvent } from '../contexts/WebSocketContext';
import { deviceService } from '../lib/services/device';
import { observationService } from '../lib/services/observations';
import { Device, DeviceStatus } from '../types/device';
import { ProbeObservation } from '../types/observation';
import { WSEventType } from '../types/websocket';

const getDeviceName = (device: Device, fallback: string) =>
  device.display_name ||
  device.manual_profile?.manual_name ||
  device.name ||
  device.alias ||
  device.model ||
  device.model_guess ||
  fallback;

const getDeviceVendor = (device: Device, fallback: string) =>
  device.display_vendor ||
  device.manual_profile?.manual_vendor ||
  device.vendor ||
  device.vendor_guess ||
  fallback;

const getConfidenceTone = (confidence: number) => {
  if (confidence >= 70) {
    return 'success';
  }
  if (confidence >= 40) {
    return 'warning';
  }
  return 'neutral';
};

export const DeviceList: React.FC = () => {
  const { t } = useTranslation();
  const [devices, setDevices] = useState<Device[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState<DeviceStatus | 'all'>('all');
  const [expandedMac, setExpandedMac] = useState<string | null>(null);
  const [observationsByMac, setObservationsByMac] = useState<
    Record<string, ProbeObservation[]>
  >({});
  const [observationsLoading, setObservationsLoading] = useState(false);

  const fetchDevices = async () => {
    setIsLoading(true);
    try {
      const data = await deviceService.getAll();
      setDevices(data);
    } catch (error) {
      console.error('Failed to fetch devices:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDevices();
  }, []);

  const loadObservations = async (mac: string) => {
    setObservationsLoading(true);
    try {
      const data = await observationService.listByDevice(mac, 5);
      setObservationsByMac((previous) => ({ ...previous, [mac]: data }));
    } catch (error) {
      console.error('Failed to fetch observations:', error);
    } finally {
      setObservationsLoading(false);
    }
  };

  const toggleObservations = (mac: string) => {
    if (expandedMac === mac) {
      setExpandedMac(null);
      return;
    }

    setExpandedMac(mac);
    if (!observationsByMac[mac]) {
      loadObservations(mac);
    }
  };

  const copyObservation = async (mac: string) => {
    const observations = observationsByMac[mac];
    if (!observations || observations.length === 0) {
      return;
    }

    try {
      await navigator.clipboard.writeText(JSON.stringify(observations[0], null, 2));
      toast.success(t('devices.observationCopied'));
    } catch (error) {
      console.error('Failed to copy observation', error);
      toast.error(t('devices.copyFailed'));
    }
  };

  useWebSocketEvent(WSEventType.SCAN_STARTED, () => {
    setDevices([]);
    setIsLoading(true);
  });
  useWebSocketEvent(WSEventType.SCAN_COMPLETED, () => {
    fetchDevices();
    setIsLoading(false);
  });
  useWebSocketEvent(WSEventType.DEVICE_RECOGNITION_UPDATED, fetchDevices);
  useWebSocketEvent(WSEventType.DEVICE_ADDED, fetchDevices);

  const filteredDevices = useMemo(() => {
    return devices.filter((device) => {
      const names = [
        device.display_name,
        device.name,
        device.alias,
        device.model,
        device.model_guess,
        device.name_auto,
        device.manual_profile?.manual_name,
      ].filter(Boolean) as string[];
      const vendors = [
        device.display_vendor,
        device.vendor,
        device.vendor_guess,
        device.vendor_auto,
        device.manual_profile?.manual_vendor,
      ].filter(Boolean) as string[];

      const matchesSearch =
        names.some((name) => name.toLowerCase().includes(search.toLowerCase())) ||
        vendors.some((vendor) => vendor.toLowerCase().includes(search.toLowerCase())) ||
        device.ip.includes(search) ||
        device.mac.toLowerCase().includes(search.toLowerCase());

      const matchesStatus =
        filterStatus === 'all' || device.status === filterStatus;

      return matchesSearch && matchesStatus;
    });
  }, [devices, filterStatus, search]);

  const onlineCount = devices.filter((device) => device.status === DeviceStatus.ONLINE).length;
  const blockedCount = devices.filter((device) => device.status === DeviceStatus.BLOCKED).length;

  return (
    <div className="zh-page">
      <PageHeader
        actions={
          <>
            <ScanButton />
            <Button
              leadingIcon={<RefreshCw className={isLoading ? 'h-4 w-4 animate-spin' : 'h-4 w-4'} />}
              onClick={fetchDevices}
              variant="secondary"
            >
              {t('devices.refresh')}
            </Button>
          </>
        }
        eyebrow={t('devices.eyebrow')}
        icon={Network}
        subtitle={t('devices.subtitle')}
        title={t('devices.title')}
      />

      <div className="zh-status-strip">
        <Badge tone="accent">{t('devices.visibleCount', { count: filteredDevices.length })}</Badge>
        <Badge tone="success">{t('devices.onlineCount', { count: onlineCount })}</Badge>
        <Badge tone="danger">{t('devices.blockedCount', { count: blockedCount })}</Badge>
      </div>

      <Surface className="p-5 lg:p-6" tone="raised">
        <div className="grid gap-4 lg:grid-cols-[1fr_14rem]">
          <div className="zh-field-wrap">
            <Search className="zh-field-icon h-4 w-4" />
            <input
              className="zh-field"
              onChange={(event) => setSearch(event.target.value)}
              placeholder={t('devices.searchPlaceholder')}
              type="text"
              value={search}
            />
          </div>
          <div className="zh-field-wrap">
            <Filter className="zh-field-icon h-4 w-4" />
            <select
              className="zh-field"
              onChange={(event) =>
                setFilterStatus(event.target.value as DeviceStatus | 'all')
              }
              value={filterStatus}
            >
              <option value="all">{t('devices.statusAll')}</option>
              <option value={DeviceStatus.ONLINE}>{t('devices.statusOnline')}</option>
              <option value={DeviceStatus.OFFLINE}>{t('devices.statusOffline')}</option>
              <option value={DeviceStatus.BLOCKED}>{t('devices.statusBlocked')}</option>
            </select>
          </div>
        </div>
      </Surface>

      <Surface className="zh-table-shell" tone="raised">
        <div className="zh-table-scroll">
          <table className="zh-table">
            <thead>
              <tr>
                <th>{t('devices.colDevice')}</th>
                <th>{t('devices.colIp')}</th>
                <th>{t('devices.colMac')}</th>
                <th>{t('devices.colStatus')}</th>
                <th>{t('devices.colLastSeen')}</th>
                <th>{t('devices.colMore')}</th>
              </tr>
            </thead>
            <tbody>
              {filteredDevices.length > 0 ? (
                filteredDevices.map((device) => {
                  const manualName = device.manual_profile?.manual_name ?? device.name_manual;
                  const manualVendor =
                    device.manual_profile?.manual_vendor ?? device.vendor_manual;
                  const hasManual = Boolean(
                    manualName || manualVendor || device.manual_profile_id
                  );
                  const confidence = device.recognition_confidence ?? 0;

                  return (
                    <React.Fragment key={device.mac}>
                      <tr>
                        <td>
                          <div className="flex items-center gap-4">
                            <DeviceAvatar status={device.status} type={device.type} />
                            <div className="min-w-0">
                              <div className="flex flex-wrap items-center gap-2">
                                <p
                                  className="truncate text-sm font-semibold"
                                  style={{ color: 'var(--text-primary)' }}
                                >
                                  {getDeviceName(device, t('devices.unknownDevice'))}
                                </p>
                                {hasManual ? (
                                  <Badge tone="success">{t('devices.manualTag')}</Badge>
                                ) : null}
                                {confidence > 0 ? (
                                  <Badge
                                    title={t('devices.confidenceTitle', {
                                      value: confidence,
                                    })}
                                    tone={getConfidenceTone(confidence)}
                                  >
                                    {confidence}%
                                  </Badge>
                                ) : null}
                              </div>
                              <p
                                className="mt-1 text-sm"
                                style={{ color: 'var(--text-secondary)' }}
                              >
                                {getDeviceVendor(device, t('devices.unknownVendor'))}
                                {device.model || device.model_guess
                                  ? ` • ${device.model || device.model_guess}`
                                  : ''}
                              </p>
                            </div>
                          </div>
                        </td>
                        <td style={{ color: 'var(--text-primary)' }}>{device.ip}</td>
                        <td className="font-mono text-sm" style={{ color: 'var(--text-secondary)' }}>
                          {device.mac}
                        </td>
                        <td>
                          <DeviceStatusBadge status={device.status} />
                        </td>
                        <td style={{ color: 'var(--text-secondary)' }}>
                          {new Date(device.last_seen).toLocaleString()}
                        </td>
                        <td>
                          <Button
                            onClick={() => toggleObservations(device.mac)}
                            size="sm"
                            variant="secondary"
                          >
                            {expandedMac === device.mac ? t('devices.hide') : t('devices.more')}
                          </Button>
                        </td>
                      </tr>
                      {expandedMac === device.mac ? (
                        <tr>
                          <td colSpan={6}>
                            <Surface className="p-4" tone="inset">
                              <div className="zh-toolbar zh-toolbar--spread">
                                <div>
                                  <p className="zh-kicker">{t('devices.probeObservations')}</p>
                                  <p
                                    className="mt-2 text-sm"
                                    style={{ color: 'var(--text-secondary)' }}
                                  >
                                    {t('devices.observationsDesc')}
                                  </p>
                                </div>
                                {observationsLoading ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
                                ) : null}
                              </div>
                              <div className="mt-4 space-y-3">
                                {observationsLoading ? (
                                  <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                                    {t('devices.loading')}
                                  </p>
                                ) : null}
                                {!observationsLoading &&
                                (!observationsByMac[device.mac] ||
                                  observationsByMac[device.mac].length === 0) ? (
                                  <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                                    {t('devices.noObservations')}
                                  </p>
                                ) : null}
                                {!observationsLoading &&
                                  observationsByMac[device.mac]?.map((observation) => (
                                    <Surface className="p-4" key={observation.id} tone="subtle">
                                      <div className="zh-toolbar zh-toolbar--spread">
                                        <div className="zh-toolbar__group">
                                          <Badge tone="neutral">{observation.protocol}</Badge>
                                          <span
                                            className="text-xs"
                                            style={{ color: 'var(--text-tertiary)' }}
                                          >
                                            {new Date(observation.timestamp).toLocaleString()}
                                          </span>
                                        </div>
                                        <Button
                                          leadingIcon={<FileJson className="h-4 w-4" />}
                                          onClick={() => copyObservation(device.mac)}
                                          size="sm"
                                          variant="ghost"
                                        >
                                          {t('devices.copyObservation')}
                                        </Button>
                                      </div>
                                      <p
                                        className="mt-3 text-sm"
                                        style={{ color: 'var(--text-primary)' }}
                                      >
                                        {observation.raw_summary || t('devices.noSummary')}
                                      </p>
                                      {observation.keyword_hits?.length ? (
                                        <p
                                          className="mt-2 text-xs"
                                          style={{ color: 'var(--text-secondary)' }}
                                        >
                                          {t('devices.keywordHits', {
                                            count: observation.keyword_hits.length,
                                            top:
                                              observation.keyword_hits[0].infer_summary ||
                                              observation.keyword_hits[0].rule_id,
                                          })}
                                        </p>
                                      ) : null}
                                      <div className="mt-3 flex flex-wrap gap-2">
                                        {observation.keywords.slice(0, 10).map((keyword) => (
                                          <Badge key={keyword} tone="neutral">
                                            {keyword}
                                          </Badge>
                                        ))}
                                      </div>
                                    </Surface>
                                  ))}
                              </div>
                            </Surface>
                          </td>
                        </tr>
                      ) : null}
                    </React.Fragment>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={6}>
                    <EmptyState
                      action={<ScanButton />}
                      description={t('devices.emptyHint')}
                      icon={Search}
                      title={t('devices.emptyTitle')}
                    />
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Surface>
    </div>
  );
};
