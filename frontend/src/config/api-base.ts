/**
 * API origin for fetches. Empty string = same origin (nginx proxies /api/ in production Compose).
 */
export function resolveApiBaseUrl(): string {
  const fromEnv = import.meta.env.VITE_API_BASE_URL;
  if (fromEnv === "") {
    return "";
  }
  if (typeof fromEnv === "string" && fromEnv.trim().length > 0) {
    return fromEnv.replace(/\/$/, "");
  }
  if (import.meta.env.MODE === "production") {
    return "";
  }
  return "http://localhost:8001";
}