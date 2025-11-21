import { api } from '../api';
import { Device, DeviceType, DeviceStatus } from '../../types/device';

export const deviceService = {
  getAll: async (): Promise<Device[]> => {
    const response = await api.get<Device[]>('/devices');
    return response.data;
  },

  getOne: async (mac: string): Promise<Device> => {
    const response = await api.get<Device>(`/devices/${mac}`);
    return response.data;
  },

  update: async (mac: string, data: Partial<Device>): Promise<Device> => {
    const response = await api.put<Device>(`/devices/${mac}`, data);
    return response.data;
  },

  updateType: async (mac: string, type: DeviceType): Promise<Device> => {
    // Backend likely expects { type: "..." }
    return deviceService.update(mac, { type });
  },

  updateStatus: async (mac: string, status: DeviceStatus): Promise<Device> => {
    return deviceService.update(mac, { status });
  },

  delete: async (mac: string): Promise<void> => {
    await api.delete(`/devices/${mac}`);
  }
};

