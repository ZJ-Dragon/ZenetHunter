import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  AlertTriangle,
  Globe2,
  Monitor,
  Moon,
  Power,
  RefreshCw,
  Save,
  Server,
  Settings as SettingsIcon,
  Sun,
  Zap,
} from 'lucide-react';
import { clsx } from 'clsx';
import toast from 'react-hot-toast';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Dialog } from '../components/ui/Dialog';
import { LoadingScreen } from '../components/ui/LoadingScreen';
import { PageHeader } from '../components/ui/PageHeader';
import { StatCard } from '../components/ui/StatCard';
import { Surface } from '../components/ui/Surface';
import { useAuth } from '../contexts/AuthContext';
import { logsService, ScanConfig, SystemInfo } from '../lib/services/logs';
import {
  applyTheme,
  getStoredTheme,
  subscribeToSystemTheme,
  THEME_STORAGE_KEY,
  ThemeMode,
} from '../lib/theme';

type Platform = 'windows' | 'macos' | 'linux';

const LANGUAGE_OPTIONS = [
  { label: 'English', value: 'en' },
  { label: '简体中文', value: 'zh-CN' },
  { label: '日本語', value: 'ja-JP' },
  { label: '한국어', value: 'ko-KR' },
  { label: 'Русский', value: 'ru-RU' },
];

const THEME_ICON_MAP: Record<ThemeMode, React.ElementType> = {
  light: Sun,
  dark: Moon,
  system: Monitor,
};

const getStoredPlatform = (): Platform | null => {
  const value = localStorage.getItem('platform');
  return value === 'windows' || value === 'macos' || value === 'linux'
    ? value
    : null;
};

const detectPlatform = (platformValue?: string): Platform => {
  const normalized = platformValue?.toLowerCase() || '';
  if (normalized.includes('windows')) {
    return 'windows';
  }
  if (normalized.includes('darwin') || normalized.includes('mac')) {
    return 'macos';
  }
  return 'linux';
};

const preferenceTileStyle = (active: boolean) => ({
  background: active ? 'var(--accent-soft)' : 'var(--surface-subtle)',
  borderColor: active ? 'rgba(10, 100, 216, 0.24)' : 'var(--border)',
  boxShadow: active ? 'var(--shadow-sm)' : 'none',
});

export const Settings: React.FC = () => {
  const initialTheme = getStoredTheme();
  const initialPlatform = getStoredPlatform() || 'linux';
  const initialLanguage = localStorage.getItem('locale') || 'en';

  const [theme, setTheme] = useState<ThemeMode>(initialTheme);
  const [platform, setPlatform] = useState<Platform>(initialPlatform);
  const [language, setLanguage] = useState(initialLanguage);
  const [savedPreferences, setSavedPreferences] = useState({
    language: initialLanguage,
    platform: initialPlatform,
    theme: initialTheme,
  });
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [scanConfig, setScanConfig] = useState<ScanConfig | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshingScanConfig, setIsRefreshingScanConfig] = useState(false);
  const [isRefreshingSystemInfo, setIsRefreshingSystemInfo] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isShuttingDown, setIsShuttingDown] = useState(false);
  const [isReplaying, setIsReplaying] = useState(false);
  const [showShutdownConfirm, setShowShutdownConfirm] = useState(false);
  const [showReplayConfirm, setShowReplayConfirm] = useState(false);
  const { t, i18n } = useTranslation();
  const { logout } = useAuth();
  const navigate = useNavigate();

  const fetchSystemInfo = useCallback(async (options?: { refreshing?: boolean }) => {
    if (options?.refreshing) {
      setIsRefreshingSystemInfo(true);
    }

    try {
      const info = await logsService.getSystemInfo();
      setSystemInfo(info);

      if (!getStoredPlatform()) {
        const detected = detectPlatform(info.platform);
        setPlatform(detected);
        setSavedPreferences((previous) => ({
          ...previous,
          platform: detected,
        }));
      }
    } catch (error) {
      console.error('Failed to fetch system info:', error);
    } finally {
      if (options?.refreshing) {
        setIsRefreshingSystemInfo(false);
      }
    }
  }, []);

  const fetchScanConfig = useCallback(async (options?: { refreshing?: boolean }) => {
    if (options?.refreshing) {
      setIsRefreshingScanConfig(true);
    }

    try {
      const config = await logsService.getScanConfig();
      setScanConfig(config);
    } catch (error) {
      console.error('Failed to fetch scan config:', error);
    } finally {
      if (options?.refreshing) {
        setIsRefreshingScanConfig(false);
      }
    }
  }, []);

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  useEffect(() => {
    void i18n.changeLanguage(language);
  }, [i18n, language]);

  useEffect(() => {
    const loadSettings = async () => {
      await Promise.allSettled([fetchSystemInfo(), fetchScanConfig()]);
      setIsLoading(false);
    };

    void loadSettings();
  }, [fetchScanConfig, fetchSystemInfo]);

  useEffect(() => {
    if (theme !== 'system') {
      return undefined;
    }

    return subscribeToSystemTheme(() => applyTheme('system'));
  }, [theme]);

  const isDirty =
    theme !== savedPreferences.theme ||
    platform !== savedPreferences.platform ||
    language !== savedPreferences.language;

  const capabilityCount = useMemo(() => {
    if (!systemInfo) {
      return 0;
    }
    return Object.values(systemInfo.capabilities).filter(Boolean).length;
  }, [systemInfo]);

  const themeOptions = useMemo(
    () => [
      {
        description: t('settings.themeLightDesc'),
        icon: THEME_ICON_MAP.light,
        label: t('settings.themeLight'),
        value: 'light' as const,
      },
      {
        description: t('settings.themeDarkDesc'),
        icon: THEME_ICON_MAP.dark,
        label: t('settings.themeDark'),
        value: 'dark' as const,
      },
      {
        description: t('settings.themeSystemDesc'),
        icon: THEME_ICON_MAP.system,
        label: t('settings.themeSystem'),
        value: 'system' as const,
      },
    ],
    [t]
  );

  const scanFeatures: Array<{ enabled: boolean; label: string }> = scanConfig
    ? [
        { label: 'mDNS', enabled: scanConfig.features.mdns },
        { label: 'SSDP', enabled: scanConfig.features.ssdp },
        { label: 'NBNS', enabled: scanConfig.features.nbns },
        { label: 'SNMP', enabled: scanConfig.features.snmp },
        { label: 'Fingerbank', enabled: scanConfig.features.fingerbank },
      ]
    : [];

  const handleSave = async () => {
    setIsSaving(true);

    try {
      localStorage.setItem(THEME_STORAGE_KEY, theme);
      localStorage.setItem('platform', platform);
      localStorage.setItem('locale', language);
      setSavedPreferences({ language, platform, theme });
      toast.success(t('settings.saveSuccess'));
    } catch (error) {
      console.error('Failed to save settings:', error);
      toast.error(t('settings.saveFailed'));
    } finally {
      setIsSaving(false);
    }
  };

  const handleShutdown = async () => {
    setIsShuttingDown(true);
    try {
      toast.loading(t('settings.shutdownProgress'), { duration: 2000 });
      await logsService.shutdownServer();
      toast.success(t('settings.shutdownDone'));
      setShowShutdownConfirm(false);
      setTimeout(() => {
        toast.error(t('settings.shutdownDisconnected'), { duration: 5000 });
      }, 1000);
    } catch (error) {
      console.error('Shutdown failed:', error);
      toast.error(t('settings.shutdownFailed'));
    } finally {
      setIsShuttingDown(false);
    }
  };

  const handleForceShutdown = async () => {
    setIsShuttingDown(true);
    try {
      toast.error(t('settings.forceProgress'), { duration: 1000 });
      await logsService.forceShutdownServer();
      toast.success(t('settings.forceDone'), { duration: 2000 });
      setShowShutdownConfirm(false);
      setTimeout(() => {
        toast.error(t('settings.forceDisconnect'), { duration: 2000 });
      }, 500);
      setTimeout(() => {
        window.close();
        setTimeout(() => {
          window.location.href = 'about:blank';
        }, 500);
      }, 2500);
    } catch (error) {
      console.log('Force shutdown executed (connection loss is expected)', error);
      toast.error(t('settings.forceTerminate'), { duration: 2000 });
      setTimeout(() => {
        window.close();
        setTimeout(() => {
          window.location.href = 'about:blank';
        }, 500);
      }, 2000);
    } finally {
      setIsShuttingDown(false);
    }
  };

  const handleReplay = async () => {
    setIsReplaying(true);
    try {
      await logsService.replaySystem();
      toast.success(t('settings.replaySuccess'), { duration: 3000 });
      logout();
      navigate('/setup', { replace: true });
    } catch (error) {
      console.error('Replay failed:', error);
      toast.error(t('settings.replayFailed'));
    } finally {
      setIsReplaying(false);
      setShowReplayConfirm(false);
    }
  };

  if (isLoading) {
    return <LoadingScreen message={t('settings.subtitle')} />;
  }

  return (
    <div className="zh-page">
      <PageHeader
        actions={
          <>
            {isDirty ? (
              <Badge tone="warning">{t('settings.unsaved')}</Badge>
            ) : (
              <Badge tone="success">{t('settings.saved')}</Badge>
            )}
            <Button
              leadingIcon={<Save className={isSaving ? 'h-4 w-4 animate-spin' : 'h-4 w-4'} />}
              loading={isSaving}
              onClick={handleSave}
              variant="accent"
            >
              {isSaving ? t('common.saving') : t('common.save')}
            </Button>
          </>
        }
        eyebrow={t('settings.eyebrow')}
        icon={SettingsIcon}
        subtitle={t('settings.subtitle')}
        title={t('settings.title')}
      />

      <div className="zh-stat-grid">
        <StatCard
          hint={t('settings.themeHint')}
          icon={theme === 'dark' ? Moon : theme === 'light' ? Sun : Monitor}
          label={t('settings.theme')}
          value={themeOptions.find((option) => option.value === theme)?.label || theme}
        />
        <StatCard
          hint={t('settings.languageHint')}
          icon={Globe2}
          label={t('settings.language')}
          value={LANGUAGE_OPTIONS.find((option) => option.value === language)?.label || language}
        />
        <StatCard
          hint={t('settings.platformHintShort')}
          icon={Monitor}
          label={t('settings.platformPref')}
          value={platform}
        />
        <StatCard
          hint={t('settings.capabilitiesHint')}
          icon={Server}
          label={t('settings.capabilities')}
          tone="var(--success)"
          value={`${capabilityCount}/3`}
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <Surface className="p-5 lg:p-6" tone="raised">
          <div className="flex items-center gap-3">
            <div
              className="inline-flex h-12 w-12 items-center justify-center rounded-[1.1rem]"
              style={{ background: 'var(--accent-soft)', color: 'var(--accent)' }}
            >
              <Monitor className="h-5 w-5" />
            </div>
            <div>
              <p className="zh-kicker">{t('settings.appearance')}</p>
              <h2 className="mt-1 text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>
                {t('settings.themeAndLanguage')}
              </h2>
            </div>
          </div>

          <div className="mt-6 grid gap-3 md:grid-cols-3">
            {themeOptions.map((option) => {
              const Icon = option.icon;
              const active = theme === option.value;
              return (
                <button
                  aria-pressed={active}
                  className={clsx(
                    'rounded-[1.35rem] border p-5 text-left transition',
                    active && 'translate-y-[-1px]'
                  )}
                  key={option.value}
                  onClick={() => setTheme(option.value)}
                  style={preferenceTileStyle(active)}
                  type="button"
                >
                  <Icon
                    className="h-6 w-6"
                    style={{
                      color: active ? 'var(--accent)' : 'var(--text-tertiary)',
                    }}
                  />
                  <p className="mt-4 text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                    {option.label}
                  </p>
                  <p className="mt-2 text-sm leading-6" style={{ color: 'var(--text-secondary)' }}>
                    {option.description}
                  </p>
                </button>
              );
            })}
          </div>

          <div className="mt-6">
            <label className="mb-2 block text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
              {t('settings.language')}
            </label>
            <select
              className="zh-field"
              onChange={(event) => setLanguage(event.target.value)}
              value={language}
            >
              {LANGUAGE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <p className="mt-2 text-xs" style={{ color: 'var(--text-tertiary)' }}>
              {t('settings.selectLanguage')}
            </p>
          </div>
        </Surface>

        <Surface className="p-5 lg:p-6" tone="raised">
          <div className="flex items-center gap-3">
            <div
              className="inline-flex h-12 w-12 items-center justify-center rounded-[1.1rem]"
              style={{ background: 'var(--surface-inset)', color: 'var(--text-primary)' }}
            >
              <Server className="h-5 w-5" />
            </div>
            <div>
              <p className="zh-kicker">{t('settings.platformPref')}</p>
              <h2 className="mt-1 text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>
                {t('settings.platformRuntime')}
              </h2>
            </div>
          </div>

          <div className="mt-6">
            <label className="mb-2 block text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
              {t('settings.platformLabel')}
            </label>
            <select
              className="zh-field"
              onChange={(event) => setPlatform(event.target.value as Platform)}
              value={platform}
            >
              <option value="windows">Windows</option>
              <option value="macos">macOS</option>
              <option value="linux">Linux</option>
            </select>
            <p className="mt-2 text-xs" style={{ color: 'var(--text-tertiary)' }}>
              {t('settings.platformHint')}
            </p>
          </div>

          <div className="mt-6 zh-detail-grid">
            <Surface className="zh-detail-card" tone="subtle">
              <p className="zh-detail-card__label">{t('settings.platform')}</p>
              <p className="zh-detail-card__value font-mono text-sm">
                {systemInfo?.platform_name || systemInfo?.platform || platform}
              </p>
            </Surface>
            <Surface className="zh-detail-card" tone="subtle">
              <p className="zh-detail-card__label">{t('settings.pythonVersion')}</p>
              <p className="zh-detail-card__value font-mono text-sm">
                {systemInfo?.python_version || '--'}
              </p>
            </Surface>
            <Surface className="zh-detail-card" tone="subtle">
              <p className="zh-detail-card__label">{t('settings.appVersion')}</p>
              <p className="zh-detail-card__value text-sm">{systemInfo?.app_version || '--'}</p>
            </Surface>
            <Surface className="zh-detail-card" tone="subtle">
              <p className="zh-detail-card__label">{t('settings.appEnv')}</p>
              <div className="zh-detail-card__value text-sm">
                {systemInfo?.app_env ? (
                  <Badge tone={systemInfo.app_env === 'production' ? 'danger' : 'accent'}>
                    {systemInfo.app_env}
                  </Badge>
                ) : (
                  '--'
                )}
              </div>
            </Surface>
          </div>
        </Surface>
      </div>

      {scanConfig ? (
        <Surface className="p-5 lg:p-6" tone="raised">
          <div className="zh-toolbar zh-toolbar--spread">
            <div>
              <p className="zh-kicker">{t('settings.scanConfig')}</p>
              <h2 className="mt-2 text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>
                {t('settings.discoveryProfile')}
              </h2>
            </div>
            <Button
              leadingIcon={
                <RefreshCw
                  className={isRefreshingScanConfig ? 'h-4 w-4 animate-spin' : 'h-4 w-4'}
                />
              }
              onClick={() => void fetchScanConfig({ refreshing: true })}
              variant="secondary"
            >
              {t('settings.refresh')}
            </Button>
          </div>

          <div className="mt-6 zh-detail-grid">
            <Surface className="zh-detail-card" tone="subtle">
              <p className="zh-detail-card__label">{t('settings.scanRange')}</p>
              <p className="zh-detail-card__value font-mono text-sm">{scanConfig.scan_range}</p>
            </Surface>
            <Surface className="zh-detail-card" tone="subtle">
              <p className="zh-detail-card__label">{t('settings.scanTimeout')}</p>
              <p className="zh-detail-card__value text-sm">{scanConfig.scan_timeout_sec} s</p>
            </Surface>
            <Surface className="zh-detail-card" tone="subtle">
              <p className="zh-detail-card__label">{t('settings.scanConcurrency')}</p>
              <p className="zh-detail-card__value text-sm">{scanConfig.scan_concurrency}</p>
            </Surface>
            <Surface className="zh-detail-card" tone="subtle">
              <p className="zh-detail-card__label">{t('settings.scanInterval')}</p>
              <p className="zh-detail-card__value text-sm">
                {scanConfig.scan_interval_sec !== null
                  ? `${scanConfig.scan_interval_sec} s`
                  : t('settings.manual')}
              </p>
            </Surface>
          </div>

          <div className="mt-6">
            <p className="zh-kicker">{t('settings.features')}</p>
            <div className="mt-4 flex flex-wrap gap-2">
              {scanFeatures.map(({ enabled, label }) => (
                <Badge key={label} tone={enabled ? 'success' : 'neutral'}>
                  {label}: {enabled ? t('settings.enabled') : t('settings.disabled')}
                </Badge>
              ))}
            </div>
          </div>
        </Surface>
      ) : null}

      {systemInfo ? (
        <Surface className="p-5 lg:p-6" tone="raised">
          <div className="zh-toolbar zh-toolbar--spread">
            <div>
              <p className="zh-kicker">{t('settings.capabilities')}</p>
              <h2 className="mt-2 text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>
                {t('settings.backendDiagnostics')}
              </h2>
            </div>
            <Button
              leadingIcon={
                <RefreshCw
                  className={isRefreshingSystemInfo ? 'h-4 w-4 animate-spin' : 'h-4 w-4'}
                />
              }
              onClick={() => void fetchSystemInfo({ refreshing: true })}
              variant="secondary"
            >
              {t('settings.refresh')}
            </Button>
          </div>

          <div className="mt-6 flex flex-wrap gap-2">
            <Badge tone={systemInfo.docker ? 'accent' : 'neutral'}>
              {t('settings.docker')}: {systemInfo.docker ? t('settings.connected') : t('settings.disconnected')}
            </Badge>
            <Badge tone={systemInfo.database_url ? 'success' : 'danger'}>
              {t('settings.database')}:{' '}
              {systemInfo.database_url ? t('settings.connected') : t('settings.disconnected')}
            </Badge>
            <Badge tone={systemInfo.capabilities.scapy_available ? 'success' : 'neutral'}>
              {t('settings.scapy')}:{' '}
              {systemInfo.capabilities.scapy_available
                ? t('settings.available')
                : t('settings.unavailable')}
            </Badge>
            <Badge tone={systemInfo.capabilities.root_permissions ? 'success' : 'neutral'}>
              {t('settings.root')}:{' '}
              {systemInfo.capabilities.root_permissions
                ? t('settings.available')
                : t('settings.unavailable')}
            </Badge>
            <Badge
              tone={
                systemInfo.capabilities.network_scan_available ? 'success' : 'neutral'
              }
            >
              {t('settings.networkScan')}:{' '}
              {systemInfo.capabilities.network_scan_available
                ? t('settings.available')
                : t('settings.unavailable')}
            </Badge>
          </div>
        </Surface>
      ) : null}

      <Surface className="p-5 lg:p-6" tone="danger">
        <div className="flex items-start gap-4">
          <div
            className="inline-flex h-12 w-12 items-center justify-center rounded-[1.1rem]"
            style={{ background: 'var(--danger-soft)', color: 'var(--danger)' }}
          >
            <AlertTriangle className="h-5 w-5" />
          </div>
          <div className="flex-1">
            <p className="zh-kicker">{t('common.dangerZone')}</p>
            <h2 className="mt-2 text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>
              {t('settings.destructiveOps')}
            </h2>
            <p className="mt-3 text-sm leading-7" style={{ color: 'var(--text-secondary)' }}>
              {t('settings.dangerText')}
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Button
                leadingIcon={<RefreshCw className="h-4 w-4" />}
                onClick={() => setShowReplayConfirm(true)}
                variant="secondary"
              >
                {t('settings.replay')}
              </Button>
              <Button
                leadingIcon={<Power className="h-4 w-4" />}
                onClick={() => setShowShutdownConfirm(true)}
                variant="danger"
              >
                {t('settings.gracefulShutdown')}
              </Button>
            </div>
          </div>
        </div>
      </Surface>

      <Dialog
        footer={
          <>
            <div>
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                {t('settings.replayConfirmDesc')}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button
                onClick={() => setShowReplayConfirm(false)}
                variant="secondary"
              >
                {t('common.cancel')}
              </Button>
              <Button
                loading={isReplaying}
                onClick={handleReplay}
                variant="danger"
              >
                {isReplaying ? t('settings.replaying') : t('settings.replayAction')}
              </Button>
            </div>
          </>
        }
        open={showReplayConfirm}
        title={t('settings.replayConfirmTitle')}
      >
        <p className="text-sm leading-7" style={{ color: 'var(--text-secondary)' }}>
          {t('settings.replayDesc')}
        </p>
      </Dialog>

      <Dialog
        footer={
          <>
            <div>
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                {t('settings.forceFallback')}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button
                onClick={() => setShowShutdownConfirm(false)}
                variant="secondary"
              >
                {t('common.cancel')}
              </Button>
              <Button
                loading={isShuttingDown}
                onClick={handleShutdown}
                variant="danger"
              >
                {t('common.confirm')}
              </Button>
              <Button
                loading={isShuttingDown}
                onClick={handleForceShutdown}
                variant="secondary"
              >
                <Zap className="h-4 w-4" />
                {t('settings.forceShutdown')}
              </Button>
            </div>
          </>
        }
        open={showShutdownConfirm}
        title={t('settings.confirmShutdown')}
      >
        <p className="text-sm leading-7" style={{ color: 'var(--text-secondary)' }}>
          {t('settings.forceHint')}
        </p>
      </Dialog>
    </div>
  );
};
