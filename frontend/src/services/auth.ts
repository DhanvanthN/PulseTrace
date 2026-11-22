import { fetchJson } from "@/services/api";
import { clearToken, setToken } from "@/services/auth-session";
import type {
  LoginPayload,
  RegisterPayload,
  TokenResponse,
  User,
} from "@/types/auth";

export function registerUser(payload: RegisterPayload): Promise<User> {
  return fetchJson<User>("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function loginUser(payload: LoginPayload): Promise<TokenResponse> {
  const response = await fetchJson<TokenResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  setToken(response.access_token);
  return response;
}

export function fetchCurrentUser(): Promise<User> {
  return fetchJson<User>("/api/v1/auth/me");
}

export async function logoutUser(): Promise<void> {
  try {
    await fetchJson<void>("/api/v1/auth/logout", { method: "POST" });
  } finally {
    clearToken();
  }
}