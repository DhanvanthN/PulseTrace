import { fetchJson } from "@/services/api";
import type { ServiceListResponse } from "@/types/log";

export function listProjectServices(projectId: string): Promise<ServiceListResponse> {
  return fetchJson<ServiceListResponse>(`/api/v1/projects/${projectId}/services`);
}