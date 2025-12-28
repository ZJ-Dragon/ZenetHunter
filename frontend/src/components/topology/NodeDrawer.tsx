import React from 'react';
import { X, Monitor, Smartphone, Router, Shield, Activity, Clock, Hash } from 'lucide-react';
import { TopologyNode } from '../../types/topology';
import { DeviceStatus } from '../../types/device';
import { AttackControl } from '../actions/AttackControl';
import { SchedulerControl } from '../actions/SchedulerControl';

interface NodeDrawerProps {
  node: TopologyNode | null;
  onClose: () => void;
}

export const NodeDrawer: React.FC<NodeDrawerProps> = ({ node, onClose }) => {
  if (!node) return null;

  const { data: device } = node;

  return (
    <div
      className="fixed inset-y-0 right-0 w-96 transform transition-transform duration-300 ease-out z-50 flex flex-col"
      style={{
        backgroundColor: 'var(--winui-surface)',
        boxShadow: 'var(--winui-shadow-xl)',
        borderLeft: '1px solid var(--winui-border-subtle)'
      }}
    >
      {/* Header */}
      <div
        className="px-6 py-4 border-b flex items-center justify-between"
        style={{
          borderColor: 'var(--winui-border-subtle)',
          backgroundColor: 'var(--winui-bg-tertiary)'
        }}
      >
        <h2 className="text-lg font-semibold" style={{ color: 'var(--winui-text-primary)' }}>Device Details</h2>
        <button
          onClick={onClose}
          className="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          style={{ color: 'var(--winui-text-secondary)' }}
        >
          <X className="h-6 w-6" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Identity Card - WinUI3 Style */}
        <div className="card-winui p-4 flex items-start space-x-4">
          <div className="flex-shrink-0">
            {device.type === 'router' ? (
              <Router className="h-10 w-10" style={{ color: '#9a4dff' }} />
            ) : device.type === 'mobile' ? (
              <Smartphone className="h-10 w-10" style={{ color: '#107c10' }} />
            ) : (
              <Monitor className="h-10 w-10" style={{ color: 'var(--winui-accent)' }} />
            )}
          </div>
          <div>
            <h3 className="text-lg font-semibold" style={{ color: 'var(--winui-text-primary)' }}>{device.name || 'Unknown Device'}</h3>
            <p className="text-sm" style={{ color: 'var(--winui-text-secondary)' }}>{device.vendor || 'Unknown Vendor'}</p>
            <div
              className="mt-2 inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold"
              style={{
                backgroundColor: device.status === DeviceStatus.ONLINE ? 'rgba(16, 124, 16, 0.1)' :
                  device.status === DeviceStatus.BLOCKED ? 'rgba(209, 52, 56, 0.1)' :
                  'var(--winui-bg-tertiary)',
                color: device.status === DeviceStatus.ONLINE ? '#107c10' :
                  device.status === DeviceStatus.BLOCKED ? '#d13438' :
                  'var(--winui-text-secondary)',
                borderRadius: 'var(--winui-radius-lg)'
              }}
            >
              {device.status.toUpperCase()}
            </div>
          </div>
        </div>

        {/* Network Info */}
        <div>
          <h4 className="text-sm font-semibold uppercase tracking-wider mb-3" style={{ color: 'var(--winui-text-secondary)' }}>Network Information</h4>
          <dl className="grid grid-cols-1 gap-4">
            <div className="flex items-center">
              <Activity className="h-5 w-5 mr-3" style={{ color: 'var(--winui-text-tertiary)' }} />
              <div>
                <dt className="text-xs" style={{ color: 'var(--winui-text-secondary)' }}>IP Address</dt>
                <dd className="text-sm font-semibold" style={{ color: 'var(--winui-text-primary)' }}>{device.ip}</dd>
              </div>
            </div>
            <div className="flex items-center">
              <Hash className="h-5 w-5 mr-3" style={{ color: 'var(--winui-text-tertiary)' }} />
              <div>
                <dt className="text-xs" style={{ color: 'var(--winui-text-secondary)' }}>MAC Address</dt>
                <dd className="text-sm font-semibold font-mono" style={{ color: 'var(--winui-text-primary)' }}>{device.mac}</dd>
              </div>
            </div>
          </dl>
        </div>

        {/* Activity Info */}
        <div>
          <h4 className="text-sm font-semibold uppercase tracking-wider mb-3" style={{ color: 'var(--winui-text-secondary)' }}>Activity</h4>
          <dl className="grid grid-cols-1 gap-4">
            <div className="flex items-center">
              <Clock className="h-5 w-5 mr-3" style={{ color: 'var(--winui-text-tertiary)' }} />
              <div>
                <dt className="text-xs" style={{ color: 'var(--winui-text-secondary)' }}>Last Seen</dt>
                <dd className="text-sm font-semibold" style={{ color: 'var(--winui-text-primary)' }}>
                  {new Date(device.last_seen).toLocaleString()}
                </dd>
              </div>
            </div>
            <div className="flex items-center">
              <Shield className="h-5 w-5 mr-3" style={{ color: 'var(--winui-text-tertiary)' }} />
              <div>
                <dt className="text-xs" style={{ color: 'var(--winui-text-secondary)' }}>Attack Status</dt>
                <dd className="text-sm font-semibold" style={{ color: 'var(--winui-text-primary)' }}>{device.attack_status}</dd>
              </div>
            </div>
          </dl>
        </div>
      </div>

      {/* Actions */}
      <div
        className="border-t p-4 flex flex-col space-y-3"
        style={{
          borderColor: 'var(--winui-border-subtle)',
          backgroundColor: 'var(--winui-bg-tertiary)'
        }}
      >
        <SchedulerControl device={device} className="w-full justify-center" />
        <AttackControl device={device} className="w-full justify-center" />
      </div>
    </div>
  );
};
