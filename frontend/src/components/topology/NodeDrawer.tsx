import React, { useState, useEffect } from 'react';
import { X, Monitor, Smartphone, Router, Shield, Activity, Clock, Hash, CheckCircle, AlertCircle, ChevronDown, ChevronUp, Eye, Pencil, Check, XCircle, UserCheck } from 'lucide-react';
import { TopologyNode } from '../../types/topology';
import { Device, DeviceStatus } from '../../types/device';
import { deviceService } from '../../lib/services/device';
import toast from 'react-hot-toast';

interface NodeDrawerProps {
  node: TopologyNode | null;
  onClose: () => void;
  onDeviceUpdate?: (device: Device) => void;
}

export const NodeDrawer: React.FC<NodeDrawerProps> = ({ node, onClose, onDeviceUpdate }) => {
  if (!node) return null;

  const { data: initialDevice } = node;
  const [device, setDevice] = useState<Device>(initialDevice);
  const [showEvidence, setShowEvidence] = useState(false);
  
  // Editable state
  const [editingName, setEditingName] = useState(false);
  const [editingVendor, setEditingVendor] = useState(false);
  const [nameValue, setNameValue] = useState('');
  const [vendorValue, setVendorValue] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  // Update device when node changes
  useEffect(() => {
    setDevice(initialDevice);
    setEditingName(false);
    setEditingVendor(false);
  }, [initialDevice]);

  // Get display name with priority: manual > name > alias > model_guess
  const getDisplayName = () => {
    return device.name_manual || device.name || device.alias || device.model || device.model_guess || 'Unknown Device';
  };

  // Get display vendor with priority: manual > vendor > vendor_guess
  const getDisplayVendor = () => {
    return device.vendor_manual || device.vendor || device.vendor_guess || 'Unknown Vendor';
  };

  // Check if has manual override
  const hasManualOverride = Boolean(device.name_manual || device.vendor_manual);

  // Start editing name
  const startEditingName = () => {
    setNameValue(device.name_manual || device.name || device.alias || '');
    setEditingName(true);
  };

  // Start editing vendor
  const startEditingVendor = () => {
    setVendorValue(device.vendor_manual || device.vendor || '');
    setEditingVendor(true);
  };

  // Save manual label
  const saveManualLabel = async (field: 'name' | 'vendor') => {
    setIsSaving(true);
    const toastId = toast.loading('Saving...');

    try {
      const response = await deviceService.updateManualLabel(device.mac, {
        name_manual: field === 'name' ? (nameValue.trim() || null) : device.name_manual,
        vendor_manual: field === 'vendor' ? (vendorValue.trim() || null) : device.vendor_manual,
      });

      setDevice(response.device);
      onDeviceUpdate?.(response.device);
      
      toast.success('Label saved successfully', { id: toastId });
      
      if (field === 'name') {
        setEditingName(false);
      } else {
        setEditingVendor(false);
      }
    } catch (error) {
      console.error('Failed to save label:', error);
      toast.error('Failed to save label', { id: toastId });
    } finally {
      setIsSaving(false);
    }
  };

  // Cancel editing
  const cancelEditing = (field: 'name' | 'vendor') => {
    if (field === 'name') {
      setEditingName(false);
      setNameValue('');
    } else {
      setEditingVendor(false);
      setVendorValue('');
    }
  };

  // Clear manual label
  const clearManualLabel = async () => {
    if (!hasManualOverride) return;
    
    const confirmed = window.confirm('Clear manual labels and revert to auto-detected values?');
    if (!confirmed) return;

    setIsSaving(true);
    const toastId = toast.loading('Clearing labels...');

    try {
      const updatedDevice = await deviceService.clearManualLabel(device.mac);
      setDevice(updatedDevice);
      onDeviceUpdate?.(updatedDevice);
      toast.success('Manual labels cleared', { id: toastId });
    } catch (error) {
      console.error('Failed to clear labels:', error);
      toast.error('Failed to clear labels', { id: toastId });
    } finally {
      setIsSaving(false);
    }
  };

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
        <div className="card-winui p-4">
          <div className="flex items-start space-x-4">
            <div className="flex-shrink-0">
              {device.type === 'router' ? (
                <Router className="h-10 w-10" style={{ color: '#9a4dff' }} />
              ) : device.type === 'mobile' ? (
                <Smartphone className="h-10 w-10" style={{ color: '#107c10' }} />
              ) : (
                <Monitor className="h-10 w-10" style={{ color: 'var(--winui-accent)' }} />
              )}
            </div>
            <div className="flex-1 min-w-0">
              {/* Device Name - Editable */}
              <div className="mb-2">
                {editingName ? (
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      value={nameValue}
                      onChange={(e) => setNameValue(e.target.value)}
                      className="flex-1 px-2 py-1 text-lg font-semibold rounded border"
                      style={{
                        backgroundColor: 'var(--winui-surface)',
                        borderColor: 'var(--winui-accent)',
                        color: 'var(--winui-text-primary)',
                        outline: 'none',
                      }}
                      placeholder="Enter device name..."
                      autoFocus
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') saveManualLabel('name');
                        if (e.key === 'Escape') cancelEditing('name');
                      }}
                    />
                    <button
                      onClick={() => saveManualLabel('name')}
                      disabled={isSaving}
                      className="p-1 rounded hover:bg-green-100 dark:hover:bg-green-900"
                      style={{ color: '#107c10' }}
                    >
                      <Check className="h-5 w-5" />
                    </button>
                    <button
                      onClick={() => cancelEditing('name')}
                      disabled={isSaving}
                      className="p-1 rounded hover:bg-red-100 dark:hover:bg-red-900"
                      style={{ color: '#d13438' }}
                    >
                      <XCircle className="h-5 w-5" />
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 group">
                    <h3 className="text-lg font-semibold truncate" style={{ color: 'var(--winui-text-primary)' }}>
                      {getDisplayName()}
                    </h3>
                    <button
                      onClick={startEditingName}
                      className="p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-gray-100 dark:hover:bg-gray-800 transition-opacity"
                      style={{ color: 'var(--winui-text-tertiary)' }}
                      title="Edit device name"
                    >
                      <Pencil className="h-4 w-4" />
                    </button>
                    {device.name_manual && (
                      <span
                        className="flex items-center gap-1 px-2 py-0.5 text-xs rounded"
                        style={{ backgroundColor: 'rgba(16, 124, 16, 0.1)', color: '#107c10' }}
                        title={`Manually set by ${device.manual_override_by || 'admin'}`}
                      >
                        <UserCheck className="h-3 w-3" />
                        Manual
                      </span>
                    )}
                  </div>
                )}
              </div>

              {/* Vendor - Editable */}
              <div className="mb-2">
                {editingVendor ? (
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      value={vendorValue}
                      onChange={(e) => setVendorValue(e.target.value)}
                      className="flex-1 px-2 py-1 text-sm rounded border"
                      style={{
                        backgroundColor: 'var(--winui-surface)',
                        borderColor: 'var(--winui-accent)',
                        color: 'var(--winui-text-secondary)',
                        outline: 'none',
                      }}
                      placeholder="Enter vendor name..."
                      autoFocus
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') saveManualLabel('vendor');
                        if (e.key === 'Escape') cancelEditing('vendor');
                      }}
                    />
                    <button
                      onClick={() => saveManualLabel('vendor')}
                      disabled={isSaving}
                      className="p-1 rounded hover:bg-green-100 dark:hover:bg-green-900"
                      style={{ color: '#107c10' }}
                    >
                      <Check className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => cancelEditing('vendor')}
                      disabled={isSaving}
                      className="p-1 rounded hover:bg-red-100 dark:hover:bg-red-900"
                      style={{ color: '#d13438' }}
                    >
                      <XCircle className="h-4 w-4" />
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 group">
                    <p className="text-sm truncate" style={{ color: 'var(--winui-text-secondary)' }}>
                      {getDisplayVendor()}
                      {(device.model || device.model_guess) && (
                        <span className="ml-2" style={{ color: 'var(--winui-text-tertiary)' }}>
                          • {device.model || device.model_guess}
                        </span>
                      )}
                    </p>
                    <button
                      onClick={startEditingVendor}
                      className="p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-gray-100 dark:hover:bg-gray-800 transition-opacity"
                      style={{ color: 'var(--winui-text-tertiary)' }}
                      title="Edit vendor"
                    >
                      <Pencil className="h-3 w-3" />
                    </button>
                    {device.vendor_manual && (
                      <span
                        className="flex items-center gap-1 px-2 py-0.5 text-xs rounded"
                        style={{ backgroundColor: 'rgba(16, 124, 16, 0.1)', color: '#107c10' }}
                        title={`Manually set by ${device.manual_override_by || 'admin'}`}
                      >
                        <UserCheck className="h-3 w-3" />
                      </span>
                    )}
                  </div>
                )}
              </div>

              {/* Status badges */}
              <div className="flex items-center gap-2 flex-wrap">
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

          {/* Clear manual labels button */}
          {hasManualOverride && (
            <div className="mt-3 pt-3 border-t" style={{ borderColor: 'var(--winui-border-subtle)' }}>
              <button
                onClick={clearManualLabel}
                disabled={isSaving}
                className="text-xs flex items-center gap-1 px-2 py-1 rounded transition-colors"
                style={{ color: 'var(--winui-text-tertiary)' }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = 'rgba(209, 52, 56, 0.1)';
                  e.currentTarget.style.color = '#d13438';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                  e.currentTarget.style.color = 'var(--winui-text-tertiary)';
                }}
              >
                <XCircle className="h-3 w-3" />
                Clear manual labels
              </button>
            </div>
          )}
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

        {/* Recognition Info - Collapsible auto-detection results */}
        {(device.vendor || device.vendor_guess || device.model || device.model_guess || device.recognition_evidence) && (
          <div>
            <h4 className="text-sm font-semibold uppercase tracking-wider mb-3" style={{ color: 'var(--winui-text-secondary)' }}>
              Auto Detection Results
            </h4>
            <div className="card-winui p-4 space-y-3">
              {/* Show auto-detected values as secondary info when manual override exists */}
              {hasManualOverride && (
                <div className="text-xs mb-2 px-2 py-1 rounded" style={{ backgroundColor: 'rgba(0, 120, 212, 0.1)', color: 'var(--winui-accent)' }}>
                  Manual labels are active. Auto-detected values shown below for reference.
                </div>
              )}
              
              {(device.vendor || device.vendor_guess) && (
                <div>
                  <dt className="text-xs mb-1" style={{ color: 'var(--winui-text-secondary)' }}>
                    {device.vendor ? 'Vendor (Identified)' : 'Vendor (OUI Guess)'}
                  </dt>
                  <dd className="text-sm font-semibold" style={{ color: 'var(--winui-text-primary)' }}>
                    {device.vendor || device.vendor_guess}
                  </dd>
                </div>
              )}
              {(device.model || device.model_guess) && (
                <div>
                  <dt className="text-xs mb-1" style={{ color: 'var(--winui-text-secondary)' }}>
                    {device.model ? 'Model (Identified)' : 'Model (Guess)'}
                  </dt>
                  <dd className="text-sm font-semibold" style={{ color: 'var(--winui-text-primary)' }}>
                    {device.model || device.model_guess}
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
            {device.manual_override_at && (
              <div className="flex items-center">
                <UserCheck className="h-5 w-5 mr-3" style={{ color: 'var(--winui-text-tertiary)' }} />
                <div>
                  <dt className="text-xs" style={{ color: 'var(--winui-text-secondary)' }}>Manual Override</dt>
                  <dd className="text-sm" style={{ color: 'var(--winui-text-primary)' }}>
                    {new Date(device.manual_override_at).toLocaleString()}
                    {device.manual_override_by && (
                      <span className="text-xs ml-1" style={{ color: 'var(--winui-text-tertiary)' }}>
                        by {device.manual_override_by}
                      </span>
                    )}
                  </dd>
                </div>
              </div>
            )}
          </dl>
        </div>
      </div>

      {/* Footer - Removed attack controls as they're now in Interference page */}
      <div
        className="border-t p-4 text-center text-xs"
        style={{
          borderColor: 'var(--winui-border-subtle)',
          backgroundColor: 'var(--winui-bg-tertiary)',
          color: 'var(--winui-text-tertiary)',
        }}
      >
        Manage attacks from the Interference page
      </div>
    </div>
  );
};
