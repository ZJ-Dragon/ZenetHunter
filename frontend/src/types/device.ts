import { KeywordHit } from './observation';

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

export interface ManualProfile {
  id: number;
  manual_name: string | null;
  manual_vendor: string | null;
  fingerprint_key: string | null;
  match_keys: Record<string, unknown>;
  mac: string | null;
  ip_hint: string | null;
  keywords: string[];
  created_at: string;
  updated_at: string;
}

export interface Device {
  mac: string;
  ip: string;
  name: string | null;
  vendor: string | null;
  model: string | null;
  type: DeviceType;
  status: DeviceStatus;
  attack_status: AttackStatus;
  defense_status: DefenseStatus;
  active_defense_policy: string | null;
  first_seen: string;
  last_seen: string;
  tags: string[] | null;
  alias: string | null;
  // Recognition fields
  vendor_guess: string | null;
  model_guess: string | null;
  recognition_confidence: number | null;
  recognition_evidence: {
    sources: string[];
    matched_fields: string[];
    weights: Record<string, number>;
    keyword_hits?: KeywordHit[];
    dictionary_infer?: {
      vendor?: string;
      product?: string;
      category?: string;
      os?: string;
    };
    confidence_breakdown?: {
      active_probe?: number;
      oui: number;
      dhcp: number;
      external_vendor?: number;
      external_device?: number;
      dictionary_delta?: number;
      combined: number;
    };
  } | null;
  // Manual override fields (legacy for compatibility)
  name_manual: string | null;
  vendor_manual: string | null;
  manual_override_at: string | null;
  manual_override_by: string | null;
  manual_profile_id?: number | null;
  manual_profile?: ManualProfile | null;
  display_name?: string | null;
  display_vendor?: string | null;
  name_auto?: string | null;
  vendor_auto?: string | null;
}

export interface DeviceFilter {
  search: string;
  status?: DeviceStatus | 'all';
  type?: DeviceType | 'all';
}
