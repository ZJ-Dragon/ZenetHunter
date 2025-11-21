import { api } from '../api';

export enum AttackType {
  KICK = 'kick',
  BLOCK = 'block',
}

export interface AttackRequest {
  type: AttackType;
  duration: number;
}

export const attackService = {
  startAttack: async (mac: string, type: AttackType = AttackType.KICK, duration: number = 60) => {
    const response = await api.post(`/attack/start/${mac}`, { type, duration });
    return response.data;
  },

  stopAttack: async (mac: string) => {
    const response = await api.post(`/attack/stop/${mac}`);
    return response.data;
  },
};

