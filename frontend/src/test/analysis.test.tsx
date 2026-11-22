import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider } from "@/features/auth/AuthProvider";
import { AnalysisDashboardPage } from "@/features/analysis/AnalysisDashboardPage";
import { AnomalyExplorerPage } from "@/features/analysis/AnomalyExplorerPage";
import { ClusterExplorerPage } from "@/features/analysis/ClusterExplorerPage";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

beforeEach(() => {
  class ResizeObserverMock {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  vi.stubGlobal("ResizeObserver", ResizeObserverMock);
});

describe("Analysis UI", () => {
  it("runs analysis and shows severity chart data", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.includes("/auth/me")) {
        return new Response(
          JSON.stringify({
            id: "00000000-0000-0000-0000-000000000099",
            email: "ops@example.com",
            full_name: "Ops",
            is_active: true,
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-01-01T00:00:00Z",
          }),
          { status: 200 }
        );
      }
      if (url.includes("/analysis/run") && init?.method === "POST") {
        return new Response(
          JSON.stringify({
            status: "completed",
            message: "ok",
            anomalies_created: 1,
            anomalies_detected: 1,
            clusters_created: 1,
            cluster_memberships: 3,
            noise_logs: 0,
            logs_analyzed: 10,
            window_start: "2026-01-01T00:00:00Z",
            window_end: "2026-01-02T00:00:00Z",
            methods: ["statistical_zscore"],
          }),
          { status: 200 }
        );
      }
      if (url.includes("/anomalies?")) {
        return new Response(
          JSON.stringify({
            items: [
              {
                id: "a1",
                project_id: "p1",
                service_id: null,
                anomaly_type: "error_spike",
                severity: "HIGH",
                score: 3.2,
                description: "Statistical error spike",
                start_time: "2026-01-01T12:00:00Z",
                end_time: "2026-01-01T13:00:00Z",
                detection_method: "statistical_zscore",
                evidence: { z_score: 3.2 },
                created_at: "2026-01-01T13:00:00Z",
              },
            ],
            total: 1,
            skip: 0,
            limit: 8,
            severity_counts: { HIGH: 1 },
          }),
          { status: 200 }
        );
      }
      return new Response("{}", { status: 404 });
    });

    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/projects/p1/analysis"]}>
          <AuthProvider>
            <Routes>
              <Route path="/projects/:projectId/analysis" element={<AnalysisDashboardPage />} />
            </Routes>
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /run analysis/i })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole("button", { name: /run analysis/i }));
    expect(await screen.findByText(/Anomalies detected:/i)).toBeInTheDocument();
  });

  it("renders anomaly explorer empty state", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes("/auth/me")) {
        return new Response(
          JSON.stringify({
            id: "u1",
            email: "ops@example.com",
            full_name: "Ops",
            is_active: true,
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-01-01T00:00:00Z",
          }),
          { status: 200 }
        );
      }
      if (url.includes("/services")) {
        return new Response(JSON.stringify({ items: [] }), { status: 200 });
      }
      if (url.includes("/anomalies?")) {
        return new Response(
          JSON.stringify({ items: [], total: 0, skip: 0, limit: 20, severity_counts: {} }),
          { status: 200 }
        );
      }
      return new Response("{}", { status: 404 });
    });

    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/projects/p1/anomalies"]}>
          <AuthProvider>
            <Routes>
              <Route path="/projects/:projectId/anomalies" element={<AnomalyExplorerPage />} />
            </Routes>
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>
    );

    expect(await screen.findByText(/no anomalies/i)).toBeInTheDocument();
  });

  it("renders cluster detail", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes("/auth/me")) {
        return new Response(
          JSON.stringify({
            id: "u1",
            email: "ops@example.com",
            full_name: "Ops",
            is_active: true,
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-01-01T00:00:00Z",
          }),
          { status: 200 }
        );
      }
      if (url.includes("/clusters?")) {
        return new Response(
          JSON.stringify({
            items: [
              {
                id: "c1",
                project_id: "p1",
                cluster_label: "C000",
                description: "Text-similarity cluster",
                representative_message: "payment timeout",
                algorithm: "dbscan_tfidf",
                log_count: 4,
                first_seen: "2026-01-01T00:00:00Z",
                last_seen: "2026-01-01T01:00:00Z",
                created_at: "2026-01-01T01:00:00Z",
              },
            ],
            total: 1,
            skip: 0,
            limit: 15,
          }),
          { status: 200 }
        );
      }
      if (url.includes("/clusters/c1")) {
        return new Response(
          JSON.stringify({
            id: "c1",
            project_id: "p1",
            cluster_label: "C000",
            description: "Text-similarity cluster",
            representative_message: "payment timeout",
            algorithm: "dbscan_tfidf",
            log_count: 4,
            first_seen: "2026-01-01T00:00:00Z",
            last_seen: "2026-01-01T01:00:00Z",
            created_at: "2026-01-01T01:00:00Z",
            logs: [{ id: "l1", timestamp: "2026-01-01T00:00:00Z", level: "ERROR", message: "payment timeout", service_id: null }],
          }),
          { status: 200 }
        );
      }
      return new Response("{}", { status: 404 });
    });

    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/projects/p1/clusters"]}>
          <AuthProvider>
            <Routes>
              <Route path="/projects/:projectId/clusters" element={<ClusterExplorerPage />} />
            </Routes>
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>
    );

    fireEvent.click(await screen.findByText(/C000/));
    expect(await screen.findByText(/payment timeout/i)).toBeInTheDocument();
  });
});