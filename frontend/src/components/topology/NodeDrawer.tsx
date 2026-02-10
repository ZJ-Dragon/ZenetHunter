import React, { useState, useEffect } from 'react';
import { X, Monitor, Smartphone, Router, Shield, Activity, Clock, Hash, CheckCircle, AlertCircle, ChevronDown, ChevronUp, Eye, Pencil, Check, XCircle, UserCheck, FileJson, Download, MoreHorizontal } from 'lucide-react';
import { TopologyNode } from '../../types/topology';
import { Device, DeviceStatus } from '../../types/device';
import { deviceService } from '../../lib/services/device';
import { observationService } from '../../lib/services/observations';
import { ProbeObservation, KeywordHit } from '../../types/observation';
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
  const [showKeywordIntel, setShowKeywordIntel] = useState(false);
  const [showObservations, setShowObservations] = useState(false);
  const [observations, setObservations] = useState<ProbeObservation[]>([]);
  const [isLoadingObservations, setIsLoadingObservations] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [showAutoIdentity, setShowAutoIdentity] = useState(false);

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
    setShowObservations(false);
    setShowAutoIdentity(false);
    setObservations([]);
    fetchObservations();
  }, [initialDevice]);

  const fetchObservations = async () => {
    setIsLoadingObservations(true);
    try {
      const data = await observationService.listByDevice(initialDevice.mac, 10);
      setObservations(data);
    } catch (error) {
      console.error('Failed to load observations', error);
    } finally {
      setIsLoadingObservations(false);
    }
  };

  const manualName = device.manual_profile?.manual_name ?? device.name_manual;
  const manualVendor = device.manual_profile?.manual_vendor ?? device.vendor_manual;
  const autoName = device.name_auto || device.name || device.alias || device.model || device.model_guess || 'Unknown Device';
  const autoVendor = device.vendor_auto || device.vendor || device.vendor_guess || 'Unknown Vendor';
  const displayName = device.display_name || manualName || autoName || 'Unknown Device';
  const displayVendor = device.display_vendor || manualVendor || autoVendor || 'Unknown Vendor';
  const hasManualOverride = Boolean(manualName || manualVendor || device.manual_profile_id);

  // Start editing name
  const startEditingName = () => {
    setNameValue(manualName || device.name || device.alias || '');
    setEditingName(true);
  };

  // Start editing vendor
  const startEditingVendor = () => {
    setVendorValue(manualVendor || device.vendor || '');
    setEditingVendor(true);
  };

  // Save manual label
  const saveManualLabel = async (field: 'name' | 'vendor') => {
    setIsSaving(true);
    const toastId = toast.loading('Saving...');

    try {
      const response = await deviceService.updateManualLabel(device.mac, {
        name_manual: field === 'name' ? (nameValue.trim() || null) : (manualName ?? null),
        vendor_manual: field === 'vendor' ? (vendorValue.trim() || null) : (manualVendor ?? null),
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

  const latestObservation = observations[0];
  const evidenceHits = (device.recognition_evidence?.keyword_hits || []) as KeywordHit[];
  const observationHits = observations.flatMap((obs) => (obs.keyword_hits || [])) as KeywordHit[];
  const keywordHits = evidenceHits.length > 0 ? evidenceHits : observationHits;
  const sortedHits = keywordHits
    .slice()
    .sort((a, b) => (b.priority || 0) - (a.priority || 0));
  const topHit = sortedHits[0];
  const dictionaryDelta = device.recognition_evidence?.confidence_breakdown?.dictionary_delta
    ?? sortedHits.reduce((acc, hit) => acc + (hit.confidence_delta ?? 0), 0);
  const dictionaryInfer: Partial<Record<'vendor' | 'product' | 'os' | 'category', string>> | undefined =
    device.recognition_evidence?.dictionary_infer || topHit?.infer;

  const formatHitInfer = (hit?: KeywordHit) => {
    if (!hit) return '';
    if (hit.infer_summary) return hit.infer_summary;
    const parts: string[] = [];
    if (hit.infer?.vendor) parts.push(hit.infer.vendor);
    if (hit.infer?.product) parts.push(hit.infer.product);
    if (hit.infer?.os) parts.push(hit.infer.os);
    if (hit.infer?.category) parts.push(`[${hit.infer.category}]`);
    return parts.join(' ').trim();
  };

  const copyObservationJson = async (obs: ProbeObservation) => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(obs, null, 2));
      toast.success('Observation copied');
    } catch (err) {
      console.error(err);
      toast.error('Copy failed');
    }
  };

  const exportNdjson = async () => {
    setIsExporting(true);
    try {
      const ndjson = await observationService.exportDeviceNdjson(device.mac, 100);
      await navigator.clipboard.writeText(ndjson);
      toast.success('NDJSON copied');
    } catch (err) {
      console.error(err);
      toast.error('Export failed');
    } finally {
      setIsExporting(false);
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
                      {displayName}
                    </h3>
                    <button
                      onClick={startEditingName}
                      className="p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-gray-100 dark:hover:bg-gray-800 transition-opacity"
                      style={{ color: 'var(--winui-text-tertiary)' }}
                      title="Edit device name"
                    >
                      <Pencil className="h-4 w-4" />
                    </button>
                    {manualName && (
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
                      {displayVendor}
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
                    {manualVendor && (
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

              <div className="mb-2">
                <button
                  onClick={() => setShowAutoIdentity((prev) => !prev)}
                  className="text-xs inline-flex items-center gap-2 px-2 py-1 rounded"
                  style={{ backgroundColor: 'var(--winui-bg-tertiary)', color: 'var(--winui-text-secondary)' }}
                >
                  <ChevronDown className={`h-3 w-3 transition-transform ${showAutoIdentity ? 'rotate-180' : ''}`} />
                  {showAutoIdentity ? 'Hide auto-detected identity' : 'Show auto-detected identity'}
                </button>
                {showAutoIdentity && (
                  <div className="mt-2 space-y-1 text-xs rounded border p-3" style={{ borderColor: 'var(--winui-border-subtle)', backgroundColor: 'var(--winui-surface)' }}>
                    <div>
                      <span className="font-semibold" style={{ color: 'var(--winui-text-primary)' }}>Name (auto): </span>
                      <span style={{ color: 'var(--winui-text-secondary)' }}>{autoName}</span>
                    </div>
                    <div>
                      <span className="font-semibold" style={{ color: 'var(--winui-text-primary)' }}>Vendor (auto): </span>
                      <span style={{ color: 'var(--winui-text-secondary)' }}>{autoVendor}</span>
                    </div>
                    {(device.model || device.model_guess) && (
                      <div style={{ color: 'var(--winui-text-secondary)' }}>
                        Model: {device.model || device.model_guess}
                      </div>
                    )}
                    {manualName && (
                      <div className="text-xxs uppercase tracking-wide" style={{ color: 'var(--winui-text-tertiary)' }}>
                        Manual profile linked {device.manual_profile_id ? `#${device.manual_profile_id}` : ''}
                      </div>
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

              {device.name_auto && (
                <div>
                  <dt className="text-xs mb-1" style={{ color: 'var(--winui-text-secondary)' }}>
                    Name (auto)
                  </dt>
                  <dd className="text-sm font-semibold" style={{ color: 'var(--winui-text-primary)' }}>
                    {device.name_auto}
                  </dd>
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
                          {device.recognition_evidence.confidence_breakdown.active_probe !== undefined && (
                            <>Active Probe: {device.recognition_evidence.confidence_breakdown.active_probe}% · </>
                          )}
                          {device.recognition_evidence.confidence_breakdown.oui !== undefined && (
                            <>OUI: {device.recognition_evidence.confidence_breakdown.oui}% · </>
                          )}
                          {device.recognition_evidence.confidence_breakdown.dhcp !== undefined && (
                            <>DHCP: {device.recognition_evidence.confidence_breakdown.dhcp}% · </>
                          )}
                          {device.recognition_evidence.confidence_breakdown.external_vendor !== undefined && (
                            <>External Vendor: {device.recognition_evidence.confidence_breakdown.external_vendor}% · </>
                          )}
                          {device.recognition_evidence.confidence_breakdown.external_device !== undefined && (
                            <>External Device: {device.recognition_evidence.confidence_breakdown.external_device}% · </>
                          )}
                          {device.recognition_evidence.confidence_breakdown.dictionary_delta !== undefined && (
                            <>Dictionary Δ {device.recognition_evidence.confidence_breakdown.dictionary_delta >= 0 ? '+' : ''}{device.recognition_evidence.confidence_breakdown.dictionary_delta} · </>
                          )}
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

        {/* Keyword Intelligence */}
        <div className="card-winui p-4">
          <div className="flex items-center justify-between mb-2">
            <div>
              <h4 className="text-sm font-semibold uppercase tracking-wider" style={{ color: 'var(--winui-text-secondary)' }}>
                Keyword Intelligence
              </h4>
              <p className="text-xs mt-1" style={{ color: 'var(--winui-text-tertiary)' }}>
                {keywordHits.length} hits
                {topHit && formatHitInfer(topHit) && <> • {formatHitInfer(topHit)}</>}
                {keywordHits.length > 0 && (
                  <> • Δ {dictionaryDelta >= 0 ? '+' : ''}{dictionaryDelta}</>
                )}
              </p>
            </div>
            <button
              onClick={() => setShowKeywordIntel((prev) => !prev)}
              className="btn-winui-secondary inline-flex items-center gap-1"
              disabled={keywordHits.length === 0}
            >
              <MoreHorizontal className="h-4 w-4" />
              {showKeywordIntel ? 'Collapse' : 'Expand'}
            </button>
          </div>
          {showKeywordIntel && (
            <div className="space-y-2">
              {keywordHits.length === 0 && (
                <p className="text-xs" style={{ color: 'var(--winui-text-secondary)' }}>No keyword hits yet.</p>
              )}
              {keywordHits.length > 0 && (
                <div className="p-3 rounded border" style={{ borderColor: 'var(--winui-border-subtle)', background: 'linear-gradient(135deg, rgba(0,120,212,0.08), rgba(0,120,212,0.02))' }}>
                  <div className="flex items-center justify-between text-xs mb-1" style={{ color: 'var(--winui-text-primary)' }}>
                    <span className="font-semibold">Dictionary applied</span>
                    <span className="font-mono">
                      Δ {dictionaryDelta >= 0 ? '+' : ''}{dictionaryDelta}{device.recognition_confidence !== null ? ` → ${device.recognition_confidence}%` : ''}
                    </span>
                  </div>
                  {formatHitInfer(topHit) && (
                    <div className="text-xs" style={{ color: 'var(--winui-text-secondary)' }}>
                      Inference: {formatHitInfer(topHit)}
                    </div>
                  )}
                  {dictionaryInfer && (dictionaryInfer.vendor || dictionaryInfer.product || dictionaryInfer.os || dictionaryInfer.category) && (
                    <div className="text-xxs mt-1 uppercase tracking-wide" style={{ color: 'var(--winui-text-tertiary)' }}>
                      Vendor: {dictionaryInfer.vendor || '—'} · Product: {dictionaryInfer.product || '—'} · OS: {dictionaryInfer.os || '—'} · Category: {dictionaryInfer.category || '—'}
                    </div>
                  )}
                </div>
              )}
              {keywordHits.length > 0 && keywordHits
                .slice()
                .sort((a, b) => (b.priority || 0) - (a.priority || 0))
                .map((hit) => (
                  <div key={hit.rule_id} className="p-3 rounded border" style={{ borderColor: 'var(--winui-border-subtle)', backgroundColor: 'var(--winui-bg-tertiary)' }}>
                    <div className="flex items-center justify-between">
                      <div className="text-sm font-semibold" style={{ color: 'var(--winui-text-primary)' }}>
                        {hit.rule_id}
                      </div>
                      <span className="text-xxs px-2 py-1 rounded-full" style={{ backgroundColor: 'rgba(0,120,212,0.1)', color: 'var(--winui-accent)' }}>
                        Δ {hit.confidence_delta ?? 0}
                      </span>
                    </div>
                    <div className="mt-1 text-xs" style={{ color: 'var(--winui-text-secondary)' }}>
                      Matched: <span className="font-mono">{hit.matched_token}</span>
                      {hit.priority !== undefined && (
                        <span className="ml-2 text-xxs px-1.5 py-0.5 rounded-full" style={{ backgroundColor: 'rgba(0,0,0,0.05)', color: 'var(--winui-text-tertiary)' }}>
                          Priority {hit.priority}
                        </span>
                      )}
                    </div>
                    {(hit.infer?.vendor || hit.infer?.product || hit.infer?.os || hit.infer?.category || hit.infer_summary) && (
                      <div className="mt-1 text-xs" style={{ color: 'var(--winui-text-primary)' }}>
                        {hit.infer_summary || (
                          <>
                            {hit.infer?.vendor && <span className="mr-2">Vendor: {hit.infer.vendor}</span>}
                            {hit.infer?.product && <span className="mr-2">Product: {hit.infer.product}</span>}
                            {hit.infer?.os && <span className="mr-2">OS: {hit.infer.os}</span>}
                            {hit.infer?.category && <span className="mr-2">Category: {hit.infer.category}</span>}
                          </>
                        )}
                        {hit.infer_summary && <span className="mr-2">{hit.infer_summary}</span>}
                      </div>
                    )}
                    {hit.notes && (
                      <p className="mt-1 text-xs" style={{ color: 'var(--winui-text-tertiary)' }}>
                        {hit.notes}
                      </p>
                    )}
                  </div>
                ))}
            </div>
          )}
        </div>

        {/* Probe Observations */}
        <div className="card-winui p-4">
          <div className="flex items-center justify-between mb-2">
            <div>
              <h4 className="text-sm font-semibold uppercase tracking-wider" style={{ color: 'var(--winui-text-secondary)' }}>
                Probe Details / Observations
              </h4>
              {latestObservation && !showObservations && (
                <p className="text-xs mt-1" style={{ color: 'var(--winui-text-tertiary)' }}>
                  {latestObservation.protocol} • {new Date(latestObservation.timestamp).toLocaleString()} • {latestObservation.keywords.length} keywords
                </p>
              )}
            </div>
            <button
              onClick={() => {
                if (!showObservations && observations.length === 0) {
                  fetchObservations();
                }
                setShowObservations((prev) => !prev);
              }}
              className="btn-winui-secondary inline-flex items-center gap-1"
            >
              <MoreHorizontal className="h-4 w-4" />
              {showObservations ? 'Collapse' : 'Expand'}
            </button>
          </div>

          {showObservations && (
            <div className="space-y-3">
              {isLoadingObservations && (
                <p className="text-xs" style={{ color: 'var(--winui-text-secondary)' }}>Loading observations...</p>
              )}
              {!isLoadingObservations && observations.length === 0 && (
                <p className="text-xs" style={{ color: 'var(--winui-text-secondary)' }}>No observations yet.</p>
              )}
              {!isLoadingObservations && observations.map((obs) => (
                <div key={obs.id} className="p-3 rounded-lg border" style={{ borderColor: 'var(--winui-border-subtle)', backgroundColor: 'var(--winui-bg-tertiary)' }}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold px-2 py-1 rounded-full" style={{ backgroundColor: 'rgba(0,120,212,0.1)', color: 'var(--winui-accent)' }}>
                        {obs.protocol}
                      </span>
                      <span className="text-xs" style={{ color: 'var(--winui-text-secondary)' }}>
                        {new Date(obs.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => copyObservationJson(obs)}
                        className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800"
                        title="Copy observation JSON"
                      >
                        <FileJson className="h-4 w-4" />
                      </button>
                      <span className="text-xs" style={{ color: 'var(--winui-text-tertiary)' }}>
                        {obs.keywords.length} keywords
                      </span>
                    </div>
                  </div>
                  {obs.raw_summary && (
                    <p className="text-sm mt-2" style={{ color: 'var(--winui-text-primary)' }}>
                      {obs.raw_summary}
                    </p>
                  )}
                  <div className="mt-2 flex flex-wrap gap-2">
                    {obs.keywords.slice(0, 12).map((kw) => (
                      <span key={kw} className="text-xxs px-2 py-1 rounded-full" style={{ backgroundColor: 'rgba(0,0,0,0.05)', color: 'var(--winui-text-secondary)' }}>
                        {kw}
                      </span>
                    ))}
                  </div>
                  <pre className="mt-2 text-xs overflow-x-auto p-2 rounded" style={{ backgroundColor: 'var(--winui-surface)', color: 'var(--winui-text-primary)', border: '1px solid var(--winui-border-subtle)' }}>
                    {JSON.stringify(obs.key_fields, null, 2)}
                  </pre>
                </div>
              ))}
              <div className="flex gap-2 justify-end">
                <button
                  onClick={exportNdjson}
                  disabled={isExporting}
                  className="btn-winui-secondary inline-flex items-center gap-2"
                >
                  <Download className="h-4 w-4" />
                  Export NDJSON
                </button>
              </div>
            </div>
          )}
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
