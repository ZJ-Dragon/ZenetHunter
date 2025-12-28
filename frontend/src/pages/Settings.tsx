import React, { useEffect, useState, useCallback } from 'react';
import { logsService } from '../lib/services/logs';
import { Settings as SettingsIcon, Moon, Sun, Monitor, Server, Save, RefreshCw } from 'lucide-react';
import { clsx } from 'clsx';

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
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

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

    // Fetch system info
    fetchSystemInfo();
  }, [fetchSystemInfo]);

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
        </div>
      )}
    </div>
  );
};
