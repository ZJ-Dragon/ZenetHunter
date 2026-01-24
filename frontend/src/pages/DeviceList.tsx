import React, { useEffect, useState, useMemo } from 'react';
import { Device, DeviceStatus, DeviceType } from '../types/device';
import { deviceService } from '../lib/services/device';
import { AttackControl } from '../components/actions/AttackControl';
import { SchedulerControl } from '../components/actions/SchedulerControl';
import { ScanButton } from '../components/actions/ScanButton';
import { Search, Filter, RefreshCw, Laptop, Smartphone, Router, Shield, Wifi, CheckCircle, AlertCircle } from 'lucide-react';
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

  // Listen for scan started - clear old devices
  useWebSocketEvent('scanStarted', () => {
    setDevices([]);
    setIsLoading(true);
  });
  
  // Listen for scan completed
  useWebSocketEvent('scanCompleted', () => {
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
      const matchesSearch =
        device.name?.toLowerCase().includes(search.toLowerCase()) ||
        device.ip.includes(search) ||
        device.mac.toLowerCase().includes(search.toLowerCase()) ||
        device.vendor?.toLowerCase().includes(search.toLowerCase()) ||
        device.vendor_guess?.toLowerCase().includes(search.toLowerCase()) ||
        device.model_guess?.toLowerCase().includes(search.toLowerCase());

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
            className="input-winui pl-10"
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
              className="input-winui pl-10"
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
                <th scope="col" className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--winui-text-secondary)' }}>Actions</th>
              </tr>
            </thead>
            <tbody style={{ backgroundColor: 'var(--winui-surface)' }}>
              {filteredDevices.length > 0 ? (
                filteredDevices.map((device) => (
                  <tr
                    key={device.mac}
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
                          <div className="text-sm font-medium" style={{ color: 'var(--winui-text-primary)' }}>
                            {device.name || device.vendor_guess || 'Unknown Device'}
                          </div>
                          <div className="text-sm flex items-center gap-2" style={{ color: 'var(--winui-text-secondary)' }}>
                            {device.vendor_guess || device.vendor || 'Unknown Vendor'}
                            {device.model_guess && (
                              <span className="text-xs" style={{ color: 'var(--winui-text-tertiary)' }}>
                                • {device.model_guess}
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
                      <div className="flex items-center space-x-2">
                        <SchedulerControl device={device} />
                        <AttackControl device={device} />
                      </div>
                    </td>
                  </tr>
                ))
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
