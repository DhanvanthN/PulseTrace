import { fetchJson } from "@/services/api";
import type {
  Project,
  ProjectCreatePayload,
  ProjectListResponse,
  ProjectUpdatePayload,
} from "@/types/project";

export function listProjects(skip = 0, limit = 20): Promise<ProjectListResponse> {
  const params = new URLSearchParams({
    skip: String(skip),
    limit: String(limit),
  });
  return fetchJson<ProjectListResponse>(`/api/v1/projects?${params}`);
}

export function getProject(projectId: string): Promise<Project> {
  return fetchJson<Project>(`/api/v1/projects/${projectId}`);
}

export function createProject(payload: ProjectCreatePayload): Promise<Project> {
  return fetchJson<Project>("/api/v1/projects", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateProject(
  projectId: string,
  payload: ProjectUpdatePayload
): Promise<Project> {
  return fetchJson<Project>(`/api/v1/projects/${projectId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteProject(projectId: string): Promise<void> {
  return fetchJson<void>(`/api/v1/projects/${projectId}`, { method: "DELETE" });
}