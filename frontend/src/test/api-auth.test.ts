import { afterEach, describe, expect, it, vi } from "vitest";

import { fetchJson } from "@/services/api";
import { clearToken, getToken, setToken } from "@/services/auth-session";

describe("fetchJson auth handling", () => {
  afterEach(() => {
    clearToken();
    vi.restoreAllMocks();
  });

  it("clears session token on 401 responses", async () => {
    setToken("expired-token");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "Not authenticated" }), { status: 401 })
    );

    await expect(fetchJson("/api/v1/auth/me")).rejects.toThrow();
    expect(getToken()).toBeNull();
  });

  it("keeps session token when POST /api/v1/auth/login returns 401", async () => {
    setToken("existing-token");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "Invalid credentials" }), { status: 401 })
    );

    await expect(
      fetchJson("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email: "a@b.com", password: "wrong" }),
      })
    ).rejects.toThrow();
    expect(getToken()).toBe("existing-token");
  });
});