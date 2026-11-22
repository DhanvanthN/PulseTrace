import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AuthProvider } from "@/features/auth/AuthProvider";
import { ProjectsPage } from "@/features/projects/ProjectsPage";

const mockUser = {
  id: "00000000-0000-0000-0000-000000000001",
  email: "dev@example.com",
  full_name: "Dev User",
  is_active: true,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

function renderProjects() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <AuthProvider>
          <ProjectsPage />
        </AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe("Projects UI", () => {
  it("shows loading then empty state when no projects", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes("/auth/me")) {
        return new Response(JSON.stringify(mockUser), { status: 200 });
      }
      if (url.includes("/projects")) {
        return new Response(
          JSON.stringify({ items: [], total: 0, skip: 0, limit: 20 }),
          { status: 200 }
        );
      }
      return new Response("{}", { status: 404 });
    });

    renderProjects();
    await waitFor(() => {
      expect(screen.getByTestId("projects-empty-state")).toBeInTheDocument();
    });
  });
});