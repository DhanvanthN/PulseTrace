export type Anomaly = {
  id: string;
  project_id: string;
  service_id: string | null;
  anomaly_type: string;
  severity: string;
  score: number;
  description: string;
  start_time: string;
  end_time: string;
  detection_method: string;
  evidence: Record<string, unknown>;
  created_at: string;
};

export type AnomalyListResponse = {
  items: Anomaly[];
  total: number;
  skip: number;
  limit: number;
  severity_counts: Record<string, number>;
};

export type AnalysisRunResponse = {
  status: string;
  message: string;
  anomalies_created: number;
  anomalies_detected: number;
  clusters_created: number;
  cluster_memberships: number;
  noise_logs: number;
  logs_analyzed: number;
  window_start: string | null;
  window_end: string | null;
  methods: string[];
};

export type LogCluster = {
  id: string;
  project_id: string;
  cluster_label: string;
  description: string;
  representative_message: string;
  algorithm: string;
  log_count: number;
  first_seen: string | null;
  last_seen: string | null;
  created_at: string;
};

export type LogClusterDetail = LogCluster & {
  logs: Array<{
    id: string;
    timestamp: string;
    level: string;
    message: string;
    service_id: string | null;
  }>;
};

export type LogClusterListResponse = {
  items: LogCluster[];
  total: number;
  skip: number;
  limit: number;
};