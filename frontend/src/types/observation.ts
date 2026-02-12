export interface KeywordHit {
  rule_id: string;
  matched_token: string;
  confidence_delta: number;
  infer?: {
    vendor?: string;
    product?: string;
    category?: string;
    os?: string;
  };
  infer_summary?: string;
  priority?: number;
  notes?: string;
}

export interface ProbeObservation {
  id: string;
  device_mac: string;
  scan_run_id?: string | null;
  protocol: string;
  timestamp: string;
  key_fields: Record<string, unknown>;
  keywords: string[];
  keyword_hits: KeywordHit[];
  raw_summary?: string | null;
  redaction_level: string;
}

export interface ProbeObservationList {
  items: ProbeObservation[];
  total: number;
}
