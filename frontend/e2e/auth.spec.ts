import type { Page } from "@playwright/test";

import { E2E_API_URL, expect, test } from "./fixtures";
import { E2E_PASSWORD, uniqueE2eEmail } from "./helpers/constants";
import { attachBearerRoute, primeSession, type TokenRef, watchAccessToken } from "./helpers/auth-browser";
import { assertNoConsoleErrors, trackConsoleErrors } from "./helpers/assertions";

test.describe("Authentication", () => {
  test("registration via UI creates session", async ({ page, api }) => {
    const errors = trackConsoleErrors(page);
    const tokenRef: TokenRef = { current: null };
    await attachBearerRoute(page, tokenRef);
    watchAccessToken(page, tokenRef);

    const email = uniqueE2eEmail("register-ui");
    await page.goto("/register");
    await page.getByLabel("Full name").fill("E2E Register");
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill(E2E_PASSWORD);
    const loginReady = page.waitForResponse(
      (res) => res.url().includes("/api/v1/auth/login") && res.ok()
    );
    await page.getByRole("button", { name: "Create account" }).click();
    const loginRes = await loginReady;
    const loginBody = (await loginRes.json()) as { access_token?: string };
    tokenRef.current = loginBody.access_token ?? null;

    await expect(page.getByRole("heading", { name: "Overview" })).toBeVisible({ timeout: 20_000 });
    expect(tokenRef.current).toBeTruthy();
    assertNoConsoleErrors(errors);
  });

  test("successful login via UI", async ({ page, api }) => {
    const email = uniqueE2eEmail("login-ui");
    await api.register("E2E Login", email);

    const errors = trackConsoleErrors(page);
    const tokenRef: TokenRef = { current: null };
    await attachBearerRoute(page, tokenRef);
    watchAccessToken(page, tokenRef);

    await page.goto("/login");
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill(E2E_PASSWORD);
    const loginReady = page.waitForResponse(
      (res) => res.url().includes("/api/v1/auth/login") && res.ok()
    );
    await page.getByRole("button", { name: "Sign in" }).click();
    await loginReady;

    await expect(page.getByRole("heading", { name: "Overview" })).toBeVisible({ timeout: 15_000 });
    assertNoConsoleErrors(errors);
  });

  test("invalid login shows error", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel("Email").fill("missing@example.com");
    await page.getByLabel("Password").fill("WrongPass9!");
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page.getByRole("alert")).toBeVisible();
    await expect(page).toHaveURL(/\/login/);
  });

  test("logout returns to sign-in", async ({ page, api }) => {
    const email = uniqueE2eEmail("logout");
    const token = await api.registerAndLogin(email).then((r) => r.token);
    await primeSession(page, token);

    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Overview" })).toBeVisible();
    await page.unroute("**/api/v1/**");
    await page.getByRole("button", { name: "Sign out" }).click();
    await expect(page).toHaveURL(/\/login/, { timeout: 15_000 });
  });

  test("protected routes redirect unauthenticated users", async ({ page }) => {
    await page.goto("/projects");
    await expect(page).toHaveURL(/\/login/, { timeout: 15_000 });
    await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
  });

  test("session expiration surfaces on overview", async ({ page, api }) => {
    const email = uniqueE2eEmail("session");
    const token = await api.registerAndLogin(email).then((r) => r.token);
    const tokenRef: TokenRef = { current: token };
    await attachBearerRoute(page, tokenRef);

    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Overview" })).toBeVisible();

    tokenRef.current = "invalid.jwt.token";
    await page.reload();
    await expect(page).toHaveURL(/\/login/, { timeout: 15_000 });
  });
});