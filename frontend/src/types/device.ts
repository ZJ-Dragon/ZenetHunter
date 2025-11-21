export enum DeviceType {
  UNKNOWN = 'unknown',
  ROUTER = 'router',
  PC = 'pc',
  MOBILE = 'mobile',
  IOT = 'iot',
}

export enum DeviceStatus {
  ONLINE = 'online',
  OFFLINE = 'offline',
  BLOCKED = 'blocked',
}

export enum AttackStatus {
  IDLE = 'idle',
  RUNNING = 'running',
  STOPPED = 'stopped',
  FAILED = 'failed',
}

export interface Device {
  mac: string;
  ip: string;
  name: string | null;
  vendor: string | null;
  type: DeviceType;
  status: DeviceStatus;
  attack_status: AttackStatus;
  first_seen: string;
  last_seen: string;
}

export interface DeviceFilter {
  search: string;
  status?: DeviceStatus | 'all';
  type?: DeviceType | 'all';
}

