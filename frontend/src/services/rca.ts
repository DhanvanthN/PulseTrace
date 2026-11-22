import { fetchJson } from "@/services/api";
import type { InvestigationReportResponse, RCAInvestigateResponse, RootCauseListResponse, RootCauseCandidate } from "@/types/rca";

export async function runInvestigation(projectId: string, incidentId: string): Promise<RCAInvestigateResponse> {
  return fetchJson<RCAInvestigateResponse>(
    `/api/v1/projects/${projectId}/incidents/${incidentId}/investigate`,
    { method: "POST" }
  );
}

export async function listRootCauses(projectId: string, incidentId: string): Promise<RootCauseListResponse> {
  return fetchJson<RootCauseListResponse>(
    `/api/v1/projects/${projectId}/incidents/${incidentId}/root-causes`
  );
}

export async function getRootCause(
  projectId: string,
  incidentId: string,
  candidateId: string
): Promise<RootCauseCandidate> {
  return fetchJson<RootCauseCandidate>(
    `/api/v1/projects/${projectId}/incidents/${incidentId}/root-causes/${candidateId}`
  );
}

export async function getInvestigationReport(
  projectId: string,
  incidentId: string
): Promise<InvestigationReportResponse> {
  return fetchJson<InvestigationReportResponse>(
    `/api/v1/projects/${projectId}/incidents/${incidentId}/investigation-report`
  );
}

export function investigationReportMarkdownUrl(projectId: string, incidentId: string): string {
  const base = import.meta.env.VITE_API_BASE_URL ?? "";
  return `${base}/api/v1/projects/${projectId}/incidents/${incidentId}/investigation-report.md`;
}