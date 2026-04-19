export type WebSocketEvent<T = unknown> = {
  event: string;
  data: T;
};

export enum WSEventType {
  // Device Events
  DEVICE_ADDED = 'deviceAdded',
  DEVICE_STATUS_CHANGED = 'deviceStatusChanged',
  DEVICE_UPDATED = 'deviceUpdated',
  DEVICE_RECOGNITION_UPDATED = 'deviceRecognitionUpdated',
  RECOGNITION_OVERRIDDEN = 'recognitionOverridden',
  DEVICE_LIST_CLEARED = 'deviceListCleared',

  // Scan Events
  SCAN_STARTED = 'scanStarted',
  SCAN_COMPLETED = 'scanCompleted',
  SCAN_PROGRESS = 'scanProgress',
  SCAN_LOG = 'scanLog',

  // Active Defense Events (from backend)
  ACTIVE_DEFENSE_STARTED = 'activeDefenseStarted',
  ACTIVE_DEFENSE_STOPPED = 'activeDefenseStopped',
  ACTIVE_DEFENSE_LOG = 'activeDefenseLog',

  // Legacy Attack Events (for backward compatibility)
  ATTACK_STARTED = 'attackStarted',
  ATTACK_STOPPED = 'attackStopped',
  ATTACK_FINISHED = 'attackFinished',

  // Log Events
  LOG_ADDED = 'logAdded',
  PING = 'ping',
  ERROR = 'error',
}

// Active Defense Log Entry
export interface ActiveDefenseLogEntry {
  level: 'info' | 'success' | 'warning' | 'error';
  message: string;
  mac: string;
  operation_type?: string;
  timestamp: string;
  error?: string;
}

// Active Defense Started Event Data
export interface ActiveDefenseStartedData {
  mac: string;
  type: string;
  duration: number;
  intensity: number;
  start_time: string;
}

// Active Defense Stopped Event Data
export interface ActiveDefenseStoppedData {
  mac: string;
  timestamp: string;
}
