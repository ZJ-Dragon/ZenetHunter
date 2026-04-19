import { api } from '../api';

export interface ScanResult {
  id: string;
  status: string;
  devices_found: number;
  started_at?: string;
  completed_at?: string | null;
  error?: string | null;
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

  getScanStatus: async (): Promise<ScanResult> => {
    const response = await api.get<ScanResult>('/scan/status');
    return response.data;
  },
};
