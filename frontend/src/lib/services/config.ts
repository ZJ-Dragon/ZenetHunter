import { api } from '../api';
import {
  OOBEStatus,
  OOBERegisterRequest,
  OOBERegisterResponse,
  OOBEAcknowledgeRequest,
} from '../../types/config';

export const configService = {
  getStatus: async (): Promise<OOBEStatus> => {
    const response = await api.get<OOBEStatus>('/config/status');
    return response.data;
  },

  register: async (data: OOBERegisterRequest): Promise<OOBERegisterResponse> => {
    const response = await api.post<OOBERegisterResponse>('/config/register', data);
    return response.data;
  },

  acknowledge: async (data: OOBEAcknowledgeRequest): Promise<void> => {
    await api.post('/config/acknowledge', data);
  },
};
