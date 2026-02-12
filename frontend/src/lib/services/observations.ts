import { api } from '../api';
import { ProbeObservationList, ProbeObservation } from '../../types/observation';

export const observationService = {
  async listByDevice(mac: string, limit = 20, since?: string): Promise<ProbeObservation[]> {
    const params: Record<string, string | number> = { limit };
    if (since) params.since = since;
    const response = await api.get<ProbeObservationList>(`/devices/${mac}/observations`, { params });
    return response.data.items;
  },

  async listByScan(scanRunId: string): Promise<ProbeObservation[]> {
    const response = await api.get<ProbeObservationList>(`/scan/${scanRunId}/observations`);
    return response.data.items;
  },

  async exportDeviceNdjson(mac: string, limit = 100): Promise<string> {
    const response = await api.get<string>(`/devices/${mac}/observations`, {
      params: { format: 'ndjson', limit },
      responseType: 'text',
    });
    return response.data;
  },
};
