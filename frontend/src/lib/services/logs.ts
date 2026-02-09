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

export interface SystemInfo {
  platform: string;
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
    active_probe?: boolean;
    http_ident?: boolean;
    printer_ident?: boolean;
  };
}

export const logsService = {
  getLogs: async (limit: number = 100): Promise<SystemLog[]> => {
    const response = await api.get<SystemLog[]>('/logs', {
      params: { limit },
    });
    return response.data;
  },

  getSystemInfo: async (): Promise<SystemInfo> => {
    const response = await api.get<SystemInfo>('/logs/system-info');
    return response.data;
  },

  getScanConfig: async (): Promise<ScanConfig> => {
    const response = await api.get<ScanConfig>('/config/scan');
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
};
