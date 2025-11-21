export type WebSocketEvent<T = any> = {
  event: string;
  data: T;
};

export enum WSEventType {
  // Device Events
  DEVICE_ADDED = 'deviceAdded',
  DEVICE_STATUS_CHANGED = 'deviceStatusChanged',
  DEVICE_UPDATED = 'deviceUpdated',

  // Scan Events
  SCAN_STARTED = 'scanStarted',
  SCAN_COMPLETED = 'scanCompleted',

  // Attack Events
  ATTACK_STARTED = 'attackStarted',
  ATTACK_STOPPED = 'attackStopped',
  ATTACK_FINISHED = 'attackFinished',

  // Log Events
  LOG_ADDED = 'logAdded',
}
