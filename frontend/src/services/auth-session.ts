const STORAGE_KEY = "pulsetrace_access_token";

function storageAvailable(): boolean {
  try {
    return typeof sessionStorage !== "undefined";
  } catch {
    return false;
  }
}

export function getToken(): string | null {
  if (!storageAvailable()) {
    return null;
  }
  try {
    return sessionStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string): void {
  if (!storageAvailable()) {
    return;
  }
  try {
    sessionStorage.setItem(STORAGE_KEY, token);
  } catch {
    // ignore quota / private mode
  }
}

export function clearToken(): void {
  if (!storageAvailable()) {
    return;
  }
  try {
    sessionStorage.removeItem(STORAGE_KEY);
  } catch {
    // ignore
  }
}