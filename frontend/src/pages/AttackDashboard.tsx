import React, { useEffect, useState } from 'react';
import { deviceService } from '../lib/services/device';
import { Device, AttackStatus } from '../types/device';
import { AttackControl } from '../components/actions/AttackControl';
import { RefreshCw, ShieldAlert, Activity } from 'lucide-react';
import { clsx } from 'clsx';
import { useWebSocketEvent } from '../contexts/WebSocketContext';
import { WSEventType } from '../types/websocket';

export const AttackDashboard: React.FC = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [isLoading, setIsLoading] = useState(true);

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

  useWebSocketEvent(WSEventType.ATTACK_STARTED, fetchDevices);
  useWebSocketEvent(WSEventType.ATTACK_STOPPED, fetchDevices);
  useWebSocketEvent(WSEventType.ATTACK_FINISHED, fetchDevices);

  const activeAttacks = devices.filter(d => d.attack_status === AttackStatus.RUNNING);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-semibold flex items-center gap-2" style={{ color: 'var(--winui-text-primary)', letterSpacing: '-0.02em' }}>
            <ShieldAlert className="h-8 w-8" style={{ color: '#d13438' }} />
            Active Interference Operations
          </h1>
          <p className="mt-1 text-sm" style={{ color: 'var(--winui-text-secondary)' }}>
            Monitor and control active interference tasks.
          </p>
        </div>
        <button
          onClick={fetchDevices}
          className="btn-winui-secondary inline-flex items-center"
        >
          <RefreshCw className={clsx("h-4 w-4 mr-2", isLoading && "animate-spin")} />
          Refresh
        </button>
      </div>

      {/* Stats - WinUI3 Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
        <div className="card-winui overflow-hidden">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium truncate" style={{ color: 'var(--winui-text-secondary)' }}>Active Attacks</dt>
            <dd className="mt-1 text-3xl font-semibold" style={{ color: 'var(--winui-text-primary)' }}>{activeAttacks.length}</dd>
          </div>
        </div>
        <div className="card-winui overflow-hidden">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium truncate" style={{ color: 'var(--winui-text-secondary)' }}>Total Devices</dt>
            <dd className="mt-1 text-3xl font-semibold" style={{ color: 'var(--winui-text-primary)' }}>{devices.length}</dd>
          </div>
        </div>
        <div className="card-winui overflow-hidden">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium truncate" style={{ color: 'var(--winui-text-secondary)' }}>System Status</dt>
            <dd className="mt-1 text-3xl font-semibold flex items-center gap-2" style={{ color: '#107c10' }}>
              <Activity className="h-6 w-6" />
              Operational
            </dd>
          </div>
        </div>
      </div>

      {/* Active Attacks List - WinUI3 Style */}
      <div className="card-winui overflow-hidden">
        <div className="px-4 py-5 border-b sm:px-6" style={{ borderColor: 'var(--winui-border-subtle)' }}>
          <h3 className="text-lg leading-6 font-semibold" style={{ color: 'var(--winui-text-primary)' }}>
            Targets Under Interference
          </h3>
        </div>
        <ul>
          {activeAttacks.length > 0 ? (
            activeAttacks.map((device) => (
              <li
                key={device.mac}
                className="px-4 py-4 sm:px-6 transition-colors duration-150"
                style={{ borderBottom: '1px solid var(--winui-border-subtle)' }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = 'var(--winui-bg-tertiary)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                }}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className="h-10 w-10 rounded-full flex items-center justify-center" style={{ backgroundColor: 'rgba(209, 52, 56, 0.1)' }}>
                        <ShieldAlert className="h-6 w-6" style={{ color: '#d13438' }} />
                      </div>
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-semibold" style={{ color: 'var(--winui-text-primary)' }}>
                        {device.name || device.mac}
                      </div>
                      <div className="text-sm" style={{ color: 'var(--winui-text-secondary)' }}>
                        {device.vendor || 'Unknown Vendor'} • {device.ip}
                      </div>
                    </div>
                  </div>
                  <div>
                    <AttackControl device={device} />
                  </div>
                </div>
              </li>
            ))
          ) : (
            <li className="px-4 py-8 text-center" style={{ color: 'var(--winui-text-secondary)' }}>
              No active interference tasks running.
            </li>
          )}
        </ul>
      </div>
    </div>
  );
};
