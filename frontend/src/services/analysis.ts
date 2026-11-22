import { fetchJson } from "@/services/api";
import type {
  AnalysisRunResponse,
  Anomaly,
  AnomalyListResponse,
  LogClusterDetail,
  LogClusterListResponse,
} from "@/types/analysis";

export async function runAnalysis(
  projectId: string,
  body: { service_id?: string } = {}
): Promise<AnalysisRunResponse> {
  return fetchJson<AnalysisRunResponse>(`/api/v1/projects/${projectId}/analysis/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export type AnomalySearchParams = {
  severity?: string;
  service_id?: string;
  anomaly_type?: string;
  start_time?: string;
  end_time?: string;
  skip?: number;
  limit?: number;
};

export async function listAnomalies(
  projectId: string,
  params: AnomalySearchParams = {}
): Promise<AnomalyListResponse> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      query.set(key, String(value));
    }
  });
  return fetchJson<AnomalyListResponse>(`/api/v1/projects/${projectId}/anomalies?${query}`);
}

export async function getAnomaly(projectId: string, anomalyId: string): Promise<Anomaly> {
  return fetchJson<Anomaly>(`/api/v1/projects/${projectId}/anomalies/${anomalyId}`);
}

export type ClusterSearchParams = {
  search?: string;
  min_log_count?: number;
  skip?: number;
  limit?: number;
};

export async function listClusters(
  projectId: string,
  params: ClusterSearchParams = {}
): Promise<LogClusterListResponse> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      query.set(key, String(value));
    }
  });
  return fetchJson<LogClusterListResponse>(`/api/v1/projects/${projectId}/clusters?${query}`);
}

export async function getCluster(projectId: string, clusterId: string): Promise<LogClusterDetail> {
  return fetchJson<LogClusterDetail>(`/api/v1/projects/${projectId}/clusters/${clusterId}`);
}