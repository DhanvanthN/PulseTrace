import type { Page } from "@playwright/test";

export type TokenRef = { current: string | null };

export async function attachBearerRoute(page: Page, tokenRef: TokenRef | string): Promise<void> {
  const resolveToken = () => (typeof tokenRef === "string" ? tokenRef : tokenRef.current);

  await page.route("**/api/v1/**", async (route) => {
    const token = resolveToken();
    const headers = { ...route.request().headers() };
    if (token) {
      headers.authorization = `Bearer ${token}`;
    } else {
      delete headers.authorization;
    }
    await route.continue({ headers });
  });
}

/** Capture JWT from login responses so UI auth works across ports (5173 → API). */
export function watchAccessToken(page: Page, tokenRef: TokenRef): void {
  page.on("response", async (response) => {
    try {
      if (!response.url().includes("/api/v1/auth/login") || !response.ok()) {
        return;
      }
      const body = (await response.json()) as { access_token?: string };
      if (body.access_token) {
        tokenRef.current = body.access_token;
      }
    } catch {
      // ignore parse errors
    }
  });
}

export async function primeSession(page: Page, token: string): Promise<void> {
  const tokenRef: TokenRef = { current: token };
  await attachBearerRoute(page, tokenRef);
  watchAccessToken(page, tokenRef);
}