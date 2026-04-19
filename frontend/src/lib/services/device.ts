import { api } from '../api';
import { Device } from '../../types/device';

export interface ManualLabelRequest {
  name_manual: string | null;
  vendor_manual: string | null;
}

export interface ManualLabelResponse {
  device: Device;
  fingerprint_key: string;
  message: string;
}

export interface DeviceMetadataUpdate {
  alias?: string | null;
  tags?: string[] | null;
}

export interface RecognitionOverrideRequest {
  vendor?: string | null;
  model?: string | null;
  device_type?: string | null;
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

  updateMetadata: async (
    mac: string,
    data: DeviceMetadataUpdate
  ): Promise<Device> => {
    const response = await api.patch<Device>(`/devices/${mac}`, data);
    return response.data;
  },

  overrideRecognition: async (
    mac: string,
    payload: RecognitionOverrideRequest
  ): Promise<Device> => {
    const response = await api.post<Device>(
      `/devices/${mac}/recognition/override`,
      payload
    );
    return response.data;
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
