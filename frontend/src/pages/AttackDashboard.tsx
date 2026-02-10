import React, { useEffect, useState, useCallback, useRef } from 'react';
import { deviceService } from '../lib/services/device';
import { attackService, AttackType } from '../lib/services/attack';
import { Device, DeviceStatus, DeviceType, AttackStatus } from '../types/device';
import { RefreshCw, ShieldAlert, Activity, Square, Clock, Zap, Terminal, ChevronDown, ChevronUp, Laptop, Smartphone, Router, Shield, Wifi, Network, Globe, Radio, Layers, Play, Search } from 'lucide-react';
import { clsx } from 'clsx';
import { useWebSocketEvent } from '../contexts/WebSocketContext';
import { WSEventType, ActiveDefenseLogEntry, ActiveDefenseStartedData, ActiveDefenseStoppedData } from '../types/websocket';
import toast from 'react-hot-toast';

// Attack type labels for display
const attackTypeLabels: Record<string, string> = {
  kick: 'WiFi Deauth',
  block: 'ARP Jam',
  dhcp_spoof: 'DHCP Spoof',
  dns_spoof: 'DNS Spoof',
  icmp_redirect: 'ICMP Redirect',
  port_scan: 'Port Scan',
  traffic_shape: 'Traffic Shape',
  mac_flood: 'MAC Flood',
  vlan_hop: 'VLAN Hop',
  beacon_flood: 'Beacon Flood',
  syn_flood: 'SYN Flood',
  udp_flood: 'UDP Flood',
  tcp_rst: 'TCP RST',
  arp_flood: 'ARP Flood',
};

// Attack type metadata for UI
const attackTypeMetadata: Record<AttackType, { label: string; icon: React.ReactNode; color: string }> = {
  [AttackType.KICK]: { label: 'WiFi Deauth', icon: <Zap className="h-4 w-4" />, color: '#ffaa44' },
  [AttackType.BLOCK]: { label: 'ARP Jam', icon: <Radio className="h-4 w-4" />, color: '#9a4dff' },
  [AttackType.DHCP_SPOOF]: { label: 'DHCP Spoof', icon: <Network className="h-4 w-4" />, color: '#0078d4' },
  [AttackType.DNS_SPOOF]: { label: 'DNS Spoof', icon: <Globe className="h-4 w-4" />, color: '#00bcf2' },
  [AttackType.ICMP_REDIRECT]: { label: 'ICMP Redirect', icon: <RefreshCw className="h-4 w-4" />, color: '#8764b8' },
  [AttackType.PORT_SCAN]: { label: 'Port Scan', icon: <Activity className="h-4 w-4" />, color: '#107c10' },
  [AttackType.TRAFFIC_SHAPE]: { label: 'Traffic Shape', icon: <Layers className="h-4 w-4" />, color: '#ff8c00' },
  [AttackType.MAC_FLOOD]: { label: 'MAC Flood', icon: <Network className="h-4 w-4" />, color: '#e81123' },
  [AttackType.VLAN_HOP]: { label: 'VLAN Hop', icon: <Layers className="h-4 w-4" />, color: '#737373' },
  [AttackType.BEACON_FLOOD]: { label: 'Beacon Flood', icon: <Wifi className="h-4 w-4" />, color: '#ffaa44' },
};

const DeviceIcon = ({ type }: { type: DeviceType }) => {
  switch (type) {
    case DeviceType.ROUTER:
      return <Router className="h-5 w-5 text-purple-500" />;
    case DeviceType.PC:
      return <Laptop className="h-5 w-5 text-blue-500" />;
    case DeviceType.MOBILE:
      return <Smartphone className="h-5 w-5 text-green-500" />;
    case DeviceType.IOT:
      return <Wifi className="h-5 w-5 text-orange-500" />;
    default:
      return <Shield className="h-5 w-5 text-gray-400" />;
  }
};

interface ActiveAttackInfo {
  mac: string;
  type: string;
  duration: number;
  intensity: number;
  start_time: string;
  device?: Device;
}

export const AttackDashboard: React.FC = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeAttacks, setActiveAttacks] = useState<Map<string, ActiveAttackInfo>>(new Map());
  const [logs, setLogs] = useState<ActiveDefenseLogEntry[]>([]);
  const [showLogs, setShowLogs] = useState(true);
  const [stoppingMacs, setStoppingMacs] = useState<Set<string>>(new Set());
  
  // Global attack settings
  const [globalIntensity, setGlobalIntensity] = useState(5);
  const [globalDuration, setGlobalDuration] = useState(60);
  const [selectedAttackType, setSelectedAttackType] = useState<AttackType>(AttackType.BLOCK);
  const [showTypeMenu, setShowTypeMenu] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [launchingMacs, setLaunchingMacs] = useState<Set<string>>(new Set());
  
  const typeMenuRef = useRef<HTMLDivElement>(null);

  // Close attack type menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (typeMenuRef.current && !typeMenuRef.current.contains(event.target as Node)) {
        setShowTypeMenu(false);
      }
    };

    if (showTypeMenu) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [showTypeMenu]);

  const fetchDevices = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await deviceService.getAll();
      setDevices(data);
      
      // Update active attacks with device info
      setActiveAttacks(prev => {
        const updated = new Map(prev);
        updated.forEach((attack, mac) => {
          const device = data.find(d => d.mac.toLowerCase() === mac.toLowerCase());
          if (device) {
            attack.device = device;
          }
        });
        return updated;
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

  // Handle active defense started
  useWebSocketEvent(WSEventType.ACTIVE_DEFENSE_STARTED, (data: ActiveDefenseStartedData) => {
    const device = devices.find(d => d.mac.toLowerCase() === data.mac.toLowerCase());
    setActiveAttacks(prev => {
      const updated = new Map(prev);
      updated.set(data.mac.toLowerCase(), {
        mac: data.mac,
        type: data.type,
        duration: data.duration,
        intensity: data.intensity,
        start_time: data.start_time,
        device,
      });
      return updated;
    });
    setLaunchingMacs(prev => {
      const updated = new Set(prev);
      updated.delete(data.mac.toLowerCase());
      return updated;
    });
    fetchDevices();
  });

  // Handle active defense stopped
  useWebSocketEvent(WSEventType.ACTIVE_DEFENSE_STOPPED, (data: ActiveDefenseStoppedData) => {
    setActiveAttacks(prev => {
      const updated = new Map(prev);
      updated.delete(data.mac.toLowerCase());
      return updated;
    });
    setStoppingMacs(prev => {
      const updated = new Set(prev);
      updated.delete(data.mac.toLowerCase());
      return updated;
    });
    fetchDevices();
  });

  // Handle active defense log with deduplication
  useWebSocketEvent(WSEventType.ACTIVE_DEFENSE_LOG, (data: ActiveDefenseLogEntry) => {
    setLogs(prev => {
      // Deduplicate: skip if same message+mac within last 2 seconds
      const isDuplicate = prev.some(log => 
        log.message === data.message && 
        log.mac === data.mac &&
        Math.abs(new Date(log.timestamp).getTime() - new Date(data.timestamp).getTime()) < 2000
      );
      
      if (isDuplicate) {
        return prev;
      }
      
      return [data, ...prev].slice(0, 100); // Keep last 100 logs
    });
  });

  // Legacy event listeners for backward compatibility
  useWebSocketEvent(WSEventType.ATTACK_STARTED, fetchDevices);
  useWebSocketEvent(WSEventType.ATTACK_STOPPED, fetchDevices);
  useWebSocketEvent(WSEventType.ATTACK_FINISHED, fetchDevices);

  // Get devices with running attacks (from device status)
  const devicesWithAttacks = devices.filter(d => d.attack_status === AttackStatus.RUNNING);
  
  // Merge with WebSocket-tracked attacks
  const allActiveAttacks = Array.from(activeAttacks.values());
  
  // Use the larger set (device status or tracked attacks)
  const displayAttacks = allActiveAttacks.length > 0 ? allActiveAttacks : 
    devicesWithAttacks.map(d => ({
      mac: d.mac,
      type: 'unknown',
      duration: 0,
      intensity: 0,
      start_time: '',
      device: d,
    }));

  // Filter devices for the list
  const filteredDevices = devices.filter(device => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      device.name?.toLowerCase().includes(query) ||
      device.ip.toLowerCase().includes(query) ||
      device.mac.toLowerCase().includes(query) ||
      device.vendor?.toLowerCase().includes(query) ||
      device.vendor_guess?.toLowerCase().includes(query)
    );
  });

  const handleStopAttack = async (mac: string) => {
    setStoppingMacs(prev => new Set(prev).add(mac.toLowerCase()));
    const toastId = toast.loading('Stopping attack...');
    
    try {
      await attackService.stopAttack(mac);
      toast.success('Attack stopped', { id: toastId });
      
      // Remove from active attacks
      setActiveAttacks(prev => {
        const updated = new Map(prev);
        updated.delete(mac.toLowerCase());
        return updated;
      });
      
      fetchDevices();
    } catch (error) {
      console.error('Failed to stop attack:', error);
      toast.error('Failed to stop attack', { id: toastId });
    } finally {
      setStoppingMacs(prev => {
        const updated = new Set(prev);
        updated.delete(mac.toLowerCase());
        return updated;
      });
    }
  };

  const handleLaunchAttack = async (device: Device) => {
    setLaunchingMacs(prev => new Set(prev).add(device.mac.toLowerCase()));
    const metadata = attackTypeMetadata[selectedAttackType];
    const toastId = toast.loading(`Launching ${metadata.label} on ${device.name || device.ip}...`);
    
    try {
      await attackService.startAttack(device.mac, selectedAttackType, globalDuration, globalIntensity);
      toast.success(`${metadata.label} attack started`, { id: toastId });
    } catch (error) {
      console.error('Failed to start attack:', error);
      toast.error('Failed to start attack', { id: toastId });
      setLaunchingMacs(prev => {
        const updated = new Set(prev);
        updated.delete(device.mac.toLowerCase());
        return updated;
      });
    }
  };

  const getLogLevelColor = (level: string) => {
    switch (level) {
      case 'success': return '#107c10';
      case 'warning': return '#f59e0b';
      case 'error': return '#d13438';
      default: return 'var(--winui-text-secondary)';
    }
  };

  const getLogLevelBg = (level: string) => {
    switch (level) {
      case 'success': return 'rgba(16, 124, 16, 0.1)';
      case 'warning': return 'rgba(245, 158, 11, 0.1)';
      case 'error': return 'rgba(209, 52, 56, 0.1)';
      default: return 'var(--winui-bg-tertiary)';
    }
  };

  const isDeviceUnderAttack = (mac: string) => {
    return activeAttacks.has(mac.toLowerCase()) || 
           devices.find(d => d.mac.toLowerCase() === mac.toLowerCase())?.attack_status === AttackStatus.RUNNING;
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-semibold flex items-center gap-2" style={{ color: 'var(--winui-text-primary)', letterSpacing: '-0.02em' }}>
            <ShieldAlert className="h-8 w-8" style={{ color: '#d13438' }} />
            Active Defense Operations
          </h1>
          <p className="mt-1 text-sm" style={{ color: 'var(--winui-text-secondary)' }}>
            Monitor and control active defense tasks in real-time.
          </p>
        </div>
        <button
          onClick={fetchDevices}
          className="btn-winui-secondary inline-flex items-center"
        >
          <RefreshCw className={clsx("h-4 w-4 mr-2", isLoading && "animate-spin")} />
          Refresh
        </button>
      </div>

      {/* Stats - WinUI3 Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
        <div className="card-winui overflow-hidden">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium truncate" style={{ color: 'var(--winui-text-secondary)' }}>Active Operations</dt>
            <dd className="mt-1 text-3xl font-semibold" style={{ color: displayAttacks.length > 0 ? '#d13438' : 'var(--winui-text-primary)' }}>
              {displayAttacks.length}
            </dd>
          </div>
        </div>
        <div className="card-winui overflow-hidden">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium truncate" style={{ color: 'var(--winui-text-secondary)' }}>Total Devices</dt>
            <dd className="mt-1 text-3xl font-semibold" style={{ color: 'var(--winui-text-primary)' }}>{devices.length}</dd>
          </div>
        </div>
        <div className="card-winui overflow-hidden">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium truncate" style={{ color: 'var(--winui-text-secondary)' }}>System Status</dt>
            <dd className="mt-1 text-3xl font-semibold flex items-center gap-2" style={{ color: '#107c10' }}>
              <Activity className="h-6 w-6" />
              Operational
            </dd>
          </div>
        </div>
      </div>

      {/* Active Attacks List - Enhanced */}
      <div className="card-winui overflow-hidden">
        <div className="px-4 py-5 border-b sm:px-6" style={{ borderColor: 'var(--winui-border-subtle)' }}>
          <h3 className="text-lg leading-6 font-semibold flex items-center gap-2" style={{ color: 'var(--winui-text-primary)' }}>
            <Zap className="h-5 w-5" style={{ color: '#ffaa44' }} />
            Targets Under Attack
          </h3>
        </div>
        <div className="divide-y" style={{ borderColor: 'var(--winui-border-subtle)' }}>
          {displayAttacks.length > 0 ? (
            displayAttacks.map((attack) => {
              const device = attack.device || devices.find(d => d.mac.toLowerCase() === attack.mac.toLowerCase());
              const isStopping = stoppingMacs.has(attack.mac.toLowerCase());
              
              return (
                <div
                  key={attack.mac}
                  className="px-4 py-4 sm:px-6 transition-colors duration-150"
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--winui-bg-tertiary)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center flex-1">
                      <div className="flex-shrink-0">
                        <div className="h-12 w-12 rounded-full flex items-center justify-center animate-pulse" style={{ backgroundColor: 'rgba(209, 52, 56, 0.15)' }}>
                          <ShieldAlert className="h-6 w-6" style={{ color: '#d13438' }} />
                        </div>
                      </div>
                      <div className="ml-4 flex-1">
                        <div className="flex items-center gap-3">
                          <span className="text-sm font-semibold" style={{ color: 'var(--winui-text-primary)' }}>
                            {device?.name || device?.alias || device?.model || device?.model_guess || 'Unknown Device'}
                          </span>
                          <span 
                            className="px-2 py-0.5 text-xs font-medium rounded"
                            style={{ 
                              backgroundColor: 'rgba(209, 52, 56, 0.1)',
                              color: '#d13438'
                            }}
                          >
                            {attackTypeLabels[attack.type] || attack.type || 'Active'}
                          </span>
                        </div>
                        <div className="mt-1 text-sm" style={{ color: 'var(--winui-text-secondary)' }}>
                          <span className="font-mono">{device?.ip || 'N/A'}</span>
                          <span className="mx-2">•</span>
                          <span className="font-mono text-xs">{attack.mac}</span>
                        </div>
                        <div className="mt-1 flex items-center gap-4 text-xs" style={{ color: 'var(--winui-text-tertiary)' }}>
                          {device?.vendor || device?.vendor_guess ? (
                            <span>{device.vendor || device.vendor_guess}</span>
                          ) : null}
                          {attack.duration > 0 && (
                            <span className="flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              {attack.duration}s duration
                            </span>
                          )}
                          {attack.intensity > 0 && (
                            <span>Intensity: {attack.intensity}/10</span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      <button
                        onClick={() => handleStopAttack(attack.mac)}
                        disabled={isStopping}
                        className={clsx(
                          "inline-flex items-center px-4 py-2 text-sm font-medium rounded-lg text-white transition-all duration-200",
                          isStopping && "opacity-50 cursor-not-allowed"
                        )}
                        style={{
                          backgroundColor: isStopping ? '#6b7280' : '#d13438',
                          minHeight: '36px'
                        }}
                        onMouseEnter={(e) => {
                          if (!isStopping) e.currentTarget.style.backgroundColor = '#c12a2e';
                        }}
                        onMouseLeave={(e) => {
                          if (!isStopping) e.currentTarget.style.backgroundColor = '#d13438';
                        }}
                      >
                        {isStopping ? (
                          <span className="h-4 w-4 border-2 border-current border-t-transparent rounded-full animate-spin mr-2" />
                        ) : (
                          <Square className="h-4 w-4 mr-2" />
                        )}
                        Stop Attack
                      </button>
                    </div>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="px-4 py-12 text-center">
              <ShieldAlert className="h-12 w-12 mx-auto mb-4" style={{ color: 'var(--winui-text-tertiary)' }} />
              <h3 className="text-lg font-semibold mb-1" style={{ color: 'var(--winui-text-primary)' }}>No Active Operations</h3>
              <p style={{ color: 'var(--winui-text-secondary)' }}>
                Select a device below to start an attack.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Real-time Logs */}
      <div className="card-winui overflow-hidden">
        <div 
          className="px-4 py-4 border-b sm:px-6 flex items-center justify-between cursor-pointer"
          style={{ borderColor: 'var(--winui-border-subtle)' }}
          onClick={() => setShowLogs(!showLogs)}
        >
          <h3 className="text-lg leading-6 font-semibold flex items-center gap-2" style={{ color: 'var(--winui-text-primary)' }}>
            <Terminal className="h-5 w-5" style={{ color: 'var(--winui-accent)' }} />
            Operation Logs
            {logs.length > 0 && (
              <span className="text-xs px-2 py-0.5 rounded-full" style={{ backgroundColor: 'var(--winui-bg-tertiary)', color: 'var(--winui-text-secondary)' }}>
                {logs.length}
              </span>
            )}
          </h3>
          {showLogs ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
        </div>
        
        {showLogs && (
          <div className="max-h-64 overflow-y-auto">
            {logs.length > 0 ? (
              <div className="divide-y" style={{ borderColor: 'var(--winui-border-subtle)' }}>
                {logs.map((log, index) => (
                  <div
                    key={`${log.timestamp}-${index}`}
                    className="px-4 py-2 text-sm font-mono"
                    style={{ backgroundColor: getLogLevelBg(log.level) }}
                  >
                    <div className="flex items-start gap-3">
                      <span className="text-xs whitespace-nowrap" style={{ color: 'var(--winui-text-tertiary)' }}>
                        {new Date(log.timestamp).toLocaleTimeString()}
                      </span>
                      <span 
                        className="flex-1"
                        style={{ color: getLogLevelColor(log.level) }}
                      >
                        {log.message}
                      </span>
                      {log.mac && (
                        <span className="text-xs whitespace-nowrap" style={{ color: 'var(--winui-text-tertiary)' }}>
                          {log.mac}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="px-4 py-8 text-center text-sm" style={{ color: 'var(--winui-text-secondary)' }}>
                No operation logs yet. Start an attack to see real-time logs.
              </div>
            )}
          </div>
        )}
      </div>

      {/* All Devices - Attack Control Center */}
      <div className="card-winui overflow-hidden">
        <div className="px-4 py-5 border-b sm:px-6" style={{ borderColor: 'var(--winui-border-subtle)' }}>
          <h3 className="text-lg leading-6 font-semibold" style={{ color: 'var(--winui-text-primary)' }}>
            All Network Devices
          </h3>
          <p className="mt-1 text-sm" style={{ color: 'var(--winui-text-secondary)' }}>
            Select a device to initiate an attack operation.
          </p>
        </div>

        {/* Attack Settings Bar */}
        <div className="px-4 py-4 border-b" style={{ borderColor: 'var(--winui-border-subtle)', backgroundColor: 'var(--winui-bg-secondary)' }}>
          <div className="flex flex-wrap items-center gap-6">
            {/* Attack Type Selector */}
            <div className="flex items-center gap-3">
              <label className="text-sm font-medium" style={{ color: 'var(--winui-text-secondary)' }}>Attack Type</label>
              <div className="relative" ref={typeMenuRef}>
                <button
                  onClick={() => setShowTypeMenu(!showTypeMenu)}
                  className="inline-flex items-center gap-2 px-3 py-2 text-sm rounded-lg border transition-colors"
                  style={{
                    backgroundColor: 'var(--winui-surface)',
                    borderColor: 'var(--winui-border-subtle)',
                    color: 'var(--winui-text-primary)',
                    minWidth: '160px'
                  }}
                >
                  <span style={{ color: attackTypeMetadata[selectedAttackType].color }}>
                    {attackTypeMetadata[selectedAttackType].icon}
                  </span>
                  <span className="flex-1 text-left">{attackTypeMetadata[selectedAttackType].label}</span>
                  <ChevronDown className="h-4 w-4" style={{ color: 'var(--winui-text-tertiary)' }} />
                </button>
                
                {showTypeMenu && (
                  <div
                    className="absolute top-full left-0 mt-1 w-56 rounded-lg z-50 py-1 max-h-72 overflow-y-auto"
                    style={{
                      backgroundColor: 'var(--winui-surface)',
                      boxShadow: 'var(--winui-shadow-lg)',
                      border: '1px solid var(--winui-border-subtle)'
                    }}
                  >
                    {Object.entries(attackTypeMetadata).map(([type, metadata]) => (
                      <button
                        key={type}
                        onClick={() => {
                          setSelectedAttackType(type as AttackType);
                          setShowTypeMenu(false);
                        }}
                        className="w-full text-left px-3 py-2 text-sm flex items-center gap-2 transition-colors"
                        style={{ 
                          color: 'var(--winui-text-primary)',
                          backgroundColor: selectedAttackType === type ? 'var(--winui-bg-tertiary)' : 'transparent'
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = 'var(--winui-bg-tertiary)';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = selectedAttackType === type ? 'var(--winui-bg-tertiary)' : 'transparent';
                        }}
                      >
                        <span style={{ color: metadata.color }}>{metadata.icon}</span>
                        <span>{metadata.label}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Intensity Slider */}
            <div className="flex items-center gap-3 flex-1 min-w-[200px] max-w-[320px]">
              <label className="text-sm font-medium whitespace-nowrap" style={{ color: 'var(--winui-text-secondary)' }}>
                Intensity
              </label>
              <div className="flex-1 flex items-center gap-3">
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={globalIntensity}
                  onChange={(e) => setGlobalIntensity(parseInt(e.target.value))}
                  className="flex-1 h-1 rounded-full appearance-none cursor-pointer"
                  style={{
                    background: `linear-gradient(to right, #d13438 0%, #d13438 ${(globalIntensity - 1) * 11.1}%, var(--winui-border-subtle) ${(globalIntensity - 1) * 11.1}%, var(--winui-border-subtle) 100%)`
                  }}
                />
                <span 
                  className="text-sm font-semibold w-8 text-center px-2 py-1 rounded"
                  style={{ 
                    backgroundColor: 'rgba(209, 52, 56, 0.1)',
                    color: '#d13438'
                  }}
                >
                  {globalIntensity}
                </span>
              </div>
            </div>

            {/* Duration */}
            <div className="flex items-center gap-3">
              <label className="text-sm font-medium whitespace-nowrap" style={{ color: 'var(--winui-text-secondary)' }}>
                Duration
              </label>
              <select
                value={globalDuration}
                onChange={(e) => setGlobalDuration(parseInt(e.target.value))}
                className="px-3 py-2 text-sm rounded-lg border"
                style={{
                  backgroundColor: 'var(--winui-surface)',
                  borderColor: 'var(--winui-border-subtle)',
                  color: 'var(--winui-text-primary)'
                }}
              >
                <option value={30}>30s</option>
                <option value={60}>60s</option>
                <option value={120}>2min</option>
                <option value={300}>5min</option>
                <option value={600}>10min</option>
              </select>
            </div>
          </div>
        </div>

        {/* Search Bar */}
        <div className="px-4 py-3 border-b" style={{ borderColor: 'var(--winui-border-subtle)' }}>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4" style={{ color: 'var(--winui-text-tertiary)' }} />
            <input
              type="text"
              placeholder="Search devices..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pr-4 py-2 text-sm rounded-lg border"
              style={{
                backgroundColor: 'var(--winui-surface)',
                borderColor: 'var(--winui-border-subtle)',
                color: 'var(--winui-text-primary)',
                paddingLeft: '42px'
              }}
            />
          </div>
        </div>

        {/* Device List */}
        <div className="max-h-[480px] overflow-y-auto">
          {filteredDevices.length > 0 ? (
            <div className="divide-y" style={{ borderColor: 'var(--winui-border-subtle)' }}>
              {filteredDevices.map((device) => {
                const underAttack = isDeviceUnderAttack(device.mac);
                const isLaunching = launchingMacs.has(device.mac.toLowerCase());
                const isStopping = stoppingMacs.has(device.mac.toLowerCase());
                
                return (
                  <div
                    key={device.mac}
                    className="px-4 py-3 sm:px-6 flex items-center gap-4 transition-colors duration-150"
                    style={{
                      backgroundColor: underAttack ? 'rgba(209, 52, 56, 0.05)' : 'transparent'
                    }}
                    onMouseEnter={(e) => {
                      if (!underAttack) e.currentTarget.style.backgroundColor = 'var(--winui-bg-tertiary)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = underAttack ? 'rgba(209, 52, 56, 0.05)' : 'transparent';
                    }}
                  >
                    {/* Device Icon */}
                    <div 
                      className={clsx(
                        "flex-shrink-0 h-10 w-10 rounded-full flex items-center justify-center",
                        underAttack && "animate-pulse"
                      )}
                      style={{ 
                        backgroundColor: underAttack ? 'rgba(209, 52, 56, 0.15)' : 'var(--winui-bg-tertiary)'
                      }}
                    >
                      {underAttack ? (
                        <ShieldAlert className="h-5 w-5" style={{ color: '#d13438' }} />
                      ) : (
                        <DeviceIcon type={device.type} />
                      )}
                    </div>

                    {/* Device Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium truncate" style={{ color: 'var(--winui-text-primary)' }}>
                          {device.name || device.alias || device.model || device.model_guess || 'Unknown Device'}
                        </span>
                        <div 
                          className={clsx(
                            "h-2 w-2 rounded-full flex-shrink-0",
                            device.status === DeviceStatus.ONLINE ? "bg-green-500" : "bg-gray-400"
                          )}
                        />
                        {underAttack && (
                          <span 
                            className="px-2 py-0.5 text-xs font-medium rounded flex-shrink-0"
                            style={{ 
                              backgroundColor: 'rgba(209, 52, 56, 0.1)',
                              color: '#d13438'
                            }}
                          >
                            Under Attack
                          </span>
                        )}
                      </div>
                      <div className="text-xs mt-0.5 flex items-center gap-2" style={{ color: 'var(--winui-text-secondary)' }}>
                        <span className="font-mono">{device.ip}</span>
                        <span>•</span>
                        <span className="font-mono text-[10px]" style={{ color: 'var(--winui-text-tertiary)' }}>{device.mac}</span>
                      </div>
                      <div className="text-xs mt-0.5" style={{ color: 'var(--winui-text-tertiary)' }}>
                        {device.vendor || device.vendor_guess || 'Unknown Vendor'}
                      </div>
                    </div>

                    {/* Action Button */}
                    <div className="flex-shrink-0">
                      {underAttack ? (
                        <button
                          onClick={() => handleStopAttack(device.mac)}
                          disabled={isStopping}
                          className={clsx(
                            "inline-flex items-center px-4 py-2 text-sm font-medium rounded-lg text-white transition-all duration-200",
                            isStopping && "opacity-50 cursor-not-allowed"
                          )}
                          style={{
                            backgroundColor: isStopping ? '#6b7280' : '#d13438',
                            minHeight: '36px'
                          }}
                          onMouseEnter={(e) => {
                            if (!isStopping) e.currentTarget.style.backgroundColor = '#c12a2e';
                          }}
                          onMouseLeave={(e) => {
                            if (!isStopping) e.currentTarget.style.backgroundColor = '#d13438';
                          }}
                        >
                          {isStopping ? (
                            <span className="h-4 w-4 border-2 border-current border-t-transparent rounded-full animate-spin mr-2" />
                          ) : (
                            <Square className="h-4 w-4 mr-2" />
                          )}
                          Stop
                        </button>
                      ) : (
                        <button
                          onClick={() => handleLaunchAttack(device)}
                          disabled={isLaunching}
                          className={clsx(
                            "inline-flex items-center px-4 py-2 text-sm font-medium rounded-lg text-white transition-all duration-200",
                            isLaunching && "opacity-50 cursor-not-allowed"
                          )}
                          style={{
                            backgroundColor: isLaunching ? '#6b7280' : '#ffaa44',
                            minHeight: '36px'
                          }}
                          onMouseEnter={(e) => {
                            if (!isLaunching) e.currentTarget.style.backgroundColor = '#e69a3e';
                          }}
                          onMouseLeave={(e) => {
                            if (!isLaunching) e.currentTarget.style.backgroundColor = '#ffaa44';
                          }}
                        >
                          {isLaunching ? (
                            <span className="h-4 w-4 border-2 border-current border-t-transparent rounded-full animate-spin mr-2" />
                          ) : (
                            <Play className="h-4 w-4 mr-2" />
                          )}
                          Attack
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="px-4 py-12 text-center">
              <Search className="h-12 w-12 mx-auto mb-4" style={{ color: 'var(--winui-text-tertiary)' }} />
              <h3 className="text-lg font-semibold mb-1" style={{ color: 'var(--winui-text-primary)' }}>
                {searchQuery ? 'No devices match your search' : 'No devices found'}
              </h3>
              <p style={{ color: 'var(--winui-text-secondary)' }}>
                {searchQuery ? 'Try a different search term.' : 'Run a network scan first to discover devices.'}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
