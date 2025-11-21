import { api } from '../api';

export interface ScanResult {
  id: string;
  status: string;
  devices_found: number;
}

export const scanService = {
  startScan: async (target_subnets: string[] = []) => {
    const response = await api.post('/scan/start', { target_subnets });
    return response.data;
  },

  getScanStatus: async (scanId: string) => {
    const response = await api.get(`/scan/${scanId}`);
    return response.data;
  },
};

