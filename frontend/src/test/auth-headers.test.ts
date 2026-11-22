import { afterEach, describe, expect, it } from "vitest";

import { buildRequestHeaders } from "@/services/auth-headers";
import { clearToken, setToken } from "@/services/auth-session";

describe("buildRequestHeaders", () => {
  afterEach(() => {
    clearToken();
  });

  it("does not attach Authorization when no token", () => {
    const headers = buildRequestHeaders(undefined, { Accept: "application/json" });
    expect(headers.Authorization).toBeUndefined();
  });

  it("attaches Authorization Bearer when token exists", () => {
    setToken("abc123token");
    const headers = buildRequestHeaders(undefined, { Accept: "application/json" });
    const auth = headers.Authorization ?? headers.authorization;
    expect(auth).toBe("Bearer abc123token");
  });

  it("does not overwrite an explicit Authorization header", () => {
    setToken("abc123token");
    const headers = buildRequestHeaders(
      { Authorization: "Bearer custom" },
      { Accept: "application/json" }
    );
    const auth = headers.Authorization ?? headers.authorization;
    expect(auth).toBe("Bearer custom");
  });
});