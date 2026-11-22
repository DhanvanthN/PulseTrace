import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import { AuthProvider } from "@/features/auth/AuthProvider";
import { IncidentExplorerPage } from "@/features/incidents/IncidentExplorerPage";
import { IncidentDetailPage } from "@/features/incidents/IncidentDetailPage";

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

beforeEach(() => {
  vi.stubGlobal("ResizeObserver", ResizeObserverMock);
});

describe("Incidents UI", () => {
  it("renders explorer list", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes("/auth/me")) {
        return new Response(JSON.stringify({ id: "u1", email: "a@b.com", full_name: "A", is_active: true, created_at: "", updated_at: "" }), { status: 200 });
      }
      if (url.includes("/incidents?")) {
        return new Response(
          JSON.stringify({
            items: [{ id: "i1", project_id: "p1", primary_service_id: null, title: "Error spike", description: "", severity: "HIGH", status: "OPEN", started_at: "", last_activity_at: "", resolved_at: null, created_at: "", updated_at: "" }],
            total: 1,
            skip: 0,
            limit: 20,
            status_counts: { OPEN: 1 },
            severity_counts: { HIGH: 1 },
          }),
          { status: 200 }
        );
      }
      return new Response("{}", { status: 404 });
    });

    render(
      <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
        <MemoryRouter initialEntries={["/projects/p1/incidents/explore"]}>
          <AuthProvider>
            <Routes>
              <Route path="/projects/:projectId/incidents/explore" element={<IncidentExplorerPage />} />
            </Routes>
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>
    );
    expect(await screen.findByTestId("incident-table-link")).toHaveTextContent(/Error spike/i);
  });

  it("renders incident timeline", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes("/auth/me")) {
        return new Response(JSON.stringify({ id: "u1", email: "a@b.com", full_name: "A", is_active: true, created_at: "", updated_at: "" }), { status: 200 });
      }
      if (url.endsWith("/incidents/i1") || url.includes("/incidents/i1")) {
        if (url.includes("/timeline")) {
          return new Response(
            JSON.stringify({
              items: [
                {
                  id: "e1",
                  incident_id: "i1",
                  event_type: "ANOMALY_DETECTED",
                  description: "Statistical error spike",
                  event_timestamp: "2026-01-01T12:00:00Z",
                  metadata: {},
                  created_at: "2026-01-01T12:00:00Z",
                },
              ],
            }),
            { status: 200 }
          );
        }
        if (url.includes("/evidence")) {
          return new Response(JSON.stringify({ items: [{ id: "ev1", incident_id: "i1", log_id: null, anomaly_id: "a1", cluster_id: null, evidence_type: "anomaly", explanation: "observed", created_at: "" }] }), { status: 200 });
        }
        if (url.includes("/root-causes")) {
          return new Response(
            JSON.stringify({
              investigation_id: null,
              version: null,
              status: null,
              items: [],
              score_note: "Confidence scores are evidence strength (0–100), not calibrated probabilities.",
            }),
            { status: 200 }
          );
        }
        return new Response(
          JSON.stringify({
            id: "i1",
            project_id: "p1",
            primary_service_id: null,
            title: "Spike",
            description: "Grouped",
            severity: "HIGH",
            status: "OPEN",
            started_at: "",
            last_activity_at: "",
            resolved_at: null,
            created_at: "",
            updated_at: "",
            events_count: 1,
            evidence_count: 1,
          }),
          { status: 200 }
        );
      }
      if (url.includes("/deployments")) {
        return new Response(JSON.stringify({ items: [], total: 0, skip: 0, limit: 50 }), { status: 200 });
      }
      return new Response("{}", { status: 404 });
    });

    render(
      <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
        <MemoryRouter initialEntries={["/projects/p1/incidents/i1"]}>
          <AuthProvider>
            <Routes>
              <Route path="/projects/:projectId/incidents/:incidentId" element={<IncidentDetailPage />} />
            </Routes>
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>
    );
    await waitFor(() => {
      expect(screen.getByText(/Statistical error spike/i)).toBeInTheDocument();
    });
  });
});