import { api } from '../api';

export interface SystemLog {
  id?: string;
  timestamp: string;
  level: string;
  module: string;
  message: string;
  correlation_id?: string;
  device_mac?: string;
  context?: Record<string, any>;
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
};
