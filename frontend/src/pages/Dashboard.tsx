import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { deviceService, Device } from '../lib/services/device';
import { attackService } from '../lib/services/attack';
import { useWebSocketEvent } from '../contexts/WebSocketContext';
import { WSEventType } from '../types/websocket';
import {
  LayoutDashboard,
  Network,
  Shield,
  Activity,
  RefreshCw,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Clock,
} from 'lucide-react';
import { ScanButton } from '../components/actions/ScanButton';
import { clsx } from 'clsx';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ElementType;
  trend?: string;
  color?: string;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon: Icon, trend, color = 'var(--winui-accent)' }) => {
  return (
    <div className="card-winui p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>
            {title}
          </p>
          <p className="mt-2 text-3xl font-bold" style={{ color: 'var(--winui-text-primary)' }}>
            {value}
          </p>
          {trend && (
            <p className="mt-1 text-xs flex items-center" style={{ color: 'var(--winui-text-tertiary)' }}>
              <TrendingUp className="h-3 w-3 mr-1" />
              {trend}
            </p>
          )}
        </div>
        <div
          className="p-3 rounded-lg"
          style={{ backgroundColor: `${color}15`, color }}
        >
          <Icon className="h-6 w-6" />
        </div>
      </div>
    </div>
  );
};

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [devices, setDevices] = useState<Device[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [stats, setStats] = useState({
    totalDevices: 0,
    onlineDevices: 0,
    blockedDevices: 0,
    recentAttacks: 0,
  });

  const fetchDevices = useCallback(async () => {
    try {
      const data = await deviceService.getDevices();
      setDevices(data);

      // Calculate statistics
      const online = data.filter(d => d.status === 'online').length;
      const blocked = data.filter(d => d.status === 'blocked').length;

      setStats({
        totalDevices: data.length,
        onlineDevices: online,
        blockedDevices: blocked,
        recentAttacks: data.filter(d => d.attack_status === 'running').length,
      });
    } catch (error) {
      console.error('Failed to fetch devices:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDevices();
  }, [fetchDevices]);

  // Listen for device updates
  useWebSocketEvent(WSEventType.DEVICE_ADDED, () => {
    fetchDevices();
  });

  useWebSocketEvent(WSEventType.DEVICE_STATUS_CHANGED, () => {
    fetchDevices();
  });

  // Get recent devices (last 5)
  const recentDevices = devices
    .sort((a, b) => new Date(b.last_seen).getTime() - new Date(a.last_seen).getTime())
    .slice(0, 5);

  // Get devices with active attacks (using AttackStatus.RUNNING)
  const attackedDevices = devices.filter(d => d.attack_status === 'running');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-semibold flex items-center gap-2" style={{ color: 'var(--winui-text-primary)', letterSpacing: '-0.02em' }}>
            <LayoutDashboard className="h-8 w-8" style={{ color: 'var(--winui-accent)' }} />
            Dashboard
          </h1>
          <p className="mt-1 text-sm" style={{ color: 'var(--winui-text-secondary)' }}>
            网络概览和快速操作
          </p>
        </div>
        <div className="flex space-x-2">
          <ScanButton />
          <button
            onClick={() => {
              setIsLoading(true);
              fetchDevices();
            }}
            className="btn-winui-secondary inline-flex items-center"
          >
            <RefreshCw className={clsx("h-4 w-4 mr-2", isLoading && "animate-spin")} />
            Refresh
          </button>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="总设备数"
          value={stats.totalDevices}
          icon={Network}
          color="var(--winui-accent)"
        />
        <StatCard
          title="在线设备"
          value={stats.onlineDevices}
          icon={CheckCircle}
          color="#10b981"
        />
        <StatCard
          title="已拦截设备"
          value={stats.blockedDevices}
          icon={Shield}
          color="#dc2626"
        />
        <StatCard
          title="活跃攻击"
          value={stats.recentAttacks}
          icon={Activity}
          color="#f59e0b"
        />
      </div>

      {/* Quick Actions & Recent Devices */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Quick Actions */}
        <div className="card-winui p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--winui-text-primary)' }}>
            <Activity className="h-5 w-5" style={{ color: 'var(--winui-accent)' }} />
            快速操作
          </h2>
          <div className="space-y-3">
            <ScanButton className="w-full" />
            <button
              className="btn-winui-secondary w-full inline-flex items-center justify-center"
              onClick={() => navigate('/devices')}
            >
              <Network className="h-4 w-4 mr-2" />
              查看所有设备
            </button>
            <button
              className="btn-winui-secondary w-full inline-flex items-center justify-center"
              onClick={() => navigate('/topology')}
            >
              <Activity className="h-4 w-4 mr-2" />
              查看网络拓扑
            </button>
            <button
              className="btn-winui-secondary w-full inline-flex items-center justify-center"
              onClick={() => navigate('/attacks')}
            >
              <Shield className="h-4 w-4 mr-2" />
              查看攻击记录
            </button>
          </div>
        </div>

        {/* Recent Devices */}
        <div className="card-winui p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--winui-text-primary)' }}>
            <Clock className="h-5 w-5" style={{ color: 'var(--winui-accent)' }} />
            最近设备
          </h2>
          <div className="space-y-2">
            {recentDevices.length === 0 ? (
              <p className="text-sm text-center py-4" style={{ color: 'var(--winui-text-tertiary)' }}>
                暂无设备
              </p>
            ) : (
              recentDevices.map((device) => (
                <div
                  key={device.mac}
                  className="flex items-center justify-between p-3 rounded-lg transition-colors"
                  style={{
                    backgroundColor: device.status === 'online' ? 'var(--winui-bg-tertiary)' : 'transparent',
                    border: '1px solid var(--winui-border-subtle)',
                  }}
                >
                  <div className="flex items-center space-x-3">
                    <div
                      className={clsx(
                        "w-2 h-2 rounded-full",
                        device.status === 'online' ? "bg-green-500" : "bg-gray-400"
                      )}
                    />
                    <div>
                      <p className="text-sm font-medium" style={{ color: 'var(--winui-text-primary)' }}>
                        {device.name || device.mac}
                      </p>
                      <p className="text-xs" style={{ color: 'var(--winui-text-secondary)' }}>
                        {device.ip} • {device.vendor || 'Unknown'}
                      </p>
                    </div>
                  </div>
                  {device.attack_status === 'running' && (
                    <AlertTriangle className="h-4 w-4 text-yellow-500" />
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Active Attacks */}
      {attackedDevices.length > 0 && (
        <div className="card-winui p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--winui-text-primary)' }}>
            <Shield className="h-5 w-5" style={{ color: '#dc2626' }} />
            活跃攻击 ({attackedDevices.length})
          </h2>
          <div className="space-y-2">
            {attackedDevices.map((device) => (
              <div
                key={device.mac}
                className="flex items-center justify-between p-3 rounded-lg"
                style={{
                  backgroundColor: 'rgba(220, 38, 38, 0.1)',
                  border: '1px solid rgba(220, 38, 38, 0.2)',
                }}
              >
                <div className="flex items-center space-x-3">
                  <Activity className="h-5 w-5 text-red-500" />
                  <div>
                    <p className="text-sm font-medium" style={{ color: 'var(--winui-text-primary)' }}>
                      {device.name || device.mac}
                    </p>
                    <p className="text-xs" style={{ color: 'var(--winui-text-secondary)' }}>
                      {device.ip} • {device.attack_status || 'Unknown'}
                    </p>
                  </div>
                </div>
                <button
                  className="btn-winui text-sm px-3 py-1"
                  onClick={async () => {
                    try {
                      await attackService.stopAttack(device.mac);
                      fetchDevices();
                    } catch (error) {
                      console.error('Failed to stop attack:', error);
                    }
                  }}
                >
                  停止
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
