import { describe, expect, it } from "vitest";

import { resolveApiBaseUrl } from "@/config/api-base";

describe("resolveApiBaseUrl", () => {
  it("returns empty string when VITE_API_BASE_URL is explicitly empty", () => {
    const prev = import.meta.env.VITE_API_BASE_URL;
    try {
      (import.meta.env as { VITE_API_BASE_URL: string }).VITE_API_BASE_URL = "";
      expect(resolveApiBaseUrl()).toBe("");
    } finally {
      (import.meta.env as { VITE_API_BASE_URL: string }).VITE_API_BASE_URL = prev;
    }
  });
});