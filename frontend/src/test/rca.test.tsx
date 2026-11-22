import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import { AuthProvider } from "@/features/auth/AuthProvider";
import { IncidentRcaSection } from "@/features/incidents/IncidentRcaSection";

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

describe("RCA UI", () => {
  it("shows candidates with evidence strength label", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes("/auth/me")) {
        return new Response(
          JSON.stringify({
            id: "u1",
            email: "ops@test.com",
            full_name: "Ops",
            is_active: true,
            created_at: "",
            updated_at: "",
          }),
          { status: 200 }
        );
      }
      if (url.includes("/root-causes")) {
        return new Response(
          JSON.stringify({
            investigation_id: "inv1",
            version: 1,
            status: "completed",
            score_note: "Confidence scores are evidence strength (0–100), not calibrated probabilities.",
            items: [
              {
                id: "c1",
                investigation_id: "inv1",
                incident_id: "i1",
                service_id: null,
                deployment_id: null,
                cause_type: "SERVICE_FAILURE",
                title: "Service failures",
                explanation: "Hypothesis",
                confidence_score: 72.5,
                ranking: 1,
                evidence_summary: { items: [], score_note: "not probability" },
                supporting_evidence_count: 2,
                contradicting_evidence_count: 1,
                created_at: "",
                updated_at: "",
              },
            ],
          }),
          { status: 200 }
        );
      }
      return new Response("{}", { status: 404 });
    });

    render(
      <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
        <MemoryRouter>
          <AuthProvider>
            <IncidentRcaSection projectId="p1" incidentId="i1" />
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/evidence strength/i)).toBeInTheDocument();
      expect(screen.getByText(/Service failures/i)).toBeInTheDocument();
    });
  });
});