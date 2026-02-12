import React, { useEffect, useState, useCallback } from 'react';
import { logsService, ScanConfig } from '../lib/services/logs';
import {
  Settings as SettingsIcon,
  Moon,
  Sun,
  Monitor,
  Server,
  Save,
  RefreshCw,
  Network,
  Power,
  AlertTriangle,
  Zap,
} from 'lucide-react';
import { clsx } from 'clsx';
import toast from 'react-hot-toast';
import { useTranslation } from 'react-i18next';

type Theme = 'light' | 'dark' | 'system';
type Platform = 'windows' | 'macos' | 'linux';

export const Settings: React.FC = () => {
  const [theme, setTheme] = useState<Theme>('system');
  const [platform, setPlatform] = useState<Platform>('linux');
  const [systemInfo, setSystemInfo] = useState<{
    platform?: string;
    platform_name?: string;
    python_version?: string;
    app_version?: string;
    app_env?: string;
    database_url?: string;
    docker?: boolean;
    capabilities?: {
      scapy_available?: boolean;
      root_permissions?: boolean;
      network_scan_available?: boolean;
    };
  } | null>(null);
  const [scanConfig, setScanConfig] = useState<ScanConfig | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isShuttingDown, setIsShuttingDown] = useState(false);
  const [showShutdownConfirm, setShowShutdownConfirm] = useState(false);
  const [showForceShutdown, setShowForceShutdown] = useState(false);
  const [showReplayConfirm, setShowReplayConfirm] = useState(false);
  const [isReplaying, setIsReplaying] = useState(false);
  const [language, setLanguage] = useState(() => localStorage.getItem('locale') || 'en');
  const { t, i18n } = useTranslation();

  const fetchSystemInfo = useCallback(async () => {
    try {
      const info = await logsService.getSystemInfo();
      setSystemInfo(info);

      // Auto-detect platform from system info
      if (info.platform) {
        const platformLower = info.platform.toLowerCase();
        if (platformLower.includes('windows')) {
          setPlatform('windows');
        } else if (platformLower.includes('darwin') || platformLower.includes('mac')) {
          setPlatform('macos');
        } else {
          setPlatform('linux');
        }
      }
    } catch (error) {
      console.error('Failed to fetch system info:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchScanConfig = useCallback(async () => {
    try {
      const config = await logsService.getScanConfig();
      setScanConfig(config);
    } catch (error) {
      console.error('Failed to fetch scan config:', error);
    }
  }, []);

  useEffect(() => {
    i18n.changeLanguage(language);
    localStorage.setItem('locale', language);
  }, [language, i18n]);

  useEffect(() => {
    // Load theme from localStorage
    const savedTheme = localStorage.getItem('theme') as Theme;
    if (savedTheme && ['light', 'dark', 'system'].includes(savedTheme)) {
      setTheme(savedTheme);
      applyTheme(savedTheme);
    } else {
      // Default to system theme
      applyTheme('system');
    }

    // Load platform from localStorage
    const savedPlatform = localStorage.getItem('platform') as Platform;
    if (savedPlatform && ['windows', 'macos', 'linux'].includes(savedPlatform)) {
      setPlatform(savedPlatform);
    }

    // Fetch system info and scan config
    fetchSystemInfo();
    fetchScanConfig();
  }, [fetchSystemInfo, fetchScanConfig]);

  // Listen for system theme changes when using system theme
  useEffect(() => {
    if (theme !== 'system') return;

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleSystemThemeChange = (e: MediaQueryListEvent) => {
      const root = document.documentElement;
      if (e.matches) {
        root.classList.add('dark');
      } else {
        root.classList.remove('dark');
      }
    };
    mediaQuery.addEventListener('change', handleSystemThemeChange);

    return () => {
      mediaQuery.removeEventListener('change', handleSystemThemeChange);
    };
  }, [theme]);

  const applyTheme = (newTheme: Theme) => {
    const root = document.documentElement;

    if (newTheme === 'system') {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      if (prefersDark) {
        root.classList.add('dark');
      } else {
        root.classList.remove('dark');
      }
    } else {
      if (newTheme === 'dark') {
        root.classList.add('dark');
      } else {
        root.classList.remove('dark');
      }
    }
  };

  const handleThemeChange = (newTheme: Theme) => {
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    applyTheme(newTheme);
  };

  const handlePlatformChange = (newPlatform: Platform) => {
    setPlatform(newPlatform);
    localStorage.setItem('platform', newPlatform);
  };

  const handleShutdown = async () => {
    setIsShuttingDown(true);
    try {
      toast.loading(t('settings.shutdownProgress'), { duration: 2000 });

      await logsService.shutdownServer();

      toast.success(t('settings.shutdownDone'));

      // Wait a moment then show message
      setTimeout(() => {
        toast.error(t('settings.shutdownDisconnected'), { duration: 5000 });
      }, 1000);
    } catch (error) {
      console.error('Shutdown failed:', error);
      toast.error(t('settings.shutdownFailed'));
      setIsShuttingDown(false);
      setShowShutdownConfirm(false);
      // Show force shutdown option
      setShowForceShutdown(true);
    }
  };

  const handleForceShutdown = async () => {
    setIsShuttingDown(true);
    try {
      toast.error(t('settings.forceProgress'), { duration: 1000 });

      // Call force shutdown API
      await logsService.forceShutdownServer();

      // Server will be killed immediately, so we might not get response
      toast.success(t('settings.forceDone'), { duration: 2000 });

      // Wait briefly then close the page
      setTimeout(() => {
        toast.error(t('settings.forceDisconnect'), { duration: 2000 });
      }, 500);

      // Close the page after 2.5 seconds
      setTimeout(() => {
        window.close();
        // If window.close() doesn't work (browser security), redirect to a blank page
        setTimeout(() => {
          window.location.href = 'about:blank';
        }, 500);
      }, 2500);
    } catch (err) {
      // Server might be killed before sending response, which is expected
      console.log('Force shutdown executed (connection lost is expected)', err);
      toast.error(t('settings.forceTerminate'), { duration: 2000 });

      // Close page even if API call failed (server is likely dead)
      setTimeout(() => {
        window.close();
        setTimeout(() => {
          window.location.href = 'about:blank';
        }, 500);
      }, 2000);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      // Save settings to backend (if API exists)
      // await configService.updateConfig({ theme, platform });

      // For now, just save to localStorage
      localStorage.setItem('theme', theme);
      localStorage.setItem('platform', platform);

      // Show success message
      toast.success(t('settings.saveSuccess'));
    } catch (error) {
      console.error('Failed to save settings:', error);
      toast.error(t('settings.saveFailed'));
    } finally {
      setIsSaving(false);
    }
  };

  const handleReplay = async () => {
    setIsReplaying(true);
    try {
      await logsService.replaySystem();
      toast.success(t('settings.replaySuccess'), { duration: 3000 });
    } catch (error) {
      console.error('Replay failed:', error);
      toast.error(t('settings.replayFailed'));
    } finally {
      setIsReplaying(false);
      setShowReplayConfirm(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-semibold flex items-center gap-2" style={{ color: 'var(--winui-text-primary)', letterSpacing: '-0.02em' }}>
            <SettingsIcon className="h-8 w-8" style={{ color: 'var(--winui-accent)' }} />
            {t('settings.title')}
          </h1>
          <p className="mt-1 text-sm" style={{ color: 'var(--winui-text-secondary)' }}>
            {t('settings.subtitle')}
          </p>
        </div>
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="btn-winui inline-flex items-center"
        >
          <Save className={clsx("h-4 w-4 mr-2", isSaving && "animate-spin")} />
          {isSaving ? t('common.saving') : t('common.save')}
        </button>
      </div>

      {/* Theme Settings */}
      <div className="card-winui p-6">
        <h2 className="text-lg font-semibold mb-4" style={{ color: 'var(--winui-text-primary)' }}>
          {t('settings.appearance')}
        </h2>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-2 block" style={{ color: 'var(--winui-text-secondary)' }}>
              {t('settings.theme')}
            </label>
            <div className="grid grid-cols-3 gap-3">
              <button
                onClick={() => handleThemeChange('light')}
                className={clsx(
                  "p-4 rounded-lg border-2 transition-all",
                  theme === 'light'
                    ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                    : "border-gray-200 dark:border-gray-700 hover:border-gray-300"
                )}
              >
                <Sun className="h-6 w-6 mx-auto mb-2" style={{ color: theme === 'light' ? 'var(--winui-accent)' : 'var(--winui-text-tertiary)' }} />
                <p className="text-sm font-medium" style={{ color: 'var(--winui-text-primary)' }}>{t('settings.theme')} - Light</p>
              </button>
              <button
                onClick={() => handleThemeChange('dark')}
                className={clsx(
                  "p-4 rounded-lg border-2 transition-all",
                  theme === 'dark'
                    ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                    : "border-gray-200 dark:border-gray-700 hover:border-gray-300"
                )}
              >
                <Moon className="h-6 w-6 mx-auto mb-2" style={{ color: theme === 'dark' ? 'var(--winui-accent)' : 'var(--winui-text-tertiary)' }} />
                <p className="text-sm font-medium" style={{ color: 'var(--winui-text-primary)' }}>{t('settings.theme')} - Dark</p>
              </button>
              <button
                onClick={() => handleThemeChange('system')}
                className={clsx(
                  "p-4 rounded-lg border-2 transition-all",
                  theme === 'system'
                    ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                    : "border-gray-200 dark:border-gray-700 hover:border-gray-300"
                )}
              >
                <Monitor className="h-6 w-6 mx-auto mb-2" style={{ color: theme === 'system' ? 'var(--winui-accent)' : 'var(--winui-text-tertiary)' }} />
                <p className="text-sm font-medium" style={{ color: 'var(--winui-text-primary)' }}>{t('settings.theme')} - System</p>
              </button>
            </div>
          </div>
          <div>
            <label className="text-sm font-medium mb-2 block" style={{ color: 'var(--winui-text-secondary)' }}>
              {t('settings.language')}
            </label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="input-winui w-full"
            >
              <option value="en">English</option>
              <option value="zh-CN">简体中文</option>
              <option value="ja-JP">日本語</option>
              <option value="ko-KR">한국어</option>
              <option value="ru-RU">Русский</option>
            </select>
            <p className="text-xs text-gray-500 mt-1">{t('settings.selectLanguage')}</p>
          </div>
        </div>
      </div>

      {/* Platform Settings */}
      <div className="card-winui p-6">
        <h2 className="text-lg font-semibold mb-4" style={{ color: 'var(--winui-text-primary)' }}>
          {t('settings.platformPref')}
        </h2>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-2 block" style={{ color: 'var(--winui-text-secondary)' }}>
              {t('settings.platformLabel')}
            </label>
            <select
              value={platform}
              onChange={(e) => handlePlatformChange(e.target.value as Platform)}
              className="input-winui w-full"
            >
              <option value="windows">Windows</option>
              <option value="macos">macOS</option>
              <option value="linux">Linux</option>
            </select>
            <p className="mt-1 text-xs" style={{ color: 'var(--winui-text-tertiary)' }}>
              {t('settings.platformHint')}
            </p>
          </div>
        </div>
      </div>

      {/* Scan Configuration */}
      {scanConfig && (
        <div className="card-winui p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold flex items-center gap-2" style={{ color: 'var(--winui-text-primary)' }}>
              <Network className="h-5 w-5" style={{ color: 'var(--winui-accent)' }} />
              {t('settings.scanConfig')}
            </h2>
            <button
              onClick={fetchScanConfig}
              className="btn-winui-secondary inline-flex items-center"
            >
              <RefreshCw className={clsx("h-4 w-4 mr-2", isLoading && "animate-spin")} />
              {t('settings.refresh')}
            </button>
          </div>
          <div className="space-y-4">
            <div className="grid grid-cols-1 gap-x-4 gap-y-4 sm:grid-cols-2">
              <div>
                <dt className="text-sm font-medium mb-1" style={{ color: 'var(--winui-text-secondary)' }}>{t('settings.scanRange')}</dt>
                <dd className="text-sm font-mono" style={{ color: 'var(--winui-text-primary)' }}>
                  {scanConfig.scan_range}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium mb-1" style={{ color: 'var(--winui-text-secondary)' }}>{t('settings.scanTimeout')}</dt>
                <dd className="text-sm" style={{ color: 'var(--winui-text-primary)' }}>
                  {scanConfig.scan_timeout_sec} s
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium mb-1" style={{ color: 'var(--winui-text-secondary)' }}>{t('settings.scanConcurrency')}</dt>
                <dd className="text-sm" style={{ color: 'var(--winui-text-primary)' }}>
                  {scanConfig.scan_concurrency}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium mb-1" style={{ color: 'var(--winui-text-secondary)' }}>{t('settings.scanInterval')}</dt>
                <dd className="text-sm" style={{ color: 'var(--winui-text-primary)' }}>
                  {scanConfig.scan_interval_sec ? `${scanConfig.scan_interval_sec} s` : 'manual'}
                </dd>
              </div>
            </div>

            <div className="mt-6 pt-6" style={{ borderTop: '1px solid var(--winui-border-subtle)' }}>
              <h4 className="text-sm font-semibold mb-4" style={{ color: 'var(--winui-text-primary)' }}>{t('settings.features')}</h4>
              <dl className="grid grid-cols-1 gap-x-4 gap-y-3 sm:grid-cols-2 lg:grid-cols-3">
                <div className="flex items-center justify-between">
                  <dt className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>mDNS</dt>
                  <dd className="text-sm">
                    {scanConfig.features.mdns ? (
                      <span className="text-green-600">{t('settings.enabled')}</span>
                    ) : (
                      <span className="text-gray-500">{t('settings.disabled')}</span>
                    )}
                  </dd>
                </div>
                <div className="flex items-center justify-between">
                  <dt className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>SSDP</dt>
                  <dd className="text-sm">
                    {scanConfig.features.ssdp ? (
                      <span className="text-green-600">{t('settings.enabled')}</span>
                    ) : (
                      <span className="text-gray-500">{t('settings.disabled')}</span>
                    )}
                  </dd>
                </div>
                <div className="flex items-center justify-between">
                  <dt className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>NBNS</dt>
                  <dd className="text-sm">
                    {scanConfig.features.nbns ? (
                      <span className="text-green-600">{t('settings.enabled')}</span>
                    ) : (
                      <span className="text-gray-500">{t('settings.disabled')}</span>
                    )}
                  </dd>
                </div>
                <div className="flex items-center justify-between">
                  <dt className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>SNMP</dt>
                  <dd className="text-sm">
                    {scanConfig.features.snmp ? (
                      <span className="text-green-600">{t('settings.enabled')}</span>
                    ) : (
                      <span className="text-gray-500">{t('settings.disabled')}</span>
                    )}
                  </dd>
                </div>
                <div className="flex items-center justify-between">
                  <dt className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>Fingerbank</dt>
                  <dd className="text-sm">
                    {scanConfig.features.fingerbank ? (
                      <span className="text-green-600">{t('settings.enabled')}</span>
                    ) : (
                      <span className="text-gray-500">{t('settings.disabled')}</span>
                    )}
                  </dd>
                </div>
              </dl>
              <p className="mt-4 text-xs" style={{ color: 'var(--winui-text-tertiary)' }}>
                {t('settings.subtitle')}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* System Information */}
      {systemInfo && (
        <div className="card-winui p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold flex items-center gap-2" style={{ color: 'var(--winui-text-primary)' }}>
              <Server className="h-5 w-5" style={{ color: 'var(--winui-accent)' }} />
              {t('settings.capabilities')}
            </h2>
            <button
              onClick={fetchSystemInfo}
              className="btn-winui-secondary inline-flex items-center"
            >
              <RefreshCw className={clsx("h-4 w-4 mr-2", isLoading && "animate-spin")} />
              {t('settings.refresh')}
            </button>
          </div>
          <dl className="grid grid-cols-1 gap-x-4 gap-y-4 sm:grid-cols-2">
            <div>
              <dt className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>{t('settings.platform')}</dt>
              <dd className="mt-1 text-sm font-mono" style={{ color: 'var(--winui-text-primary)' }}>
                {systemInfo.platform_name || systemInfo.platform}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>{t('settings.pythonVersion')}</dt>
              <dd className="mt-1 text-sm font-mono" style={{ color: 'var(--winui-text-primary)' }}>
                {systemInfo.python_version}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>{t('settings.appVersion')}</dt>
              <dd className="mt-1 text-sm" style={{ color: 'var(--winui-text-primary)' }}>
                {systemInfo.app_version}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>{t('settings.appEnv')}</dt>
              <dd className="mt-1 text-sm">
                <span
                  className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold"
                  style={{
                    backgroundColor: systemInfo.app_env === 'production' ? 'rgba(220, 38, 38, 0.1)' : 'rgba(0, 120, 212, 0.1)',
                    color: systemInfo.app_env === 'production' ? '#dc2626' : 'var(--winui-accent)',
                  }}
                >
                  {systemInfo.app_env}
                </span>
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>{t('settings.docker')}</dt>
              <dd className="mt-1 text-sm">
                {systemInfo.docker ? (
                  <span className="text-green-600">{t('settings.connected')}</span>
                ) : (
                  <span className="text-gray-500">{t('settings.disconnected')}</span>
                )}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>{t('settings.database')}</dt>
              <dd className="mt-1 text-sm">
                {systemInfo.database_url ? (
                  <span className="text-green-600">{t('settings.connected')}</span>
                ) : (
                  <span className="text-gray-500">{t('settings.disconnected')}</span>
                )}
              </dd>
            </div>
          </dl>

          {/* Capabilities */}
          <div className="mt-6 pt-6" style={{ borderTop: '1px solid var(--winui-border-subtle)' }}>
            <h4 className="text-sm font-semibold mb-4" style={{ color: 'var(--winui-text-primary)' }}>{t('settings.featureSupport')}</h4>
            <dl className="grid grid-cols-1 gap-x-4 gap-y-4 sm:grid-cols-3">
              <div>
                <dt className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>Scapy</dt>
                <dd className="mt-1">
                  {systemInfo.capabilities?.scapy_available ? (
                    <span className="text-green-600 text-sm">{t('settings.available')}</span>
                  ) : (
                    <span className="text-gray-500 text-sm">{t('settings.unavailable')}</span>
                  )}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>{t('settings.root')}</dt>
                <dd className="mt-1">
                  {systemInfo.capabilities?.root_permissions ? (
                    <span className="text-green-600 text-sm">{t('settings.available')}</span>
                  ) : (
                    <span className="text-gray-500 text-sm">{t('settings.unavailable')}</span>
                  )}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>{t('settings.networkScan')}</dt>
                <dd className="mt-1">
                  {systemInfo.capabilities?.network_scan_available ? (
                    <span className="text-green-600 text-sm">{t('settings.available')}</span>
                  ) : (
                    <span className="text-gray-500 text-sm">{t('settings.unavailable')}</span>
                  )}
                </dd>
              </div>
            </dl>
          </div>

          {/* Danger Zone - Server Shutdown & Replay */}
          <div
            className="mt-6 pt-6 px-4 py-4 rounded-lg"
            style={{
              borderTop: '1px solid var(--winui-border-subtle)',
              backgroundColor: 'rgba(220, 38, 38, 0.05)',
              border: '1px solid rgba(220, 38, 38, 0.2)',
            }}
          >
            <div className="flex items-start">
              <AlertTriangle className="h-5 w-5 text-red-600 mr-3 mt-0.5" />
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-red-600 mb-2">
                  {t('common.dangerZone')}
                </h4>
                <p className="text-sm text-gray-600 mb-4">
                  {t('settings.dangerText')}
                </p>
                {showReplayConfirm && (
                  <div className="mb-4 p-3 border border-indigo-300 rounded-lg bg-indigo-50">
                    <p className="text-sm text-indigo-800 font-semibold mb-2">
                      {t('settings.replayConfirmTitle')}
                    </p>
                    <p className="text-xs text-indigo-700 mb-3">
                      {t('settings.replayConfirmDesc')}
                    </p>
                    <div className="flex gap-2">
                      <button
                        onClick={handleReplay}
                        disabled={isReplaying}
                        className="inline-flex items-center px-3 py-1.5 border border-indigo-700 rounded-md shadow-sm text-sm font-medium text-white bg-indigo-700 hover:bg-indigo-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-600 disabled:opacity-50"
                      >
                        {isReplaying ? t('settings.replaying') : t('settings.replayAction')}
                      </button>
                      <button
                        onClick={() => setShowReplayConfirm(false)}
                        disabled={isReplaying}
                        className="inline-flex items-center px-3 py-1.5 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
                      >
                        {t('common.cancel')}
                      </button>
                    </div>
                  </div>
                )}
                <div className="flex items-center gap-3 mb-4">
                  <button
                    onClick={() => setShowReplayConfirm(true)}
                    disabled={isReplaying}
                    className="inline-flex items-center px-4 py-2 border border-indigo-600 rounded-md shadow-sm text-sm font-medium text-indigo-700 bg-white hover:bg-indigo-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <RefreshCw className="h-4 w-4 mr-2" />
                    {isReplaying ? t('settings.replaying') : t('settings.replay')}
                  </button>
                  <span className="text-xs text-gray-500">
                    {t('settings.replayDesc')}
                  </span>
                </div>
                {!showShutdownConfirm ? (
                  <div className="space-y-3">
                    <button
                      onClick={() => setShowShutdownConfirm(true)}
                      disabled={isShuttingDown}
                      className="inline-flex items-center px-4 py-2 border border-red-600 rounded-md shadow-sm text-sm font-medium text-red-600 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <Power className="h-4 w-4 mr-2" />
                      {isShuttingDown ? t('settings.shutdownProgress') : t('settings.gracefulShutdown')}
                    </button>

                    {showForceShutdown && (
                      <div className="pt-3 border-t border-red-300">
                        <p className="text-xs text-red-700 mb-2">
                          {t('settings.forceHint')}
                        </p>
                        <button
                          onClick={handleForceShutdown}
                          disabled={isShuttingDown}
                          className="inline-flex items-center px-4 py-2 border-2 border-red-800 rounded-md shadow-sm text-sm font-medium text-white bg-red-800 hover:bg-red-900 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          <Zap className="h-4 w-4 mr-2" />
                          {isShuttingDown ? t('settings.forceProgress') : t('settings.forceShutdown')}
                        </button>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="flex items-center space-x-3">
                      <p className="text-sm font-medium text-red-600">
                        {t('settings.confirmShutdown')}
                      </p>
                      <button
                        onClick={handleShutdown}
                        disabled={isShuttingDown}
                        className="inline-flex items-center px-3 py-1.5 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
                      >
                        {isShuttingDown ? t('settings.shutdownProgress') : t('common.confirm')}
                      </button>
                      <button
                        onClick={() => setShowShutdownConfirm(false)}
                        disabled={isShuttingDown}
                        className="inline-flex items-center px-3 py-1.5 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
                      >
                        {t('common.cancel')}
                      </button>
                    </div>

                    <div className="pt-3 border-t border-red-300">
                      <p className="text-xs text-red-700 mb-2">
                        {t('settings.forceFallback')}
                      </p>
                      <button
                        onClick={handleForceShutdown}
                        disabled={isShuttingDown}
                        className="inline-flex items-center px-3 py-1.5 border-2 border-red-900 rounded-md shadow-sm text-sm font-medium text-white bg-red-900 hover:bg-black focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-800 disabled:opacity-50"
                      >
                        <Zap className="h-4 w-4 mr-2" />
                        {isShuttingDown ? t('settings.forceProgress') : t('settings.forceShutdown')}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
