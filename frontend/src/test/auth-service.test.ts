import { afterEach, describe, expect, it, vi } from "vitest";

import { loginUser, logoutUser } from "@/services/auth";
import { clearToken, getToken, setToken } from "@/services/auth-session";

describe("auth service", () => {
  afterEach(() => {
    clearToken();
    vi.restoreAllMocks();
  });

  it("loginUser stores access_token in sessionStorage", async () => {
    const user = {
      id: "u1",
      email: "a@example.com",
      full_name: "Test",
      is_active: true,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    };
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          access_token: "jwt-from-login",
          token_type: "bearer",
          expires_in: 3600,
          user,
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      )
    );

    await loginUser({ email: "a@example.com", password: "SecurePass1!" });
    expect(getToken()).toBe("jwt-from-login");
  });

  it("logoutUser clears session token even when API call succeeds", async () => {
    setToken("jwt-to-clear");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(null, { status: 204 }));

    await logoutUser();
    expect(getToken()).toBeNull();
  });
});