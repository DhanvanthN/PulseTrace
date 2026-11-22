import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import { AuthProvider } from "@/features/auth/AuthProvider";
import { OverviewPage } from "@/features/dashboard/OverviewPage";

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("Overview dashboard", () => {
  it("shows live incident total from API", async () => {
    vi.stubGlobal("ResizeObserver", ResizeObserverMock);
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes("/auth/me")) {
        return new Response(
          JSON.stringify({
            id: "u1",
            email: "a@b.com",
            full_name: "A",
            is_active: true,
            created_at: "",
            updated_at: "",
          }),
          { status: 200 }
        );
      }
      if (url.includes("/projects?")) {
        return new Response(
          JSON.stringify({
            items: [{ id: "p1", name: "ShopFlow", environment: "staging", description: "", created_at: "", updated_at: "" }],
            total: 1,
            skip: 0,
            limit: 50,
          }),
          { status: 200 }
        );
      }
      if (url.includes("/incidents?")) {
        return new Response(
          JSON.stringify({
            items: [],
            total: 3,
            skip: 0,
            limit: 8,
            status_counts: { OPEN: 2 },
            severity_counts: { HIGH: 1, CRITICAL: 1 },
          }),
          { status: 200 }
        );
      }
      if (url.includes("/anomalies?")) {
        return new Response(JSON.stringify({ items: [], total: 4, skip: 0, limit: 1, severity_counts: {} }), {
          status: 200,
        });
      }
      if (url.includes("/services")) {
        return new Response(JSON.stringify({ items: [{ id: "s1", name: "API", service_type: "api", environment: "staging", description: "" }] }), {
          status: 200,
        });
      }
      return new Response("{}", { status: 404 });
    });

    render(
      <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
        <MemoryRouter>
          <AuthProvider>
            <OverviewPage />
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText("3")).toBeInTheDocument();
    });
  });
});