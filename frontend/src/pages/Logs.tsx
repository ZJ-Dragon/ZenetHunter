import React, { useEffect, useState } from 'react';
import { logsService, SystemLog, SystemInfo } from '../lib/services/logs';
import { RefreshCw, AlertCircle, Info, AlertTriangle, XCircle, CheckCircle, Terminal, Server } from 'lucide-react';
import { clsx } from 'clsx';

const LogLevelIcon: React.FC<{ level: string }> = ({ level }) => {
  const levelLower = level.toLowerCase();
  if (levelLower === 'error' || levelLower === 'critical') {
    return <XCircle className="h-4 w-4 text-red-500" />;
  } else if (levelLower === 'warning') {
    return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
  } else if (levelLower === 'info') {
    return <Info className="h-4 w-4 text-blue-500" />;
  } else {
    return <AlertCircle className="h-4 w-4 text-gray-400" />;
  }
};

const LogLevelBadge: React.FC<{ level: string }> = ({ level }) => {
  const levelLower = level.toLowerCase();
  const badgeStyles: Record<string, { bg: string; text: string }> = {
    error: { bg: 'rgba(209, 52, 56, 0.1)', text: '#d13438' },
    critical: { bg: 'rgba(209, 52, 56, 0.1)', text: '#d13438' },
    warning: { bg: 'rgba(255, 170, 68, 0.1)', text: '#ffaa44' },
    info: { bg: 'rgba(0, 120, 212, 0.1)', text: 'var(--winui-accent)' },
    debug: { bg: 'var(--winui-bg-tertiary)', text: 'var(--winui-text-secondary)' },
  };
  
  const style = badgeStyles[levelLower] || badgeStyles.debug;
  
  return (
    <span 
      className="px-3 py-1 text-xs font-semibold rounded-full"
      style={{ 
        backgroundColor: style.bg, 
        color: style.text,
        borderRadius: 'var(--winui-radius-lg)'
      }}
    >
      {level.toUpperCase()}
    </span>
  );
};

export const Logs: React.FC = () => {
  const [logs, setLogs] = useState<SystemLog[]>([]);
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [filterLevel, setFilterLevel] = useState<string>('all');
  const [limit, setLimit] = useState(100);

  const fetchLogs = async () => {
    try {
      const data = await logsService.getLogs(limit);
      setLogs(data);
    } catch (error) {
      console.error('Failed to fetch logs:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchSystemInfo = async () => {
    try {
      const info = await logsService.getSystemInfo();
      setSystemInfo(info);
    } catch (error) {
      console.error('Failed to fetch system info:', error);
    }
  };

  useEffect(() => {
    fetchLogs();
    fetchSystemInfo();
    // Auto-refresh every 5 seconds
    const interval = setInterval(fetchLogs, 5000);
    return () => clearInterval(interval);
  }, [limit]);

  const filteredLogs = filterLevel === 'all' 
    ? logs 
    : logs.filter(log => log.level.toLowerCase() === filterLevel.toLowerCase());

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-semibold flex items-center gap-2" style={{ color: 'var(--winui-text-primary)', letterSpacing: '-0.02em' }}>
            <Terminal className="h-8 w-8" style={{ color: 'var(--winui-accent)' }} />
            System Logs & Information
          </h1>
          <p className="mt-1 text-sm" style={{ color: 'var(--winui-text-secondary)' }}>
            View application logs and system environment information.
          </p>
        </div>
        <button
          onClick={() => {
            setIsLoading(true);
            fetchLogs();
            fetchSystemInfo();
          }}
          className="btn-winui-secondary inline-flex items-center"
        >
          <RefreshCw className={clsx("h-4 w-4 mr-2", isLoading && "animate-spin")} />
          Refresh
        </button>
      </div>

      {/* System Information - WinUI3 Style */}
      {systemInfo && (
        <div className="card-winui overflow-hidden">
          <div className="px-4 py-5 border-b sm:px-6" style={{ borderColor: 'var(--winui-border-subtle)' }}>
            <h3 className="text-lg leading-6 font-semibold flex items-center gap-2" style={{ color: 'var(--winui-text-primary)' }}>
              <Server className="h-5 w-5" style={{ color: 'var(--winui-text-tertiary)' }} />
              System Information
            </h3>
          </div>
          <div className="px-4 py-5 sm:p-6">
            <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
              <div>
                <dt className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>Platform</dt>
                <dd className="mt-1 text-sm font-mono" style={{ color: 'var(--winui-text-primary)' }}>{systemInfo.platform}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>Python Version</dt>
                <dd className="mt-1 text-sm font-mono" style={{ color: 'var(--winui-text-primary)' }}>{systemInfo.python_version}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>App Version</dt>
                <dd className="mt-1 text-sm" style={{ color: 'var(--winui-text-primary)' }}>{systemInfo.app_version}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>Environment</dt>
                <dd className="mt-1 text-sm" style={{ color: 'var(--winui-text-primary)' }}>{systemInfo.app_env}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>Docker Container</dt>
                <dd className="mt-1 text-sm">
                  {systemInfo.docker ? (
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold" style={{ backgroundColor: 'rgba(0, 120, 212, 0.1)', color: 'var(--winui-accent)' }}>
                      Yes
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold" style={{ backgroundColor: 'var(--winui-bg-tertiary)', color: 'var(--winui-text-secondary)' }}>
                      No
                    </span>
                  )}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>Database</dt>
                <dd className="mt-1 text-sm">
                  {systemInfo.database_url ? (
                    <CheckCircle className="h-5 w-5" style={{ color: '#107c10' }} />
                  ) : (
                    <XCircle className="h-5 w-5" style={{ color: '#d13438' }} />
                  )}
                </dd>
              </div>
            </dl>
            
            {/* Capabilities */}
            <div className="mt-6 pt-6" style={{ borderTop: '1px solid var(--winui-border-subtle)' }}>
              <h4 className="text-sm font-semibold mb-4" style={{ color: 'var(--winui-text-primary)' }}>Capabilities</h4>
              <dl className="grid grid-cols-1 gap-x-4 gap-y-4 sm:grid-cols-3">
                <div>
                  <dt className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>Scapy Available</dt>
                  <dd className="mt-1">
                    {systemInfo.capabilities.scapy_available ? (
                      <CheckCircle className="h-5 w-5" style={{ color: '#107c10' }} />
                    ) : (
                      <XCircle className="h-5 w-5" style={{ color: '#d13438' }} />
                    )}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>Root Permissions</dt>
                  <dd className="mt-1">
                    {systemInfo.capabilities.root_permissions ? (
                      <CheckCircle className="h-5 w-5" style={{ color: '#107c10' }} />
                    ) : (
                      <XCircle className="h-5 w-5" style={{ color: '#d13438' }} />
                    )}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>Network Scan</dt>
                  <dd className="mt-1">
                    {systemInfo.capabilities.network_scan_available ? (
                      <CheckCircle className="h-5 w-5" style={{ color: '#107c10' }} />
                    ) : (
                      <XCircle className="h-5 w-5" style={{ color: '#d13438' }} />
                    )}
                  </dd>
                </div>
              </dl>
            </div>
          </div>
        </div>
      )}

      {/* Logs - WinUI3 Style */}
      <div className="card-winui overflow-hidden">
        <div className="px-4 py-5 border-b sm:px-6 flex justify-between items-center" style={{ borderColor: 'var(--winui-border-subtle)' }}>
          <h3 className="text-lg leading-6 font-semibold" style={{ color: 'var(--winui-text-primary)' }}>System Logs</h3>
          <div className="flex items-center space-x-4">
            <select
              value={filterLevel}
              onChange={(e) => setFilterLevel(e.target.value)}
              className="input-winui block pl-3 pr-10 py-2 text-sm"
            >
              <option value="all">All Levels</option>
              <option value="debug">Debug</option>
              <option value="info">Info</option>
              <option value="warning">Warning</option>
              <option value="error">Error</option>
              <option value="critical">Critical</option>
            </select>
            <select
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              className="input-winui block pl-3 pr-10 py-2 text-sm"
            >
              <option value="50">50 logs</option>
              <option value="100">100 logs</option>
              <option value="200">200 logs</option>
              <option value="500">500 logs</option>
            </select>
          </div>
        </div>
        <div className="overflow-y-auto max-h-[600px]">
          <table className="min-w-full" style={{ borderCollapse: 'separate', borderSpacing: 0 }}>
            <thead className="sticky top-0" style={{ backgroundColor: 'var(--winui-bg-tertiary)' }}>
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--winui-text-secondary)' }}>Time</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--winui-text-secondary)' }}>Level</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--winui-text-secondary)' }}>Module</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--winui-text-secondary)' }}>Message</th>
              </tr>
            </thead>
            <tbody style={{ backgroundColor: 'var(--winui-surface)' }}>
              {filteredLogs.length > 0 ? (
                filteredLogs.map((log) => (
                  <tr 
                    key={log.id || `${log.timestamp}-${log.message}`} 
                    className="transition-colors duration-150"
                    style={{ borderBottom: '1px solid var(--winui-border-subtle)' }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = 'var(--winui-bg-tertiary)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'var(--winui-surface)';
                    }}
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono" style={{ color: 'var(--winui-text-secondary)' }}>
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <LogLevelBadge level={log.level} />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm" style={{ color: 'var(--winui-text-secondary)' }}>
                      {log.module}
                    </td>
                    <td className="px-6 py-4 text-sm" style={{ color: 'var(--winui-text-primary)' }}>
                      <div className="flex items-start">
                        <LogLevelIcon level={log.level} className="mr-2 mt-0.5 flex-shrink-0" />
                        <div>
                          <div>{log.message}</div>
                          {log.device_mac && (
                            <div className="text-xs mt-1" style={{ color: 'var(--winui-text-tertiary)' }}>Device: {log.device_mac}</div>
                          )}
                          {log.context && Object.keys(log.context).length > 0 && (
                            <details className="mt-1">
                              <summary className="text-xs cursor-pointer" style={{ color: 'var(--winui-text-tertiary)' }}>Context</summary>
                              <pre className="text-xs mt-1 ml-4 overflow-x-auto" style={{ color: 'var(--winui-text-secondary)' }}>
                                {JSON.stringify(log.context, null, 2)}
                              </pre>
                            </details>
                          )}
                        </div>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={4} className="px-6 py-8 text-center" style={{ color: 'var(--winui-text-secondary)' }}>
                    No logs found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
