import React, { useState } from 'react';
import { X, Monitor, Smartphone, Router, Shield, Activity, Clock, Hash, CheckCircle, AlertCircle, ChevronDown, ChevronUp, Eye } from 'lucide-react';
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
  const [showEvidence, setShowEvidence] = useState(false);

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
          <div className="flex-1">
            <h3 className="text-lg font-semibold" style={{ color: 'var(--winui-text-primary)' }}>
              {device.name || device.vendor_guess || 'Unknown Device'}
            </h3>
            <p className="text-sm" style={{ color: 'var(--winui-text-secondary)' }}>
              {device.vendor_guess || device.vendor || 'Unknown Vendor'}
              {device.model_guess && (
                <span className="ml-2" style={{ color: 'var(--winui-text-tertiary)' }}>
                  • {device.model_guess}
                </span>
              )}
            </p>
            <div className="mt-2 flex items-center gap-2 flex-wrap">
              <div
                className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold"
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
              {device.recognition_confidence !== null && device.recognition_confidence > 0 && (
                <div
                  className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs"
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
                </div>
              )}
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

        {/* Recognition Info */}
        {(device.vendor_guess || device.model_guess || device.recognition_evidence) && (
          <div>
            <h4 className="text-sm font-semibold uppercase tracking-wider mb-3" style={{ color: 'var(--winui-text-secondary)' }}>
              Device Recognition
            </h4>
            <div className="card-winui p-4 space-y-3">
              {device.vendor_guess && (
                <div>
                  <dt className="text-xs mb-1" style={{ color: 'var(--winui-text-secondary)' }}>Vendor Guess</dt>
                  <dd className="text-sm font-semibold" style={{ color: 'var(--winui-text-primary)' }}>
                    {device.vendor_guess}
                  </dd>
                </div>
              )}
              {device.model_guess && (
                <div>
                  <dt className="text-xs mb-1" style={{ color: 'var(--winui-text-secondary)' }}>Model Guess</dt>
                  <dd className="text-sm font-semibold" style={{ color: 'var(--winui-text-primary)' }}>
                    {device.model_guess}
                  </dd>
                </div>
              )}
              {device.recognition_evidence && (
                <div>
                  <button
                    onClick={() => setShowEvidence(!showEvidence)}
                    className="w-full flex items-center justify-between text-sm font-medium mb-2"
                    style={{ color: 'var(--winui-text-primary)' }}
                  >
                    <span className="flex items-center gap-2">
                      <Eye className="h-4 w-4" />
                      Evidence
                    </span>
                    {showEvidence ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  </button>
                  {showEvidence && (
                    <div className="mt-2 space-y-2 text-xs" style={{ color: 'var(--winui-text-secondary)' }}>
                      {device.recognition_evidence.sources && device.recognition_evidence.sources.length > 0 && (
                        <div>
                          <span className="font-semibold">Sources: </span>
                          {device.recognition_evidence.sources.join(', ')}
                        </div>
                      )}
                      {device.recognition_evidence.matched_fields && device.recognition_evidence.matched_fields.length > 0 && (
                        <div>
                          <span className="font-semibold">Matched Fields: </span>
                          {device.recognition_evidence.matched_fields.join(', ')}
                        </div>
                      )}
                      {device.recognition_evidence.confidence_breakdown && (
                        <div>
                          <span className="font-semibold">Confidence Breakdown: </span>
                          OUI: {device.recognition_evidence.confidence_breakdown.oui}%,
                          DHCP: {device.recognition_evidence.confidence_breakdown.dhcp}%,
                          Combined: {device.recognition_evidence.confidence_breakdown.combined}%
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

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
