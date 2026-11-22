import { getToken } from "@/services/auth-session";

/** Merge default headers with init headers and attach Bearer token when present. */
export function buildRequestHeaders(
  initHeaders?: HeadersInit,
  defaults?: Record<string, string>
): Record<string, string> {
  const base = defaults ?? {};
  const headers = new Headers(base);
  if (initHeaders) {
    new Headers(initHeaders).forEach((value, key) => {
      headers.set(key, value);
    });
  }
  if (!headers.has("Authorization")) {
    const token = getToken();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
  }
  return Object.fromEntries(headers.entries());
}