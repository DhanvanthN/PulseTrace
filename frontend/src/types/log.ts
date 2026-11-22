export interface LogBatch {
  id: string;
  project_id: string;
  uploaded_by: string | null;
  filename: string;
  file_format: string;
  status: string;
  total_records: number;
  processed_records: number;
  failed_records: number;
  error_summary: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface LogBatchListResponse {
  items: LogBatch[];
  total: number;
  skip: number;
  limit: number;
}

export interface LogEntry {
  id: string;
  project_id: string;
  service_id: string | null;
  service_name: string | null;
  batch_id: string;
  timestamp: string;
  level: string;
  message: string;
  trace_id: string | null;
  request_id: string | null;
  metadata: Record<string, unknown>;
  fingerprint: string;
  created_at: string;
}

export interface LogListResponse {
  items: LogEntry[];
  total: number;
  skip: number;
  limit: number;
}

export interface Service {
  id: string;
  project_id: string;
  name: string;
  service_type: string;
  environment: string;
  description: string | null;
  created_at: string;
}

export interface ServiceListResponse {
  items: Service[];
}

export interface LogSearchParams {
  start_time?: string;
  end_time?: string;
  level?: string;
  service_id?: string;
  trace_id?: string;
  request_id?: string;
  keyword?: string;
  batch_id?: string;
  skip?: number;
  limit?: number;
}