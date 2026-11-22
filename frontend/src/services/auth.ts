import { fetchJson } from "@/services/api";
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

export function loginUser(payload: LoginPayload): Promise<TokenResponse> {
  return fetchJson<TokenResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function fetchCurrentUser(): Promise<User> {
  return fetchJson<User>("/api/v1/auth/me");
}

export function logoutUser(): Promise<void> {
  return fetchJson<void>("/api/v1/auth/logout", { method: "POST" });
}