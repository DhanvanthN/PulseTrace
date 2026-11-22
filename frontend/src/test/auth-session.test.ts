import { afterEach, describe, expect, it } from "vitest";

import { clearToken, getToken, setToken } from "@/services/auth-session";

describe("auth-session", () => {
  afterEach(() => {
    clearToken();
  });

  it("stores and retrieves token in sessionStorage", () => {
    expect(getToken()).toBeNull();
    setToken("test-token-value");
    expect(getToken()).toBe("test-token-value");
  });

  it("clearToken removes stored token", () => {
    setToken("test-token-value");
    clearToken();
    expect(getToken()).toBeNull();
  });
});