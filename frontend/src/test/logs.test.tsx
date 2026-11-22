import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AuthProvider } from "@/features/auth/AuthProvider";
import { LogUploadPage } from "@/features/logs/LogUploadPage";
import { LogExplorerPage } from "@/features/logs/LogExplorerPage";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("Logs UI", () => {
  it("validates unsupported upload extensions", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "Not authenticated" }), { status: 401 })
    );
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/projects/p1/logs/upload"]}>
          <AuthProvider>
            <Routes>
              <Route path="/projects/:projectId/logs/upload" element={<LogUploadPage />} />
            </Routes>
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>
    );

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const bad = new File(["data"], "malware.exe", { type: "application/octet-stream" });
    fireEvent.change(input, { target: { files: [bad] } });
    expect(await screen.findByText(/unsupported format/i)).toBeInTheDocument();
  });

  it("renders log explorer empty state", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
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
      if (url.includes("/services")) {
        return new Response(JSON.stringify({ items: [] }), { status: 200 });
      }
      if (url.includes("/logs?")) {
        return new Response(
          JSON.stringify({ items: [], total: 0, skip: 0, limit: 25 }),
          { status: 200 }
        );
      }
      return new Response("{}", { status: 404 });
    });

    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/projects/p1/logs"]}>
          <AuthProvider>
            <Routes>
              <Route path="/projects/:projectId/logs" element={<LogExplorerPage />} />
            </Routes>
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId("logs-empty-state")).toBeInTheDocument();
    });
  });
});