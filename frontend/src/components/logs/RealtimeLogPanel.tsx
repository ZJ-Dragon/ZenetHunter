import React, { useEffect, useState, useRef } from 'react';
import { useWebSocketEvent } from '../../contexts/WebSocketContext';
import { WSEventType } from '../../types/websocket';
import { SystemLog } from '../../lib/services/logs';
import { X, Terminal, AlertCircle, Info, AlertTriangle, XCircle } from 'lucide-react';

interface RealtimeLogPanelProps {
  isOpen: boolean;
  onClose: () => void;
  maxLogs?: number;
}

const LogLevelIcon: React.FC<{ level: string }> = ({ level }) => {
  const levelLower = level.toLowerCase();
  if (levelLower === 'error' || levelLower === 'critical') {
    return <XCircle className="h-3 w-3 text-red-500" />;
  } else if (levelLower === 'warning') {
    return <AlertTriangle className="h-3 w-3 text-yellow-500" />;
  } else if (levelLower === 'info') {
    return <Info className="h-3 w-3 text-blue-500" />;
  } else {
    return <AlertCircle className="h-3 w-3 text-gray-400" />;
  }
};

export const RealtimeLogPanel: React.FC<RealtimeLogPanelProps> = ({
  isOpen,
  onClose,
  maxLogs = 50
}) => {
  const [logs, setLogs] = useState<SystemLog[]>([]);
  const logEndRef = useRef<HTMLDivElement>(null);

  // Listen for new logs via WebSocket
  useWebSocketEvent<SystemLog>(WSEventType.LOG_ADDED, (log) => {
    setLogs((prev) => {
      const newLogs = [log, ...prev].slice(0, maxLogs);
      return newLogs;
    });
  });

  // Auto-scroll to bottom when new log arrives
  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed bottom-0 right-0 w-96 h-96 z-50 flex flex-col"
      style={{
        backgroundColor: 'var(--winui-surface)',
        borderTop: '1px solid var(--winui-border-subtle)',
        borderLeft: '1px solid var(--winui-border-subtle)',
        borderRadius: 'var(--winui-radius-lg) 0 0 0',
        boxShadow: '0 -4px 12px rgba(0, 0, 0, 0.15)',
      }}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3 border-b"
        style={{ borderColor: 'var(--winui-border-subtle)' }}
      >
        <div className="flex items-center space-x-2">
          <Terminal className="h-5 w-5" style={{ color: 'var(--winui-accent)' }} />
          <h3 className="text-sm font-semibold" style={{ color: 'var(--winui-text-primary)' }}>
            实时日志
          </h3>
          <span
            className="px-2 py-0.5 text-xs rounded-full"
            style={{
              backgroundColor: 'var(--winui-bg-tertiary)',
              color: 'var(--winui-text-secondary)',
            }}
          >
            {logs.length}
          </span>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          style={{ color: 'var(--winui-text-secondary)' }}
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Logs List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1" style={{ backgroundColor: 'var(--winui-bg-primary)' }}>
        {logs.length === 0 ? (
          <div className="text-center py-8" style={{ color: 'var(--winui-text-tertiary)' }}>
            <Terminal className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">等待日志...</p>
          </div>
        ) : (
          logs.map((log, index) => (
            <div
              key={log.id || `${log.timestamp}-${index}`}
              className="px-3 py-2 rounded text-xs transition-colors"
              style={{
                backgroundColor: index % 2 === 0 ? 'transparent' : 'var(--winui-bg-tertiary)',
              }}
            >
              <div className="flex items-start space-x-2">
                <LogLevelIcon level={log.level} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-1">
                    <span
                      className="px-1.5 py-0.5 rounded text-xs font-medium"
                      style={{
                        backgroundColor: 'var(--winui-bg-tertiary)',
                        color: 'var(--winui-text-secondary)',
                      }}
                    >
                      {log.level.toUpperCase()}
                    </span>
                    <span className="text-xs font-mono" style={{ color: 'var(--winui-text-tertiary)' }}>
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="text-xs break-words" style={{ color: 'var(--winui-text-primary)' }}>
                    {log.message}
                  </p>
                  {log.module && (
                    <p className="text-xs mt-0.5" style={{ color: 'var(--winui-text-tertiary)' }}>
                      {log.module}
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
        <div ref={logEndRef} />
      </div>
    </div>
  );
};
