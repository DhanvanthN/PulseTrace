import { resolveApiBaseUrl } from "@/config/api-base";

const API_BASE_URL = resolveApiBaseUrl();

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly details?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function fetchJson<T>(
  path: string,
  init?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (
    response.status === 401 &&
    typeof window !== "undefined" &&
    import.meta.env.MODE !== "test"
  ) {
    const onAuthPage =
      window.location.pathname.startsWith("/login") ||
      window.location.pathname.startsWith("/register");
    if (!onAuthPage) {
      window.location.assign("/login?session=expired");
    }
  }

  if (!response.ok) {
    let details: unknown;
    try {
      details = await response.json();
    } catch {
      details = undefined;
    }
    let message = `Request failed (${response.status})`;
    if (typeof details === "object" && details !== null && "detail" in details) {
      const detail = (details as { detail: unknown }).detail;
      if (typeof detail === "string") {
        message = detail;
      } else if (Array.isArray(detail) && detail.length > 0) {
        const first = detail[0] as { msg?: string };
        message = first.msg ?? message;
      }
    }
    throw new ApiError(message, response.status, details);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}