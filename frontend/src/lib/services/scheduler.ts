import { api } from '../api';

export interface StrategyFeedback {
  device_mac: string;
  strategy: {
    type: 'defense' | 'attack';
    strategy_id: string;
  };
  effect_score: number; // 0.0 to 1.0
  resource_cost: number; // 0.0 to 1.0
  duration_seconds: number;
  device_response: string;
}

export const schedulerService = {
  executeStrategy: async (mac: string, maxStrategies: number = 3) => {
    const response = await api.post(`/devices/${mac}/scheduler/execute`, null, {
      params: { max_strategies: maxStrategies },
    });
    return response.data;
  },

  simulateStrategy: async (mac: string) => {
    const response = await api.post(`/devices/${mac}/scheduler/simulate`);
    return response.data;
  },

  submitFeedback: async (mac: string, feedback: StrategyFeedback) => {
    const response = await api.post(`/devices/${mac}/scheduler/feedback`, feedback);
    return response.data;
  },
};
