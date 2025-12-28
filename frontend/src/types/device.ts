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

export enum DefenseStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  PENDING = 'pending',
  ERROR = 'error',
}

export interface Device {
  mac: string;
  ip: string;
  name: string | null;
  vendor: string | null;
  type: DeviceType;
  status: DeviceStatus;
  attack_status: AttackStatus;
  defense_status: DefenseStatus;
  active_defense_policy: string | null;
  first_seen: string;
  last_seen: string;
}

export interface DeviceFilter {
  search: string;
  status?: DeviceStatus | 'all';
  type?: DeviceType | 'all';
}
