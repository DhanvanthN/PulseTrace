export const E2E_PASSWORD = "SecurePass1!";
export const E2E_USER_PREFIX = "e2e-pulsetrace";

export function uniqueE2eEmail(suffix: string): string {
  const stamp = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  return `${E2E_USER_PREFIX}-${suffix}-${stamp}@example.com`;
}