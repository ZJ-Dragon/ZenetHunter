import { api } from '../api';
import { NetworkTopology } from '../../types/topology';

export const topologyService = {
  getTopology: async (): Promise<NetworkTopology> => {
    // baseURL already includes /api
    const response = await api.get<NetworkTopology>('/topology');
    return response.data;
  },
};
