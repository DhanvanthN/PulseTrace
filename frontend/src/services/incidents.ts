import { fetchJson } from "@/services/api";
import type {
  Deployment,
  Incident,
  IncidentCorrelateResponse,
  IncidentDetail,
  IncidentEvent,
  IncidentEvidence,
  IncidentListResponse,
} from "@/types/incident";

export async function listIncidents(
  projectId: string,
  params: Record<string, string | number | undefined> = {}
): Promise<IncidentListResponse> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      query.set(key, String(value));
    }
  });
  return fetchJson<IncidentListResponse>(`/api/v1/projects/${projectId}/incidents?${query}`);
}

export async function createIncident(
  projectId: string,
  body: { title: string; description?: string; severity?: string; primary_service_id?: string }
): Promise<Incident> {
  return fetchJson<Incident>(`/api/v1/projects/${projectId}/incidents`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function correlateIncidents(projectId: string): Promise<IncidentCorrelateResponse> {
  return fetchJson<IncidentCorrelateResponse>(`/api/v1/projects/${projectId}/incidents/correlate`, {
    method: "POST",
  });
}

export async function getIncident(projectId: string, incidentId: string): Promise<IncidentDetail> {
  return fetchJson<IncidentDetail>(`/api/v1/projects/${projectId}/incidents/${incidentId}`);
}

export async function updateIncident(
  projectId: string,
  incidentId: string,
  body: Partial<{ title: string; description: string; severity: string; status: string }>
): Promise<Incident> {
  return fetchJson<Incident>(`/api/v1/projects/${projectId}/incidents/${incidentId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function getIncidentTimeline(
  projectId: string,
  incidentId: string
): Promise<{ items: IncidentEvent[] }> {
  return fetchJson(`/api/v1/projects/${projectId}/incidents/${incidentId}/timeline`);
}

export async function getIncidentEvidence(
  projectId: string,
  incidentId: string
): Promise<{ items: IncidentEvidence[] }> {
  return fetchJson(`/api/v1/projects/${projectId}/incidents/${incidentId}/evidence`);
}

export async function addIncidentNote(
  projectId: string,
  incidentId: string,
  content: string
): Promise<IncidentEvent> {
  return fetchJson<IncidentEvent>(`/api/v1/projects/${projectId}/incidents/${incidentId}/notes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
}

export async function listDeployments(projectId: string): Promise<{ items: Deployment[]; total: number }> {
  return fetchJson(`/api/v1/projects/${projectId}/deployments?limit=50`);
}