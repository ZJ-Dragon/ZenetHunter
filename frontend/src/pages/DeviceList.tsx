import React, { useEffect, useState, useMemo } from 'react';
import { Device, DeviceStatus, DeviceType } from '../types/device';
import { deviceService } from '../lib/services/device';
import { ScanButton } from '../components/actions/ScanButton';
import { observationService } from '../lib/services/observations';
import { ProbeObservation } from '../types/observation';
import { Search, Filter, RefreshCw, Laptop, Smartphone, Router, Shield, Wifi, CheckCircle, AlertCircle, MoreHorizontal, Loader2, FileJson } from 'lucide-react';
import { clsx } from 'clsx';
import { useWebSocketEvent } from '../contexts/WebSocketContext';
import { WSEventType } from '../types/websocket';

const DeviceIcon = ({ type }: { type: DeviceType }) => {
  switch (type) {
    case DeviceType.ROUTER:
      return <Router className="h-5 w-5 text-purple-500" />;
    case DeviceType.PC:
      return <Laptop className="h-5 w-5 text-blue-500" />;
    case DeviceType.MOBILE:
      return <Smartphone className="h-5 w-5 text-green-500" />;
    case DeviceType.IOT:
      return <Wifi className="h-5 w-5 text-orange-500" />;
    default:
      return <Shield className="h-5 w-5 text-gray-400" />;
  }
};

const StatusBadge = ({ status }: { status: DeviceStatus }) => {
  const statusStyles: Record<DeviceStatus, { bg: string; text: string }> = {
    [DeviceStatus.ONLINE]: { bg: 'rgba(16, 124, 16, 0.1)', text: '#107c10' },
    [DeviceStatus.OFFLINE]: { bg: 'var(--winui-bg-tertiary)', text: 'var(--winui-text-secondary)' },
    [DeviceStatus.BLOCKED]: { bg: 'rgba(209, 52, 56, 0.1)', text: '#d13438' },
  };

  const style = statusStyles[status];

  return (
    <span
      className="px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full"
      style={{
        backgroundColor: style.bg,
        color: style.text,
        borderRadius: 'var(--winui-radius-lg)'
      }}
    >
      {status}
    </span>
  );
};

export const DeviceList: React.FC = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState<DeviceStatus | 'all'>('all');
  const [expandedMac, setExpandedMac] = useState<string | null>(null);
  const [observationsByMac, setObservationsByMac] = useState<Record<string, ProbeObservation[]>>({});
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
      setObservationsByMac((prev) => ({ ...prev, [mac]: data }));
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
    const obs = observationsByMac[mac];
    if (!obs || obs.length === 0) return;
    try {
      await navigator.clipboard.writeText(JSON.stringify(obs[0], null, 2));
    } catch (err) {
      console.error('Failed to copy observation', err);
    }
  };

  // Listen for scan started - clear old devices
  useWebSocketEvent(WSEventType.SCAN_STARTED, () => {
    setDevices([]);
    setIsLoading(true);
  });

  // Listen for scan completed
  useWebSocketEvent(WSEventType.SCAN_COMPLETED, () => {
    fetchDevices();
    setIsLoading(false);
  });

  // Listen for device recognition updates
  useWebSocketEvent(WSEventType.DEVICE_RECOGNITION_UPDATED, () => {
    fetchDevices();
  });

  useWebSocketEvent(WSEventType.DEVICE_ADDED, () => {
    fetchDevices();
  });

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
        names.some((n) => n.toLowerCase().includes(search.toLowerCase())) ||
        vendors.some((v) => v.toLowerCase().includes(search.toLowerCase())) ||
        device.ip.includes(search) ||
        device.mac.toLowerCase().includes(search.toLowerCase());

      const matchesStatus = filterStatus === 'all' || device.status === filterStatus;

      return matchesSearch && matchesStatus;
    });
  }, [devices, search, filterStatus]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl font-semibold" style={{ color: 'var(--winui-text-primary)', letterSpacing: '-0.02em' }}>Network Devices</h1>
        <div className="flex items-center gap-2">
          <ScanButton />
          <button
            onClick={fetchDevices}
            className="btn-winui-secondary inline-flex items-center"
          >
            <RefreshCw className={clsx("h-4 w-4 mr-2", isLoading && "animate-spin")} />
            Refresh
          </button>
        </div>
      </div>

      {/* Filters - WinUI3 Style */}
      <div className="card-winui p-4 flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-5 w-5" style={{ color: 'var(--winui-text-tertiary)' }} />
          </div>
          <input
            type="text"
            className="input-winui"
            style={{ paddingLeft: '42px' }}
            placeholder="Search by Name, IP, MAC or Vendor..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="w-full sm:w-48">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Filter className="h-5 w-5" style={{ color: 'var(--winui-text-tertiary)' }} />
            </div>
            <select
              className="input-winui"
              style={{ paddingLeft: '42px' }}
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value as DeviceStatus | 'all')}
            >
              <option value="all">All Status</option>
              <option value={DeviceStatus.ONLINE}>Online</option>
              <option value={DeviceStatus.OFFLINE}>Offline</option>
              <option value={DeviceStatus.BLOCKED}>Blocked</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table - WinUI3 Style */}
      <div className="card-winui overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full" style={{ borderCollapse: 'separate', borderSpacing: 0 }}>
            <thead style={{ backgroundColor: 'var(--winui-bg-tertiary)' }}>
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--winui-text-secondary)' }}>Device</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--winui-text-secondary)' }}>IP Address</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--winui-text-secondary)' }}>MAC Address</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--winui-text-secondary)' }}>Status</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--winui-text-secondary)' }}>Last Seen</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--winui-text-secondary)' }}>More</th>
              </tr>
            </thead>
            <tbody style={{ backgroundColor: 'var(--winui-surface)' }}>
              {filteredDevices.length > 0 ? (
                filteredDevices.map((device) => {
                  const manualName = device.manual_profile?.manual_name ?? device.name_manual;
                  const manualVendor = device.manual_profile?.manual_vendor ?? device.vendor_manual;
                  const displayName = device.display_name || manualName || device.name || device.alias || device.model || device.model_guess || 'Unknown Device';
                  const displayVendor = device.display_vendor || manualVendor || device.vendor || device.vendor_guess || 'Unknown Vendor';
                  const hasManual = Boolean(manualName || manualVendor || device.manual_profile_id);

                  return (
                    <React.Fragment key={device.mac}>
                      <tr
                        className="transition-colors duration-150"
                        style={{
                          borderBottom: '1px solid var(--winui-border-subtle)',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = 'var(--winui-bg-tertiary)';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = 'var(--winui-surface)';
                        }}
                      >
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className="flex-shrink-0 h-10 w-10 flex items-center justify-center rounded-full" style={{ backgroundColor: 'var(--winui-bg-tertiary)' }}>
                              <DeviceIcon type={device.type} />
                            </div>
                            <div className="ml-4">
                              <div className="text-sm font-medium flex items-center gap-2" style={{ color: 'var(--winui-text-primary)' }}>
                                {displayName}
                                {hasManual && (
                                  <span className="text-xxs px-2 py-0.5 rounded-full" style={{ backgroundColor: 'rgba(16, 124, 16, 0.1)', color: '#107c10' }}>
                                    Manual
                                  </span>
                                )}
                              </div>
                              <div className="text-sm flex items-center gap-2" style={{ color: 'var(--winui-text-secondary)' }}>
                                {displayVendor}
                                {(device.model || device.model_guess) && (
                                  <span className="text-xs" style={{ color: 'var(--winui-text-tertiary)' }}>
                                    • {device.model || device.model_guess}
                                  </span>
                                )}
                                {device.recognition_confidence !== null && device.recognition_confidence > 0 && (
                                  <span
                                    className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded"
                                    style={{
                                      backgroundColor: device.recognition_confidence >= 70
                                        ? 'rgba(16, 124, 16, 0.1)'
                                        : device.recognition_confidence >= 40
                                        ? 'rgba(245, 158, 11, 0.1)'
                                        : 'rgba(107, 114, 128, 0.1)',
                                      color: device.recognition_confidence >= 70
                                        ? '#107c10'
                                        : device.recognition_confidence >= 40
                                        ? '#f59e0b'
                                        : '#6b7280',
                                    }}
                                    title={`Recognition confidence: ${device.recognition_confidence}%`}
                                  >
                                    {device.recognition_confidence >= 70 ? (
                                      <CheckCircle className="h-3 w-3" />
                                    ) : (
                                      <AlertCircle className="h-3 w-3" />
                                    )}
                                    {device.recognition_confidence}%
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm" style={{ color: 'var(--winui-text-primary)' }}>{device.ip}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap font-mono text-sm" style={{ color: 'var(--winui-text-secondary)' }}>
                          {device.mac}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <StatusBadge status={device.status} />
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm" style={{ color: 'var(--winui-text-secondary)' }}>
                          {new Date(device.last_seen).toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <button
                            onClick={() => toggleObservations(device.mac)}
                            className="btn-winui-secondary inline-flex items-center gap-1"
                          >
                            <MoreHorizontal className="h-4 w-4" />
                            More
                          </button>
                        </td>
                      </tr>
                      {expandedMac === device.mac && (
                        <tr>
                          <td colSpan={6} className="px-6 py-3" style={{ backgroundColor: 'var(--winui-bg-tertiary)' }}>
                            <div className="flex items-center justify-between mb-2">
                              <div className="text-xs font-semibold" style={{ color: 'var(--winui-text-secondary)' }}>
                                Probe observations
                              </div>
                              {observationsLoading && <Loader2 className="h-4 w-4 animate-spin" />}
                            </div>
                            {observationsLoading && (
                              <p className="text-xs" style={{ color: 'var(--winui-text-secondary)' }}>Loading...</p>
                            )}
                            {!observationsLoading && (!observationsByMac[device.mac] || observationsByMac[device.mac].length === 0) && (
                              <p className="text-xs" style={{ color: 'var(--winui-text-secondary)' }}>No observations yet.</p>
                            )}
                            {!observationsLoading && observationsByMac[device.mac] && observationsByMac[device.mac].length > 0 && (
                              <div className="space-y-2">
                                {observationsByMac[device.mac].map((obs) => (
                                  <div key={obs.id} className="p-3 rounded border" style={{ borderColor: 'var(--winui-border-subtle)', backgroundColor: 'var(--winui-surface)' }}>
                                    <div className="flex items-center justify-between">
                                      <div className="flex items-center gap-2">
                                        <span className="text-xxs px-2 py-1 rounded-full" style={{ backgroundColor: 'rgba(0,0,0,0.05)', color: 'var(--winui-text-secondary)' }}>
                                          {obs.protocol}
                                        </span>
                                        <span className="text-xs" style={{ color: 'var(--winui-text-tertiary)' }}>
                                          {new Date(obs.timestamp).toLocaleString()}
                                        </span>
                                      </div>
                                      <button
                                        onClick={() => copyObservation(device.mac)}
                                        className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800"
                                        title="Copy first observation JSON"
                                      >
                                        <FileJson className="h-4 w-4" />
                                      </button>
                                    </div>
                                    <div className="mt-1 text-xs" style={{ color: 'var(--winui-text-primary)' }}>
                                      {obs.raw_summary || 'No summary'}
                                    </div>
                                    {obs.keyword_hits && obs.keyword_hits.length > 0 && (
                                      <div className="mt-1 text-xxs" style={{ color: 'var(--winui-text-secondary)' }}>
                                        {obs.keyword_hits.length} keyword hits (top: {obs.keyword_hits[0].infer_summary || obs.keyword_hits[0].rule_id})
                                      </div>
                                    )}
                                    <div className="mt-1 flex flex-wrap gap-1">
                                      {obs.keywords.slice(0, 10).map((kw) => (
                                        <span key={kw} className="text-xxs px-2 py-0.5 rounded-full" style={{ backgroundColor: 'rgba(0,0,0,0.05)', color: 'var(--winui-text-secondary)' }}>
                                          {kw}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            )}
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center">
                    <div className="flex flex-col items-center justify-center">
                      <Search className="h-12 w-12 mb-4" style={{ color: 'var(--winui-text-tertiary)' }} />
                      <h3 className="text-lg font-semibold mb-1" style={{ color: 'var(--winui-text-primary)' }}>No devices found</h3>
                      <p className="mb-6" style={{ color: 'var(--winui-text-secondary)' }}>Start a network scan to discover devices on your network.</p>
                      <ScanButton />
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
