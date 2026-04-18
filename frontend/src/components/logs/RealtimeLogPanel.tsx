import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  Info,
  Terminal,
  X,
  XCircle,
} from 'lucide-react';
import { useWebSocketEvent } from '../../contexts/WebSocketContext';
import { SystemLog } from '../../lib/services/logs';
import { WSEventType } from '../../types/websocket';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { EmptyState } from '../ui/EmptyState';
import { Surface } from '../ui/Surface';

interface RealtimeLogPanelProps {
  isOpen: boolean;
  maxLogs?: number;
  onClose: () => void;
}

const getTone = (level: string) => {
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

const LogLevelIcon: React.FC<{ level: string }> = ({ level }) => {
  const levelLower = level.toLowerCase();
  if (levelLower === 'error' || levelLower === 'critical') {
    return <XCircle className="h-4 w-4" style={{ color: 'var(--danger)' }} />;
  }
  if (levelLower === 'warning') {
    return <AlertTriangle className="h-4 w-4" style={{ color: 'var(--warning)' }} />;
  }
  if (levelLower === 'info') {
    return <Info className="h-4 w-4" style={{ color: 'var(--accent)' }} />;
  }
  return <AlertCircle className="h-4 w-4" style={{ color: 'var(--text-tertiary)' }} />;
};

export const RealtimeLogPanel: React.FC<RealtimeLogPanelProps> = ({
  isOpen,
  onClose,
  maxLogs = 50,
}) => {
  const [logs, setLogs] = useState<SystemLog[]>([]);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [isOpen, onClose]);

  useWebSocketEvent<SystemLog>(WSEventType.LOG_ADDED, (log) => {
    setLogs((previous) => [log, ...previous].slice(0, maxLogs));
  });

  if (!isOpen) {
    return null;
  }

  return (
    <div
      className="fixed bottom-4 right-4 z-50 w-[min(28rem,calc(100vw-2rem))]"
      role="dialog"
      aria-label="Realtime logs"
    >
      <Surface className="overflow-hidden" tone="raised">
        <div
          className="flex items-center justify-between gap-4 px-5 py-4"
          style={{ borderBottom: '1px solid var(--border)' }}
        >
          <div>
            <p className="zh-kicker">Live Feed</p>
            <div className="mt-2 flex items-center gap-2">
              <Terminal className="h-5 w-5" style={{ color: 'var(--accent)' }} />
              <h3 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
                Realtime Logs
              </h3>
              <Badge tone="neutral">{logs.length}</Badge>
            </div>
          </div>
          <Button aria-label="Close realtime log panel" onClick={onClose} size="icon" variant="ghost">
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="max-h-[30rem] overflow-y-auto p-4">
          {logs.length === 0 ? (
            <EmptyState
              description="Logs will appear here as the backend emits new events."
              icon={Terminal}
              title="Waiting for logs"
            />
          ) : (
            <div className="space-y-3">
              {logs.map((log, index) => (
                <Surface
                  className="p-4"
                  key={log.id || `${log.timestamp}-${index}`}
                  tone={index === 0 ? 'subtle' : 'inset'}
                >
                  <div className="flex items-start gap-3">
                    <LogLevelIcon level={log.level} />
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge tone={getTone(log.level)}>{log.level.toUpperCase()}</Badge>
                        <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </span>
                        {log.module ? (
                          <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
                            {log.module}
                          </span>
                        ) : null}
                      </div>
                      <p className="mt-2 text-sm leading-6" style={{ color: 'var(--text-primary)' }}>
                        {log.message}
                      </p>
                    </div>
                  </div>
                </Surface>
              ))}
            </div>
          )}
        </div>
      </Surface>
    </div>
  );
};
