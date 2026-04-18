import React, { useCallback, useEffect, useState } from 'react';
import {
  Check,
  ChevronDown,
  ChevronUp,
  Download,
  Eye,
  FileJson,
  Network,
  Pencil,
  Shield,
  X,
  XCircle,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { useTranslation } from 'react-i18next';
import { observationService } from '../../lib/services/observations';
import { deviceService } from '../../lib/services/device';
import { Device } from '../../types/device';
import { KeywordHit, ProbeObservation } from '../../types/observation';
import { TopologyNode } from '../../types/topology';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { DeviceAvatar } from '../ui/DeviceAvatar';
import { DeviceStatusBadge } from '../ui/DeviceStatusBadge';
import { EmptyState } from '../ui/EmptyState';
import { Surface } from '../ui/Surface';

interface NodeDrawerProps {
  node: TopologyNode;
  onClose: () => void;
  onDeviceUpdate?: (device: Device) => void;
}

const DetailCard: React.FC<{
  label: string;
  value: React.ReactNode;
}> = ({ label, value }) => (
  <Surface className="zh-detail-card" tone="subtle">
    <p className="zh-detail-card__label">{label}</p>
    <div className="zh-detail-card__value text-sm">{value}</div>
  </Surface>
);

const formatHitInfer = (hit?: KeywordHit) => {
  if (!hit) {
    return '';
  }
  if (hit.infer_summary) {
    return hit.infer_summary;
  }
  const parts: string[] = [];
  if (hit.infer?.vendor) parts.push(hit.infer.vendor);
  if (hit.infer?.product) parts.push(hit.infer.product);
  if (hit.infer?.os) parts.push(hit.infer.os);
  if (hit.infer?.category) parts.push(`[${hit.infer.category}]`);
  return parts.join(' ').trim();
};

export const NodeDrawer: React.FC<NodeDrawerProps> = ({
  node,
  onClose,
  onDeviceUpdate,
}) => {
  const { t } = useTranslation();
  const { data: initialDevice } = node;
  const [device, setDevice] = useState<Device>(initialDevice);
  const [showEvidence, setShowEvidence] = useState(false);
  const [showKeywordIntel, setShowKeywordIntel] = useState(false);
  const [showObservations, setShowObservations] = useState(false);
  const [observations, setObservations] = useState<ProbeObservation[]>([]);
  const [isLoadingObservations, setIsLoadingObservations] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [showAutoIdentity, setShowAutoIdentity] = useState(false);
  const [editingName, setEditingName] = useState(false);
  const [editingVendor, setEditingVendor] = useState(false);
  const [nameValue, setNameValue] = useState('');
  const [vendorValue, setVendorValue] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  const fetchObservations = useCallback(async () => {
    setIsLoadingObservations(true);
    try {
      const data = await observationService.listByDevice(initialDevice.mac, 10);
      setObservations(data);
    } catch (error) {
      console.error('Failed to load observations', error);
    } finally {
      setIsLoadingObservations(false);
    }
  }, [initialDevice.mac]);

  useEffect(() => {
    setDevice(initialDevice);
    setEditingName(false);
    setEditingVendor(false);
    setShowObservations(false);
    setShowAutoIdentity(false);
    setObservations([]);
    fetchObservations();
  }, [fetchObservations, initialDevice]);

  const manualName = device.manual_profile?.manual_name ?? device.name_manual;
  const manualVendor = device.manual_profile?.manual_vendor ?? device.vendor_manual;
  const autoName =
    device.name_auto ||
    device.name ||
    device.alias ||
    device.model ||
    device.model_guess ||
    t('topologyDrawer.unknownDevice');
  const autoVendor =
    device.vendor_auto ||
    device.vendor ||
    device.vendor_guess ||
    t('topologyDrawer.unknownVendor');
  const displayName = device.display_name || manualName || autoName;
  const displayVendor = device.display_vendor || manualVendor || autoVendor;
  const hasManualOverride = Boolean(
    manualName || manualVendor || device.manual_profile_id
  );

  const latestObservation = observations[0];
  const evidenceHits = (device.recognition_evidence?.keyword_hits || []) as KeywordHit[];
  const observationHits = observations.flatMap(
    (observation) => (observation.keyword_hits || []) as KeywordHit[]
  );
  const keywordHits = evidenceHits.length > 0 ? evidenceHits : observationHits;
  const sortedHits = [...keywordHits].sort(
    (left, right) => (right.priority || 0) - (left.priority || 0)
  );
  const topHit = sortedHits[0];
  const dictionaryDelta =
    device.recognition_evidence?.confidence_breakdown?.dictionary_delta ??
    sortedHits.reduce((sum, hit) => sum + (hit.confidence_delta ?? 0), 0);

  const startEditingName = () => {
    setNameValue(manualName || device.name || device.alias || '');
    setEditingName(true);
  };

  const startEditingVendor = () => {
    setVendorValue(manualVendor || device.vendor || '');
    setEditingVendor(true);
  };

  const cancelEditing = (field: 'name' | 'vendor') => {
    if (field === 'name') {
      setEditingName(false);
      setNameValue('');
    } else {
      setEditingVendor(false);
      setVendorValue('');
    }
  };

  const saveManualLabel = async (field: 'name' | 'vendor') => {
    setIsSaving(true);
    const toastId = toast.loading(t('topologyDrawer.saving'));

    try {
      const response = await deviceService.updateManualLabel(device.mac, {
        name_manual: field === 'name' ? nameValue.trim() || null : manualName ?? null,
        vendor_manual:
          field === 'vendor' ? vendorValue.trim() || null : manualVendor ?? null,
      });

      setDevice(response.device);
      onDeviceUpdate?.(response.device);
      toast.success(t('topologyDrawer.labelSaved'), { id: toastId });

      if (field === 'name') {
        setEditingName(false);
      } else {
        setEditingVendor(false);
      }
    } catch (error) {
      console.error('Failed to save label:', error);
      toast.error(t('topologyDrawer.labelSaveFailed'), { id: toastId });
    } finally {
      setIsSaving(false);
    }
  };

  const clearManualLabel = async () => {
    if (!hasManualOverride) {
      return;
    }

    const confirmed = window.confirm(t('topologyDrawer.clearManualConfirm'));
    if (!confirmed) {
      return;
    }

    setIsSaving(true);
    const toastId = toast.loading(t('topologyDrawer.clearing'));

    try {
      const updatedDevice = await deviceService.clearManualLabel(device.mac);
      setDevice(updatedDevice);
      onDeviceUpdate?.(updatedDevice);
      toast.success(t('topologyDrawer.cleared'), { id: toastId });
    } catch (error) {
      console.error('Failed to clear labels:', error);
      toast.error(t('topologyDrawer.clearFailed'), { id: toastId });
    } finally {
      setIsSaving(false);
    }
  };

  const copyObservationJson = async (observation: ProbeObservation) => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(observation, null, 2));
      toast.success(t('topologyDrawer.observationCopied'));
    } catch (error) {
      console.error(error);
      toast.error(t('topologyDrawer.copyFailed'));
    }
  };

  const exportNdjson = async () => {
    setIsExporting(true);
    try {
      const ndjson = await observationService.exportDeviceNdjson(device.mac, 100);
      await navigator.clipboard.writeText(ndjson);
      toast.success(t('topologyDrawer.ndjsonCopied'));
    } catch (error) {
      console.error(error);
      toast.error(t('topologyDrawer.exportFailed'));
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="zh-drawer">
      <div
        className="flex items-start justify-between gap-4 px-6 py-5"
        style={{ borderBottom: '1px solid var(--border)' }}
      >
        <div className="flex items-start gap-4">
          <DeviceAvatar size="lg" status={device.status} type={device.type} />
          <div className="min-w-0">
            <p className="zh-kicker">{t('topologyDrawer.titleKicker')}</p>

            {editingName ? (
              <div className="mt-3 flex items-center gap-2">
                <input
                  autoFocus
                  className="zh-field"
                  onChange={(event) => setNameValue(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter') saveManualLabel('name');
                    if (event.key === 'Escape') cancelEditing('name');
                  }}
                  placeholder={t('topologyDrawer.namePlaceholder')}
                  type="text"
                  value={nameValue}
                />
                <Button
                  disabled={isSaving}
                  onClick={() => saveManualLabel('name')}
                  size="icon"
                  variant="secondary"
                >
                  <Check className="h-4 w-4" />
                </Button>
                <Button
                  disabled={isSaving}
                  onClick={() => cancelEditing('name')}
                  size="icon"
                  variant="ghost"
                >
                  <XCircle className="h-4 w-4" />
                </Button>
              </div>
            ) : (
              <div className="mt-3 flex items-center gap-2">
                <h2
                  className="truncate text-2xl font-semibold"
                  style={{ color: 'var(--text-primary)' }}
                >
                  {displayName}
                </h2>
                <Button onClick={startEditingName} size="icon" variant="ghost">
                  <Pencil className="h-4 w-4" />
                </Button>
                {manualName ? <Badge tone="success">{t('devices.manualTag')}</Badge> : null}
              </div>
            )}

            {editingVendor ? (
              <div className="mt-3 flex items-center gap-2">
                <input
                  autoFocus
                  className="zh-field"
                  onChange={(event) => setVendorValue(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter') saveManualLabel('vendor');
                    if (event.key === 'Escape') cancelEditing('vendor');
                  }}
                  placeholder={t('topologyDrawer.vendorPlaceholder')}
                  type="text"
                  value={vendorValue}
                />
                <Button
                  disabled={isSaving}
                  onClick={() => saveManualLabel('vendor')}
                  size="icon"
                  variant="secondary"
                >
                  <Check className="h-4 w-4" />
                </Button>
                <Button
                  disabled={isSaving}
                  onClick={() => cancelEditing('vendor')}
                  size="icon"
                  variant="ghost"
                >
                  <XCircle className="h-4 w-4" />
                </Button>
              </div>
            ) : (
              <div className="mt-3 flex items-center gap-2">
                <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                  {displayVendor}
                  {device.model || device.model_guess
                    ? ` • ${device.model || device.model_guess}`
                    : ''}
                </p>
                <Button onClick={startEditingVendor} size="icon" variant="ghost">
                  <Pencil className="h-4 w-4" />
                </Button>
              </div>
            )}

            <div className="mt-4 flex flex-wrap items-center gap-2">
              <DeviceStatusBadge status={device.status} />
              {device.recognition_confidence !== null &&
              device.recognition_confidence > 0 ? (
                <Badge
                  tone={
                    device.recognition_confidence >= 70
                      ? 'success'
                      : device.recognition_confidence >= 40
                        ? 'warning'
                        : 'neutral'
                  }
                >
                  {device.recognition_confidence}%
                </Badge>
              ) : null}
            </div>
          </div>
        </div>
        <Button aria-label={t('topologyDrawer.closeDrawer')} onClick={onClose} size="icon" variant="ghost">
          <X className="h-4 w-4" />
        </Button>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto p-5">
        <Surface className="p-5" tone="subtle">
          <div className="zh-toolbar zh-toolbar--spread">
            <div>
              <p className="zh-kicker">{t('topologyDrawer.identityKicker')}</p>
              <h3 className="mt-2 text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>
                {t('topologyDrawer.identityTitle')}
              </h3>
            </div>
            <Button
              onClick={() => setShowAutoIdentity((previous) => !previous)}
              size="sm"
              variant="secondary"
            >
              {showAutoIdentity
                ? t('topologyDrawer.hideAutoIdentity')
                : t('topologyDrawer.showAutoIdentity')}
              {showAutoIdentity ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </Button>
          </div>

          {showAutoIdentity ? (
            <div className="mt-4 space-y-3">
              <Surface className="p-4" tone="inset">
                <p className="zh-detail-card__label">{t('topologyDrawer.autoName')}</p>
                <p className="zh-detail-card__value text-sm">{autoName}</p>
              </Surface>
              <Surface className="p-4" tone="inset">
                <p className="zh-detail-card__label">{t('topologyDrawer.autoVendor')}</p>
                <p className="zh-detail-card__value text-sm">{autoVendor}</p>
              </Surface>
            </div>
          ) : null}

          {hasManualOverride ? (
            <div className="mt-4">
              <Button onClick={clearManualLabel} size="sm" variant="ghost">
                <XCircle className="h-4 w-4" />
                {t('topologyDrawer.clearManual')}
              </Button>
            </div>
          ) : null}
        </Surface>

        <Surface className="p-5" tone="raised">
          <p className="zh-kicker">{t('topologyDrawer.overviewKicker')}</p>
          <div className="mt-4 zh-detail-grid">
            <DetailCard
              label={t('topologyDrawer.ipAddress')}
              value={device.ip || t('topologyDrawer.unavailable')}
            />
            <DetailCard
              label={t('topologyDrawer.macAddress')}
              value={<span className="font-mono">{device.mac}</span>}
            />
            <DetailCard
              label={t('topologyDrawer.lastSeen')}
              value={new Date(device.last_seen).toLocaleString()}
            />
            <DetailCard label={t('topologyDrawer.attackStatus')} value={device.attack_status} />
            {device.manual_override_at ? (
              <DetailCard
                label={t('topologyDrawer.manualOverride')}
                value={
                  <>
                    {new Date(device.manual_override_at).toLocaleString()}
                    {device.manual_override_by ? (
                      <span style={{ color: 'var(--text-tertiary)' }}>
                        {' '}
                        {t('topologyDrawer.by')} {device.manual_override_by}
                      </span>
                    ) : null}
                  </>
                }
              />
            ) : null}
          </div>
        </Surface>

        {(device.vendor ||
          device.vendor_guess ||
          device.model ||
          device.model_guess ||
          device.recognition_evidence) ? (
          <Surface className="p-5" tone="raised">
            <div className="zh-toolbar zh-toolbar--spread">
              <div>
                <p className="zh-kicker">{t('topologyDrawer.detectionKicker')}</p>
                <h3
                  className="mt-2 text-xl font-semibold"
                  style={{ color: 'var(--text-primary)' }}
                >
                  {t('topologyDrawer.detectionTitle')}
                </h3>
              </div>
              {device.recognition_evidence ? (
                <Button
                  onClick={() => setShowEvidence((previous) => !previous)}
                  size="sm"
                  variant="ghost"
                >
                  <Eye className="h-4 w-4" />
                  {t('topologyDrawer.evidence')}
                  {showEvidence ? (
                    <ChevronUp className="h-4 w-4" />
                  ) : (
                    <ChevronDown className="h-4 w-4" />
                  )}
                </Button>
              ) : null}
            </div>
            <div className="mt-4 zh-detail-grid">
              {device.name_auto ? (
                <DetailCard label={t('topologyDrawer.name')} value={device.name_auto} />
              ) : null}
              {device.vendor || device.vendor_guess ? (
                <DetailCard
                  label={
                    device.vendor
                      ? t('topologyDrawer.vendor')
                      : t('topologyDrawer.vendorGuess')
                  }
                  value={device.vendor || device.vendor_guess}
                />
              ) : null}
              {device.model || device.model_guess ? (
                <DetailCard
                  label={
                    device.model
                      ? t('topologyDrawer.model')
                      : t('topologyDrawer.modelGuess')
                  }
                  value={device.model || device.model_guess}
                />
              ) : null}
            </div>
            {showEvidence && device.recognition_evidence ? (
              <Surface className="mt-4 p-4" tone="subtle">
                <div className="space-y-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
                  {device.recognition_evidence.sources?.length ? (
                    <p>
                      <strong style={{ color: 'var(--text-primary)' }}>
                        {t('topologyDrawer.sources')}:
                      </strong>{' '}
                      {device.recognition_evidence.sources.join(', ')}
                    </p>
                  ) : null}
                  {device.recognition_evidence.matched_fields?.length ? (
                    <p>
                      <strong style={{ color: 'var(--text-primary)' }}>
                        {t('topologyDrawer.matchedFields')}:
                      </strong>{' '}
                      {device.recognition_evidence.matched_fields.join(', ')}
                    </p>
                  ) : null}
                  {device.recognition_evidence.confidence_breakdown ? (
                    <p>
                      <strong style={{ color: 'var(--text-primary)' }}>
                        {t('topologyDrawer.confidenceBreakdown')}:
                      </strong>{' '}
                      {device.recognition_evidence.confidence_breakdown.active_probe !==
                      undefined
                        ? `${t('topologyDrawer.activeProbe')} ${device.recognition_evidence.confidence_breakdown.active_probe}% • `
                        : ''}
                      OUI {device.recognition_evidence.confidence_breakdown.oui}% • DHCP{' '}
                      {device.recognition_evidence.confidence_breakdown.dhcp}% • {t('topologyDrawer.combined')}{' '}
                      {device.recognition_evidence.confidence_breakdown.combined}%
                    </p>
                  ) : null}
                </div>
              </Surface>
            ) : null}
          </Surface>
        ) : null}

        <Surface className="p-5" tone="raised">
          <div className="zh-toolbar zh-toolbar--spread">
            <div>
              <p className="zh-kicker">{t('topologyDrawer.intelligenceKicker')}</p>
              <h3 className="mt-2 text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>
                {t('topologyDrawer.intelligenceTitle')}
              </h3>
            </div>
            <Button
              disabled={keywordHits.length === 0}
              onClick={() => setShowKeywordIntel((previous) => !previous)}
              size="sm"
              variant="secondary"
            >
              {showKeywordIntel ? t('common.collapse') : t('common.expand')}
            </Button>
          </div>

          {showKeywordIntel ? (
            <div className="mt-4 space-y-3">
              {keywordHits.length === 0 ? (
                <EmptyState
                  description={t('topologyDrawer.noKeywordDesc')}
                  icon={Shield}
                  title={t('topologyDrawer.noKeywordTitle')}
                />
              ) : (
                <>
                  <Surface className="p-4" tone="subtle">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge tone="accent">
                        {t('topologyDrawer.delta')} {dictionaryDelta >= 0 ? '+' : ''}
                        {dictionaryDelta}
                      </Badge>
                      {topHit ? (
                        <Badge tone="warning">{formatHitInfer(topHit) || topHit.rule_id}</Badge>
                      ) : null}
                    </div>
                  </Surface>
                  {sortedHits.map((hit) => (
                    <Surface className="p-4" key={hit.rule_id} tone="inset">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <p className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                          {hit.rule_id}
                        </p>
                        <Badge tone="accent">
                          {t('topologyDrawer.delta')} {hit.confidence_delta ?? 0}
                        </Badge>
                      </div>
                      <p className="mt-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
                        {t('topologyDrawer.matchedToken')}:{' '}
                        <span className="font-mono">{hit.matched_token}</span>
                      </p>
                      {formatHitInfer(hit) ? (
                        <p className="mt-2 text-sm" style={{ color: 'var(--text-primary)' }}>
                          {formatHitInfer(hit)}
                        </p>
                      ) : null}
                      {hit.notes ? (
                        <p className="mt-2 text-xs" style={{ color: 'var(--text-tertiary)' }}>
                          {hit.notes}
                        </p>
                      ) : null}
                    </Surface>
                  ))}
                </>
              )}
            </div>
          ) : (
            <p className="mt-4 text-sm" style={{ color: 'var(--text-secondary)' }}>
              {keywordHits.length
                ? topHit
                  ? t('topologyDrawer.hitsAvailableWithTop', {
                      count: keywordHits.length,
                      top: formatHitInfer(topHit) || topHit.rule_id,
                    })
                  : t('topologyDrawer.hitsAvailable', { count: keywordHits.length })
                : t('topologyDrawer.noHitsYet')}
            </p>
          )}
        </Surface>

        <Surface className="p-5" tone="raised">
          <div className="zh-toolbar zh-toolbar--spread">
            <div>
              <p className="zh-kicker">{t('topologyDrawer.observationsKicker')}</p>
              <h3 className="mt-2 text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>
                {t('topologyDrawer.observationsTitle')}
              </h3>
              {latestObservation && !showObservations ? (
                <p className="mt-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
                  {latestObservation.protocol} •{' '}
                  {new Date(latestObservation.timestamp).toLocaleString()}
                </p>
              ) : null}
            </div>
            <Button
              onClick={() => {
                if (!showObservations && observations.length === 0) {
                  fetchObservations();
                }
                setShowObservations((previous) => !previous);
              }}
              size="sm"
              variant="secondary"
            >
              {showObservations ? t('common.collapse') : t('common.expand')}
            </Button>
          </div>

          {showObservations ? (
            <div className="mt-4 space-y-3">
              {isLoadingObservations ? (
                <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                  {t('topologyDrawer.loadingObservations')}
                </p>
              ) : null}
              {!isLoadingObservations && observations.length === 0 ? (
                <EmptyState
                  description={t('topologyDrawer.noObservationsDesc')}
                  icon={Network}
                  title={t('topologyDrawer.noObservationsTitle')}
                />
              ) : null}
              {!isLoadingObservations &&
                observations.map((observation) => (
                  <Surface className="p-4" key={observation.id} tone="subtle">
                    <div className="zh-toolbar zh-toolbar--spread">
                      <div className="zh-toolbar__group">
                        <Badge tone="neutral">{observation.protocol}</Badge>
                        <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
                          {new Date(observation.timestamp).toLocaleString()}
                        </span>
                      </div>
                      <Button
                        onClick={() => copyObservationJson(observation)}
                        size="sm"
                        variant="ghost"
                      >
                        <FileJson className="h-4 w-4" />
                        {t('topologyDrawer.copyJson')}
                      </Button>
                    </div>
                    {observation.raw_summary ? (
                      <p className="mt-3 text-sm" style={{ color: 'var(--text-primary)' }}>
                        {observation.raw_summary}
                      </p>
                    ) : null}
                    <div className="mt-3 flex flex-wrap gap-2">
                      {observation.keywords.slice(0, 12).map((keyword) => (
                        <Badge key={keyword} tone="neutral">
                          {keyword}
                        </Badge>
                      ))}
                    </div>
                    <pre
                      className="mt-3 overflow-x-auto rounded-[1rem] border p-3 text-xs"
                      style={{
                        background: 'var(--surface-inset)',
                        borderColor: 'var(--border)',
                        color: 'var(--text-secondary)',
                      }}
                    >
                      {JSON.stringify(observation.key_fields, null, 2)}
                    </pre>
                  </Surface>
                ))}
              {observations.length > 0 ? (
                <div className="flex justify-end">
                  <Button
                    loading={isExporting}
                    onClick={exportNdjson}
                    size="sm"
                    variant="secondary"
                  >
                    <Download className="h-4 w-4" />
                    {t('topologyDrawer.exportNdjson')}
                  </Button>
                </div>
              ) : null}
            </div>
          ) : null}
        </Surface>
      </div>

      <div
        className="px-6 py-4 text-xs"
        style={{
          borderTop: '1px solid var(--border)',
          color: 'var(--text-tertiary)',
        }}
      >
        {t('topologyDrawer.footerHint')}
      </div>
    </div>
  );
};
