export type Incident = {
  id: string;
  project_id: string;
  primary_service_id: string | null;
  title: string;
  description: string;
  severity: string;
  status: string;
  started_at: string;
  last_activity_at: string;
  resolved_at: string | null;
  created_at: string;
  updated_at: string;
};

export type IncidentDetail = Incident & {
  events_count: number;
  evidence_count: number;
};

export type IncidentListResponse = {
  items: Incident[];
  total: number;
  skip: number;
  limit: number;
  status_counts: Record<string, number>;
  severity_counts: Record<string, number>;
};

export type IncidentEvent = {
  id: string;
  incident_id: string;
  event_type: string;
  description: string;
  event_timestamp: string;
  metadata: Record<string, unknown>;
  created_at: string;
};

export type IncidentEvidence = {
  id: string;
  incident_id: string;
  log_id: string | null;
  anomaly_id: string | null;
  cluster_id: string | null;
  evidence_type: string;
  explanation: string;
  created_at: string;
};

export type Deployment = {
  id: string;
  project_id: string;
  service_id: string | null;
  version: string;
  change_type: string;
  description: string;
  configuration_diff: Record<string, unknown>;
  deployed_at: string;
  created_at: string;
};

export type IncidentCorrelateResponse = {
  status: string;
  message: string;
  incidents_created: number;
  incidents_updated: number;
  anomalies_processed: number;
};