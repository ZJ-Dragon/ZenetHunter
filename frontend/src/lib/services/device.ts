import { api } from '../api';
import { Device, DeviceType, DeviceStatus } from '../../types/device';

export interface ManualLabelRequest {
  name_manual: string | null;
  vendor_manual: string | null;
}

export interface ManualLabelResponse {
  device: Device;
  fingerprint_key: string;
  message: string;
}

export const deviceService = {
  getAll: async (): Promise<Device[]> => {
    const response = await api.get<Device[]>('/devices');
    return response.data;
  },

  getDevices: async (): Promise<Device[]> => {
    return deviceService.getAll();
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
  },

  /**
   * Update manual labels for a device (name and vendor)
   * @param mac Device MAC address
   * @param labels Manual label data
   */
  updateManualLabel: async (mac: string, labels: ManualLabelRequest): Promise<ManualLabelResponse> => {
    const response = await api.put<ManualLabelResponse>(`/devices/${mac}/manual-label`, labels);
    return response.data;
  },

  /**
   * Clear manual labels from a device
   * @param mac Device MAC address
   */
  clearManualLabel: async (mac: string): Promise<Device> => {
    const response = await api.delete<Device>(`/devices/${mac}/manual-label`);
    return response.data;
  },
};
