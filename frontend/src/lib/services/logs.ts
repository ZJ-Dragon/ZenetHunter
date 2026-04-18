import { api } from '../api';

export interface SystemLog {
  id?: string;
  timestamp: string;
  level: string;
  module: string;
  message: string;
  correlation_id?: string;
  device_mac?: string;
  context?: Record<string, unknown>;
}

export interface CapabilityState {
  available: boolean;
  reason: string | null;
  metadata: Record<string, unknown>;
}

export interface RuntimeDiagnostics {
  python_executable: string;
  python_version: string;
  platform: string;
  is_root: boolean;
  environment_kind: string;
  environment_name: string | null;
  virtual_env: string | null;
  conda_env: string | null;
  dependencies_ready: boolean;
  missing_modules: string[];
  modules: Record<
    string,
    {
      name: string;
      import_name: string;
      available: boolean;
      error: string | null;
    }
  >;
}

export interface SystemInfo {
  platform: string;
  platform_name?: string;
  python_version: string;
  app_version: string;
  app_env: string;
  database_url?: string;
  docker: boolean;
  capabilities: {
    scapy_available: boolean;
    root_permissions: boolean;
    network_scan_available: boolean;
  };
  capability_state: Record<string, CapabilityState>;
  runtime?: RuntimeDiagnostics;
}

export interface ScanConfig {
  scan_range: string;
  scan_timeout_sec: number;
  scan_concurrency: number;
  scan_interval_sec: number | null;
  features: {
    mdns: boolean;
    ssdp: boolean;
    nbns: boolean;
    snmp: boolean;
    fingerbank: boolean;
  };
  capability_state?: Record<string, CapabilityState>;
}

type RawSystemInfo = Omit<SystemInfo, 'capabilities' | 'capability_state'> & {
  capabilities?: Record<string, unknown> & {
    scapy?: boolean;
    scapy_available?: boolean;
    root_permissions?: boolean;
    network_scan_available?: boolean;
  };
  capability_state?: Record<string, CapabilityState>;
};

interface RawScanConfig extends ScanConfig {
  capability_state?: Record<string, CapabilityState>;
}

const toOptionalBoolean = (value: unknown): boolean | undefined => {
  if (value === true) {
    return true;
  }
  if (value === false) {
    return false;
  }
  return undefined;
};

const normalizeCapabilities = (
  capabilities: RawSystemInfo['capabilities'],
  capabilityState: RawSystemInfo['capability_state']
) => {
  const scapyAvailable =
    capabilityState?.scapy_import?.available ??
    toOptionalBoolean(capabilities?.scapy) ??
    toOptionalBoolean(capabilities?.scapy_available);

  const rootPermissions =
    capabilityState?.root_permissions?.available ??
    toOptionalBoolean(capabilities?.root_permissions);

  const networkScanAvailable =
    capabilityState?.arp_sweep?.available ??
    capabilityState?.icmp_ping?.available ??
    capabilityState?.tcp_probe?.available ??
    toOptionalBoolean(capabilities?.network_scan_available);

  return {
    scapy_available: Boolean(scapyAvailable),
    root_permissions: Boolean(rootPermissions),
    network_scan_available: Boolean(networkScanAvailable),
  };
};

export const logsService = {
  getLogs: async (limit: number = 100): Promise<SystemLog[]> => {
    const response = await api.get<SystemLog[]>('/logs', {
      params: { limit },
    });
    return response.data;
  },

  getSystemInfo: async (): Promise<SystemInfo> => {
    const response = await api.get<RawSystemInfo>('/logs/system-info');
    const payload = response.data;
    return {
      ...payload,
      capabilities: normalizeCapabilities(
        payload.capabilities,
        payload.capability_state
      ),
      capability_state: payload.capability_state || {},
    };
  },

  getScanConfig: async (): Promise<ScanConfig> => {
    const response = await api.get<RawScanConfig>('/config/scan');
    return response.data;
  },

  shutdownServer: async (): Promise<{ status: string; message: string }> => {
    const response = await api.post<{ status: string; message: string }>(
      '/shutdown'
    );
    return response.data;
  },

  forceShutdownServer: async (): Promise<{
    status: string;
    message: string;
  }> => {
    const response = await api.post<{ status: string; message: string }>(
      '/force-shutdown'
    );
    return response.data;
  },

  replaySystem: async (): Promise<void> => {
    await api.post('/config/replay');
  },
};
