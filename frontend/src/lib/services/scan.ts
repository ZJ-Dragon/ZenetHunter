import { api } from '../api';

export interface ScanResult {
  id: string;
  status: string;
  devices_found: number;
}

export interface ScanRequest {
  type?: 'quick' | 'full' | 'passive';
  target_subnets?: string[];
}

export const scanService = {
  startScan: async (request: ScanRequest = {}) => {
    // Default to quick scan if not specified
    const scanRequest = {
      type: request.type || 'quick',
      target_subnets: request.target_subnets || null,
    };
    const response = await api.post('/scan/start', scanRequest);
    return response.data;
  },

  getScanStatus: async (scanId: string) => {
    const response = await api.get(`/scan/${scanId}`);
    return response.data;
  },
};
