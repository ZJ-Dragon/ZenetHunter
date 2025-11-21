export interface OOBEConfig {
  is_configured: boolean;
  network_interface?: string;
  target_subnets?: string[];
  scan_interval?: number;
  default_policy?: 'monitor' | 'block_unknown';
}

export interface OOBESetupRequest {
  target_subnets: string[];
  scan_interval: number;
  default_policy: 'monitor' | 'block_unknown';
  admin_password?: string; // Optional if we enforce reset
}

