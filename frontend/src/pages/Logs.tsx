import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Database,
  Info,
  RefreshCw,
  Server,
  Terminal,
  XCircle,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { EmptyState } from '../components/ui/EmptyState';
import { PageHeader } from '../components/ui/PageHeader';
import { StatCard } from '../components/ui/StatCard';
import { Surface } from '../components/ui/Surface';
import { logsService, SystemInfo, SystemLog } from '../lib/services/logs';

const getLogTone = (level: string) => {
  const normalized = level.toLowerCase();
  if (normalized === 'error' || normalized === 'critical') {
    return 'danger';
  }
  if (normalized === 'warning') {
    return 'warning';
  }
  if (normalized === 'info') {
    return 'accent';
  }
  return 'neutral';
};

const getLogIcon = (level: string) => {
  const normalized = level.toLowerCase();
  if (normalized === 'error' || normalized === 'critical') {
    return XCircle;
  }
  if (normalized === 'warning') {
    return AlertTriangle;
  }
  if (normalized === 'info') {
    return Info;
  }
  return AlertCircle;
};

const capabilitySummary = (systemInfo: SystemInfo | null) => {
  if (!systemInfo) {
    return 0;
  }

  return Object.values(systemInfo.capabilities).filter(Boolean).length;
};

export const Logs: React.FC = () => {
  const { t } = useTranslation();
  const [logs, setLogs] = useState<SystemLog[]>([]);
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [filterLevel, setFilterLevel] = useState<string>('all');
  const [limit, setLimit] = useState(100);

  const fetchLogs = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await logsService.getLogs(limit);
      setLogs(data);
    } catch (error) {
      console.error('Failed to fetch logs:', error);
    } finally {
      setIsLoading(false);
    }
  }, [limit]);

  const fetchSystemInfo = useCallback(async () => {
    try {
      const info = await logsService.getSystemInfo();
      setSystemInfo(info);
    } catch (error) {
      console.error('Failed to fetch system info:', error);
    }
  }, []);

  useEffect(() => {
    fetchLogs();
    fetchSystemInfo();
    const interval = setInterval(fetchLogs, 5000);
    return () => clearInterval(interval);
  }, [fetchLogs, fetchSystemInfo]);

  const filteredLogs = useMemo(
    () =>
      filterLevel === 'all'
        ? logs
        : logs.filter(
            (log) => log.level.toLowerCase() === filterLevel.toLowerCase()
          ),
    [filterLevel, logs]
  );

  return (
    <div className="zh-page">
      <PageHeader
        actions={
          <Button
            leadingIcon={<RefreshCw className={isLoading ? 'h-4 w-4 animate-spin' : 'h-4 w-4'} />}
            onClick={() => {
              fetchLogs();
              fetchSystemInfo();
            }}
            variant="secondary"
          >
            {t('logsPage.refresh')}
          </Button>
        }
        eyebrow={t('logsPage.eyebrow')}
        icon={Terminal}
        subtitle={t('logsPage.subtitle')}
        title={t('logsPage.title')}
      />

      <div className="zh-stat-grid">
        <StatCard
          hint={systemInfo?.platform || t('logsPage.systemInfoHint')}
          icon={Server}
          label={t('logsPage.systemInfo')}
          value={systemInfo?.app_version || '--'}
        />
        <StatCard
          hint={systemInfo?.app_env || t('logsPage.databaseHint')}
          icon={Database}
          label={t('logsPage.database')}
          value={systemInfo?.database_url ? t('settings.connected') : t('settings.disconnected')}
        />
        <StatCard
          hint={t('logsPage.capabilitiesHint')}
          icon={CheckCircle2}
          label={t('logsPage.capabilities')}
          tone="var(--success)"
          value={`${capabilitySummary(systemInfo)}/3`}
        />
      </div>

      {systemInfo ? (
        <Surface className="p-5 lg:p-6" tone="raised">
          <div className="zh-toolbar zh-toolbar--spread">
            <div>
              <p className="zh-kicker">{t('logsPage.systemInfo')}</p>
              <h2 className="mt-2 text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>
                {t('logsPage.diagnosticsTitle')}
              </h2>
            </div>
            <div className="zh-status-strip">
              <Badge tone={systemInfo.docker ? 'accent' : 'neutral'}>
                {t('logsPage.docker')}: {systemInfo.docker ? t('common.yes') : t('common.no')}
              </Badge>
              <Badge tone={systemInfo.database_url ? 'success' : 'danger'}>
                {t('logsPage.database')}
              </Badge>
            </div>
          </div>
          <div className="mt-6 zh-detail-grid">
            <Surface className="zh-detail-card" tone="subtle">
              <p className="zh-detail-card__label">{t('logsPage.platform')}</p>
              <p className="zh-detail-card__value font-mono text-sm">{systemInfo.platform}</p>
            </Surface>
            <Surface className="zh-detail-card" tone="subtle">
              <p className="zh-detail-card__label">{t('logsPage.python')}</p>
              <p className="zh-detail-card__value font-mono text-sm">{systemInfo.python_version}</p>
            </Surface>
            <Surface className="zh-detail-card" tone="subtle">
              <p className="zh-detail-card__label">{t('logsPage.appVersion')}</p>
              <p className="zh-detail-card__value text-sm">{systemInfo.app_version}</p>
            </Surface>
            <Surface className="zh-detail-card" tone="subtle">
              <p className="zh-detail-card__label">{t('logsPage.env')}</p>
              <p className="zh-detail-card__value text-sm">{systemInfo.app_env}</p>
            </Surface>
          </div>
          <div className="mt-6 zh-legend">
            <div className="zh-legend__item">
              <span className="zh-legend__swatch" style={{ background: 'var(--success)' }} />
              {t('logsPage.scapy')}:{' '}
              {systemInfo.capabilities.scapy_available ? t('common.yes') : t('common.no')}
            </div>
            <div className="zh-legend__item">
              <span className="zh-legend__swatch" style={{ background: 'var(--accent)' }} />
              {t('logsPage.root')}:{' '}
              {systemInfo.capabilities.root_permissions ? t('common.yes') : t('common.no')}
            </div>
            <div className="zh-legend__item">
              <span className="zh-legend__swatch" style={{ background: 'var(--warning)' }} />
              {t('logsPage.network')}:{' '}
              {systemInfo.capabilities.network_scan_available ? t('common.yes') : t('common.no')}
            </div>
          </div>
        </Surface>
      ) : null}

      <Surface className="p-5 lg:p-6" tone="raised">
        <div className="zh-toolbar zh-toolbar--spread">
          <div>
            <p className="zh-kicker">{t('logsPage.logsTitle')}</p>
            <h2 className="mt-2 text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>
              {t('logsPage.eventsTitle')}
            </h2>
          </div>
          <div className="zh-toolbar__group">
            <select
              className="zh-field"
              onChange={(event) => setFilterLevel(event.target.value)}
              value={filterLevel}
            >
              <option value="all">{t('logsPage.levelAll')}</option>
              <option value="debug">{t('logsPage.levelDebug')}</option>
              <option value="info">{t('logsPage.levelInfo')}</option>
              <option value="warning">{t('logsPage.levelWarning')}</option>
              <option value="error">{t('logsPage.levelError')}</option>
              <option value="critical">{t('logsPage.levelCritical')}</option>
            </select>
            <select
              className="zh-field"
              onChange={(event) => setLimit(Number(event.target.value))}
              value={limit}
            >
              <option value="50">{t('logsPage.limit', { count: 50 })}</option>
              <option value="100">{t('logsPage.limit', { count: 100 })}</option>
              <option value="200">{t('logsPage.limit', { count: 200 })}</option>
              <option value="500">{t('logsPage.limit', { count: 500 })}</option>
            </select>
          </div>
        </div>
        <div className="mt-6 zh-table-shell">
          <div className="zh-table-scroll max-h-[40rem]">
            <table className="zh-table">
              <thead>
                <tr>
                  <th>{t('logsPage.time')}</th>
                  <th>{t('logsPage.level')}</th>
                  <th>{t('logsPage.module')}</th>
                  <th>{t('logsPage.message')}</th>
                </tr>
              </thead>
              <tbody>
                {filteredLogs.length > 0 ? (
                  filteredLogs.map((log) => {
                    const Icon = getLogIcon(log.level);
                    return (
                      <tr key={log.id || `${log.timestamp}-${log.message}`}>
                        <td className="font-mono text-sm" style={{ color: 'var(--text-secondary)' }}>
                          {new Date(log.timestamp).toLocaleString()}
                        </td>
                        <td>
                          <Badge tone={getLogTone(log.level)}>{log.level.toUpperCase()}</Badge>
                        </td>
                        <td style={{ color: 'var(--text-secondary)' }}>{log.module}</td>
                        <td>
                          <div className="flex items-start gap-3">
                            <Icon
                              className="mt-0.5 h-4 w-4 flex-shrink-0"
                              style={{
                                color:
                                  getLogTone(log.level) === 'danger'
                                    ? 'var(--danger)'
                                    : getLogTone(log.level) === 'warning'
                                      ? 'var(--warning)'
                                      : getLogTone(log.level) === 'accent'
                                        ? 'var(--accent)'
                                        : 'var(--text-tertiary)',
                              }}
                            />
                            <div>
                              <p className="text-sm" style={{ color: 'var(--text-primary)' }}>
                                {log.message}
                              </p>
                              {log.device_mac ? (
                                <p className="mt-1 text-xs" style={{ color: 'var(--text-tertiary)' }}>
                                  {t('logsPage.device')}: {log.device_mac}
                                </p>
                              ) : null}
                              {log.context && Object.keys(log.context).length > 0 ? (
                                <details className="mt-2">
                                  <summary
                                    className="cursor-pointer text-xs"
                                    style={{ color: 'var(--text-tertiary)' }}
                                  >
                                    {t('logsPage.context')}
                                  </summary>
                                  <pre
                                    className="mt-2 overflow-x-auto rounded-2xl border p-3 text-xs"
                                    style={{
                                      background: 'var(--surface-inset)',
                                      borderColor: 'var(--border)',
                                      color: 'var(--text-secondary)',
                                    }}
                                  >
                                    {JSON.stringify(log.context, null, 2)}
                                  </pre>
                                </details>
                              ) : null}
                            </div>
                          </div>
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={4}>
                      <EmptyState
                        description={t('logsPage.empty')}
                        icon={Terminal}
                        title={t('logsPage.emptyTitle')}
                      />
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </Surface>
    </div>
  );
};
