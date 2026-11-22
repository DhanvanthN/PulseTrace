import { resolveApiBaseUrl } from "@/config/api-base";
import { fetchJson } from "@/services/api";
import { buildRequestHeaders } from "@/services/auth-headers";
import type {
  LogBatch,
  LogBatchListResponse,
  LogEntry,
  LogListResponse,
  LogSearchParams,
} from "@/types/log";

function toQuery(params: LogSearchParams): string {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      search.set(key, String(value));
    }
  });
  return search.toString();
}

export async function uploadLogs(
  projectId: string,
  file: File,
  serviceId?: string
): Promise<LogBatch> {
  const formData = new FormData();
  formData.append("file", file);
  if (serviceId) {
    formData.append("service_id", serviceId);
  }

  const API_BASE_URL = resolveApiBaseUrl();
  const response = await fetch(`${API_BASE_URL}/api/v1/projects/${projectId}/logs/upload`, {
    method: "POST",
    credentials: "include",
    headers: buildRequestHeaders(undefined, { Accept: "application/json" }),
    body: formData,
  });

  if (!response.ok) {
    let detail = `Upload failed (${response.status})`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) detail = payload.detail;
    } catch {
      // ignore
    }
    throw new Error(detail);
  }
  return response.json() as Promise<LogBatch>;
}

export function searchLogs(
  projectId: string,
  params: LogSearchParams
): Promise<LogListResponse> {
  const query = toQuery(params);
  return fetchJson<LogListResponse>(`/api/v1/projects/${projectId}/logs?${query}`);
}

export function getLog(projectId: string, logId: string): Promise<LogEntry> {
  return fetchJson<LogEntry>(`/api/v1/projects/${projectId}/logs/${logId}`);
}

export function listLogBatches(
  projectId: string,
  skip = 0,
  limit = 20
): Promise<LogBatchListResponse> {
  const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
  return fetchJson<LogBatchListResponse>(
    `/api/v1/projects/${projectId}/logs/batches?${params}`
  );
}