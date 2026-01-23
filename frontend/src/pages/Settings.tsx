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
      toast.loading('正在优雅关闭服务器...', { duration: 2000 });

      await logsService.shutdownServer();

      toast.success('服务器已关闭');

      // Wait a moment then show message
      setTimeout(() => {
        toast.error('与服务器的连接已断开', { duration: 5000 });
      }, 1000);
    } catch (error) {
      console.error('Shutdown failed:', error);
      toast.error('优雅关闭失败，请尝试强制关闭');
      setIsShuttingDown(false);
      setShowShutdownConfirm(false);
      // Show force shutdown option
      setShowForceShutdown(true);
    }
  };

  const handleForceShutdown = async () => {
    setIsShuttingDown(true);
    try {
      toast.error('正在强制关闭服务器...', { duration: 1000 });

      // Call force shutdown API
      await logsService.forceShutdownServer();

      // Server will be killed immediately, so we might not get response
      toast.success('服务器已强制关闭', { duration: 2000 });

      // Wait briefly then close the page
      setTimeout(() => {
        toast.error('连接已断开，页面将在2秒后关闭', { duration: 2000 });
      }, 500);

      // Close the page after 2.5 seconds
      setTimeout(() => {
        window.close();
        // If window.close() doesn't work (browser security), redirect to a blank page
        setTimeout(() => {
          window.location.href = 'about:blank';
        }, 500);
      }, 2500);
    } catch (error) {
      // Server might be killed before sending response, which is expected
      console.log('Force shutdown executed (connection lost is expected)');
      toast.error('服务器已强制终止，页面即将关闭', { duration: 2000 });

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
      alert('设置已保存');
    } catch (error) {
      console.error('Failed to save settings:', error);
      alert('保存失败，请重试');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-semibold flex items-center gap-2" style={{ color: 'var(--winui-text-primary)', letterSpacing: '-0.02em' }}>
            <SettingsIcon className="h-8 w-8" style={{ color: 'var(--winui-accent)' }} />
            设置
          </h1>
          <p className="mt-1 text-sm" style={{ color: 'var(--winui-text-secondary)' }}>
            配置应用程序和系统偏好
          </p>
        </div>
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="btn-winui inline-flex items-center"
        >
          <Save className={clsx("h-4 w-4 mr-2", isSaving && "animate-spin")} />
          {isSaving ? '保存中...' : '保存设置'}
        </button>
      </div>

      {/* Theme Settings */}
      <div className="card-winui p-6">
        <h2 className="text-lg font-semibold mb-4" style={{ color: 'var(--winui-text-primary)' }}>
          外观设置
        </h2>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-2 block" style={{ color: 'var(--winui-text-secondary)' }}>
              主题模式
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
                <p className="text-sm font-medium" style={{ color: 'var(--winui-text-primary)' }}>浅色</p>
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
                <p className="text-sm font-medium" style={{ color: 'var(--winui-text-primary)' }}>深色</p>
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
                <p className="text-sm font-medium" style={{ color: 'var(--winui-text-primary)' }}>跟随系统</p>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Platform Settings */}
      <div className="card-winui p-6">
        <h2 className="text-lg font-semibold mb-4" style={{ color: 'var(--winui-text-primary)' }}>
          平台配置
        </h2>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-2 block" style={{ color: 'var(--winui-text-secondary)' }}>
              客户端平台
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
              选择运行环境以使用对应的网络脚本
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
              扫描配置
            </h2>
            <button
              onClick={fetchScanConfig}
              className="btn-winui-secondary inline-flex items-center"
            >
              <RefreshCw className={clsx("h-4 w-4 mr-2", isLoading && "animate-spin")} />
              刷新
            </button>
          </div>
          <div className="space-y-4">
            <div className="grid grid-cols-1 gap-x-4 gap-y-4 sm:grid-cols-2">
              <div>
                <dt className="text-sm font-medium mb-1" style={{ color: 'var(--winui-text-secondary)' }}>扫描网段</dt>
                <dd className="text-sm font-mono" style={{ color: 'var(--winui-text-primary)' }}>
                  {scanConfig.scan_range}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium mb-1" style={{ color: 'var(--winui-text-secondary)' }}>超时时间</dt>
                <dd className="text-sm" style={{ color: 'var(--winui-text-primary)' }}>
                  {scanConfig.scan_timeout_sec} 秒
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium mb-1" style={{ color: 'var(--winui-text-secondary)' }}>并发数</dt>
                <dd className="text-sm" style={{ color: 'var(--winui-text-primary)' }}>
                  {scanConfig.scan_concurrency}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium mb-1" style={{ color: 'var(--winui-text-secondary)' }}>扫描间隔</dt>
                <dd className="text-sm" style={{ color: 'var(--winui-text-primary)' }}>
                  {scanConfig.scan_interval_sec ? `${scanConfig.scan_interval_sec} 秒` : '手动扫描'}
                </dd>
              </div>
            </div>

            <div className="mt-6 pt-6" style={{ borderTop: '1px solid var(--winui-border-subtle)' }}>
              <h4 className="text-sm font-semibold mb-4" style={{ color: 'var(--winui-text-primary)' }}>功能开关</h4>
              <dl className="grid grid-cols-1 gap-x-4 gap-y-3 sm:grid-cols-2 lg:grid-cols-3">
                <div className="flex items-center justify-between">
                  <dt className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>mDNS</dt>
                  <dd className="text-sm">
                    {scanConfig.features.mdns ? (
                      <span className="text-green-600">✓ 启用</span>
                    ) : (
                      <span className="text-gray-500">✗ 禁用</span>
                    )}
                  </dd>
                </div>
                <div className="flex items-center justify-between">
                  <dt className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>SSDP</dt>
                  <dd className="text-sm">
                    {scanConfig.features.ssdp ? (
                      <span className="text-green-600">✓ 启用</span>
                    ) : (
                      <span className="text-gray-500">✗ 禁用</span>
                    )}
                  </dd>
                </div>
                <div className="flex items-center justify-between">
                  <dt className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>NBNS</dt>
                  <dd className="text-sm">
                    {scanConfig.features.nbns ? (
                      <span className="text-green-600">✓ 启用</span>
                    ) : (
                      <span className="text-gray-500">✗ 禁用</span>
                    )}
                  </dd>
                </div>
                <div className="flex items-center justify-between">
                  <dt className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>SNMP</dt>
                  <dd className="text-sm">
                    {scanConfig.features.snmp ? (
                      <span className="text-green-600">✓ 启用</span>
                    ) : (
                      <span className="text-gray-500">✗ 禁用</span>
                    )}
                  </dd>
                </div>
                <div className="flex items-center justify-between">
                  <dt className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>Fingerbank</dt>
                  <dd className="text-sm">
                    {scanConfig.features.fingerbank ? (
                      <span className="text-green-600">✓ 启用</span>
                    ) : (
                      <span className="text-gray-500">✗ 禁用</span>
                    )}
                  </dd>
                </div>
              </dl>
              <p className="mt-4 text-xs" style={{ color: 'var(--winui-text-tertiary)' }}>
                配置通过环境变量设置，修改配置需要重启后端服务
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
              系统信息
            </h2>
            <button
              onClick={fetchSystemInfo}
              className="btn-winui-secondary inline-flex items-center"
            >
              <RefreshCw className={clsx("h-4 w-4 mr-2", isLoading && "animate-spin")} />
              刷新
            </button>
          </div>
          <dl className="grid grid-cols-1 gap-x-4 gap-y-4 sm:grid-cols-2">
            <div>
              <dt className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>平台</dt>
              <dd className="mt-1 text-sm font-mono" style={{ color: 'var(--winui-text-primary)' }}>
                {systemInfo.platform_name || systemInfo.platform}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>Python 版本</dt>
              <dd className="mt-1 text-sm font-mono" style={{ color: 'var(--winui-text-primary)' }}>
                {systemInfo.python_version}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>应用版本</dt>
              <dd className="mt-1 text-sm" style={{ color: 'var(--winui-text-primary)' }}>
                {systemInfo.app_version}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>运行环境</dt>
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
              <dt className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>Docker 容器</dt>
              <dd className="mt-1 text-sm">
                {systemInfo.docker ? (
                  <span className="text-green-600">是</span>
                ) : (
                  <span className="text-gray-500">否</span>
                )}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>数据库</dt>
              <dd className="mt-1 text-sm">
                {systemInfo.database_url ? (
                  <span className="text-green-600">已连接</span>
                ) : (
                  <span className="text-gray-500">未连接</span>
                )}
              </dd>
            </div>
          </dl>

          {/* Capabilities */}
          <div className="mt-6 pt-6" style={{ borderTop: '1px solid var(--winui-border-subtle)' }}>
            <h4 className="text-sm font-semibold mb-4" style={{ color: 'var(--winui-text-primary)' }}>功能支持</h4>
            <dl className="grid grid-cols-1 gap-x-4 gap-y-4 sm:grid-cols-3">
              <div>
                <dt className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>Scapy</dt>
                <dd className="mt-1">
                  {systemInfo.capabilities?.scapy_available ? (
                    <span className="text-green-600 text-sm">✓ 可用</span>
                  ) : (
                    <span className="text-gray-500 text-sm">✗ 不可用</span>
                  )}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>Root 权限</dt>
                <dd className="mt-1">
                  {systemInfo.capabilities?.root_permissions ? (
                    <span className="text-green-600 text-sm">✓ 已获取</span>
                  ) : (
                    <span className="text-gray-500 text-sm">✗ 未获取</span>
                  )}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>网络扫描</dt>
                <dd className="mt-1">
                  {systemInfo.capabilities?.network_scan_available ? (
                    <span className="text-green-600 text-sm">✓ 可用</span>
                  ) : (
                    <span className="text-gray-500 text-sm">✗ 不可用</span>
                  )}
                </dd>
              </div>
            </dl>
          </div>

          {/* Danger Zone - Server Shutdown */}
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
                  危险区域
                </h4>
                <p className="text-sm text-gray-600 mb-4">
                  关闭后端服务器将终止所有正在运行的操作，包括扫描和主动防御任务。
                  所有WebSocket连接将断开。
                </p>
                {!showShutdownConfirm ? (
                  <div className="space-y-3">
                    <button
                      onClick={() => setShowShutdownConfirm(true)}
                      disabled={isShuttingDown}
                      className="inline-flex items-center px-4 py-2 border border-red-600 rounded-md shadow-sm text-sm font-medium text-red-600 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <Power className="h-4 w-4 mr-2" />
                      优雅关闭服务器
                    </button>

                    {showForceShutdown && (
                      <div className="pt-3 border-t border-red-300">
                        <p className="text-xs text-red-700 mb-2">
                          ⚠️ 优雅关闭失败？使用强制关闭（会立即终止所有进程）
                        </p>
                        <button
                          onClick={handleForceShutdown}
                          disabled={isShuttingDown}
                          className="inline-flex items-center px-4 py-2 border-2 border-red-800 rounded-md shadow-sm text-sm font-medium text-white bg-red-800 hover:bg-red-900 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          <Zap className="h-4 w-4 mr-2" />
                          强制关闭服务器
                        </button>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="flex items-center space-x-3">
                      <p className="text-sm font-medium text-red-600">
                        确定要关闭服务器吗？
                      </p>
                      <button
                        onClick={handleShutdown}
                        disabled={isShuttingDown}
                        className="inline-flex items-center px-3 py-1.5 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
                      >
                        {isShuttingDown ? '关闭中...' : '确认关闭'}
                      </button>
                      <button
                        onClick={() => setShowShutdownConfirm(false)}
                        disabled={isShuttingDown}
                        className="inline-flex items-center px-3 py-1.5 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
                      >
                        取消
                      </button>
                    </div>

                    <div className="pt-3 border-t border-red-300">
                      <p className="text-xs text-red-700 mb-2">
                        💀 如果优雅关闭卡住，点击下方强制关闭（会kill进程）
                      </p>
                      <button
                        onClick={handleForceShutdown}
                        disabled={isShuttingDown}
                        className="inline-flex items-center px-3 py-1.5 border-2 border-red-900 rounded-md shadow-sm text-sm font-medium text-white bg-red-900 hover:bg-black focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-800 disabled:opacity-50"
                      >
                        <Zap className="h-4 w-4 mr-2" />
                        {isShuttingDown ? '强制关闭中...' : '强制关闭'}
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
