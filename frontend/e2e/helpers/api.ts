import { APIRequestContext, expect } from "@playwright/test";

import { E2E_PASSWORD } from "./constants";
import { buildRecentJsonlSpike } from "./data";

export class PulseTraceApi {
  constructor(
    private readonly request: APIRequestContext,
    private readonly baseUrl: string
  ) {}

  async assertReachable(): Promise<void> {
    const health = await this.request.get(`${this.baseUrl}/api/v1/health/database`);
    expect(health.ok(), "Postgres/API must be running for E2E").toBeTruthy();
  }

  async register(fullName: string, email: string, password = E2E_PASSWORD) {
    const response = await this.request.post(`${this.baseUrl}/api/v1/auth/register`, {
      data: { full_name: fullName, email, password },
    });
    expect(response.ok()).toBeTruthy();
    return response.json();
  }

  async login(email: string, password = E2E_PASSWORD): Promise<string> {
    const response = await this.request.post(`${this.baseUrl}/api/v1/auth/login`, {
      data: { email, password },
    });
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    return body.access_token as string;
  }

  async registerAndLogin(email: string, fullName = "E2E User") {
    await this.register(fullName, email);
    const token = await this.login(email);
    return { email, token };
  }

  authHeaders(token: string) {
    return { Authorization: `Bearer ${token}` };
  }

  async createProject(token: string, name: string, environment = "staging") {
    const response = await this.request.post(`${this.baseUrl}/api/v1/projects`, {
      headers: this.authHeaders(token),
      data: { name, environment, description: "E2E isolated project" },
    });
    expect(response.status()).toBe(201);
    return response.json() as Promise<{ id: string; name: string }>;
  }

  async uploadJsonl(token: string, projectId: string, filename: string, content: Buffer) {
    const response = await this.request.post(`${this.baseUrl}/api/v1/projects/${projectId}/logs/upload`, {
      headers: this.authHeaders(token),
      multipart: {
        file: {
          name: filename,
          mimeType: "application/octet-stream",
          buffer: content,
        },
      },
    });
    return response;
  }

  async runAnalysis(token: string, projectId: string) {
    return this.request.post(`${this.baseUrl}/api/v1/projects/${projectId}/analysis/run`, {
      headers: { ...this.authHeaders(token), "Content-Type": "application/json" },
      data: {},
    });
  }

  async correlate(token: string, projectId: string) {
    return this.request.post(`${this.baseUrl}/api/v1/projects/${projectId}/incidents/correlate`, {
      headers: this.authHeaders(token),
    });
  }

  async listIncidents(token: string, projectId: string) {
    const response = await this.request.get(`${this.baseUrl}/api/v1/projects/${projectId}/incidents`, {
      headers: this.authHeaders(token),
    });
    expect(response.ok()).toBeTruthy();
    return response.json() as Promise<{ items: Array<{ id: string; title: string }>; total: number }>;
  }

  async investigate(token: string, projectId: string, incidentId: string) {
    return this.request.post(
      `${this.baseUrl}/api/v1/projects/${projectId}/incidents/${incidentId}/investigate`,
      { headers: { ...this.authHeaders(token), "Content-Type": "application/json" }, data: {} }
    );
  }

  /** Fresh user, project, spike logs uploaded (no analysis yet). */
  async createLogReadyWorkspace(suffix: string) {
    const email = `e2e-pulsetrace-${suffix}-${Date.now()}@example.com`;
    const { token } = await this.registerAndLogin(email, `E2E ${suffix}`);
    const project = await this.createProject(token, `E2E ${suffix} ${Date.now().toString(36)}`);
    const upload = await this.uploadJsonl(token, project.id, "spike.jsonl", buildRecentJsonlSpike());
    expect(upload.status()).toBe(201);
    return { email, token, projectId: project.id, projectName: project.name };
  }

  /** Through correlate — ready for incident UI + RCA. */
  async createIncidentReadyWorkspace(suffix: string) {
    const base = await this.createLogReadyWorkspace(suffix);
    const analysis = await this.runAnalysis(base.token, base.projectId);
    expect(analysis.ok()).toBeTruthy();
    const runBody = await analysis.json();
    expect(runBody.status).toBe("completed");
    expect(runBody.anomalies_detected).toBeGreaterThan(0);

    const correlate = await this.correlate(base.token, base.projectId);
    expect(correlate.ok()).toBeTruthy();
    const incidents = await this.listIncidents(base.token, base.projectId);
    expect(incidents.total).toBeGreaterThan(0);
    return {
      ...base,
      incidentId: incidents.items[0].id,
      incidentTitle: incidents.items[0].title,
    };
  }
}