export interface OOBEStatus {
  admin_exists: boolean;
  first_run_completed: boolean;
}

export interface OOBERegisterRequest {
  username: string;
  password: string;
}

export interface OOBERegisterResponse {
  access_token: string;
  token_type: string;
}

export interface OOBEAcknowledgeRequest {
  acknowledged: boolean;
}
