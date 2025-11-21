import { api } from '../api';
import { OOBEConfig, OOBESetupRequest } from '../../types/config';

export const configService = {
  getStatus: async (): Promise<OOBEConfig> => {
    // This endpoint checks if system is already initialized
    const response = await api.get<OOBEConfig>('/config/status');
    return response.data;
  },

  setup: async (data: OOBESetupRequest): Promise<void> => {
    await api.post('/config/setup', data);
  },
};
