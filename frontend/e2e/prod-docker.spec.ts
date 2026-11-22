/**
 * Production Docker stack (nginx same-origin). Run when stack is up:
 *
 *   E2E_SKIP_WEBSERVER=1 E2E_BASE_URL=http://127.0.0.1:8081 npm run test:e2e -- prod-docker.spec.ts
 */
import path from "node:path";
import { fileURLToPath } from "node:url";

import { expect, test } from "@playwright/test";

import { buildRecentJsonlSpike } from "./helpers/data";
import { E2E_PASSWORD, uniqueE2eEmail } from "./helpers/constants";

const baseURL = process.env.E2E_BASE_URL ?? "http://127.0.0.1:8081";

test.describe("Production Docker stack", () => {
  test.skip(!process.env.E2E_PROD_STACK, "Set E2E_PROD_STACK=1 when QA compose is running");

  test.use({ baseURL });

  test("same-origin workflow through nginx", async ({ page }) => {
    const email = uniqueE2eEmail("prod-docker");
    const name = "Prod QA User";

    await page.goto("/register");
    await page.getByLabel("Full name").fill(name);
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill(E2E_PASSWORD);
    await page.getByRole("button", { name: "Create account" }).click();
    await expect(page.getByRole("heading", { name: "Overview" })).toBeVisible({ timeout: 30_000 });

    await page.goto("/projects");
    await page.getByRole("button", { name: "New project" }).click();
    const projectName = `QA ${Date.now().toString(36)}`;
    await page.getByLabel("Name").fill(projectName);
    await page.locator("form").getByRole("button", { name: "Create project" }).click();
    await expect(page.getByRole("heading", { level: 2, name: projectName })).toBeVisible();

    await page.getByRole("link", { name: projectName, exact: true }).first().click();
    const projectUrl = page.url();
    const projectId = projectUrl.split("/projects/")[1]?.split(/[/?#]/)[0] ?? "";
    expect(projectId.length).toBeGreaterThan(8);

    await page.goto(`${baseURL}/projects/${projectId}/logs/upload`);
    await page.locator('input[type="file"]').setInputFiles({
      name: "spike.jsonl",
      mimeType: "application/json",
      buffer: buildRecentJsonlSpike(),
    });
    await page.getByRole("button", { name: "Upload and process" }).click();
    await expect(page.getByText(/Processed \d+/)).toBeVisible({ timeout: 120_000 });

    await page.goto(`${baseURL}/projects/${projectId}/analysis`);
    await page.getByRole("button", { name: "Run analysis" }).click();
    await expect(page.getByText(/completed/i)).toBeVisible({ timeout: 180_000 });

    await page.goto(`${baseURL}/projects/${projectId}/incidents`);
    await page.getByRole("button", { name: "Run correlation" }).click();
    await expect(page.getByText(/Last correlation/)).toBeVisible({ timeout: 180_000 });

    await page.getByRole("link", { name: "Open explorer" }).click();
    await page.getByTestId("incident-table-link").first().click();

    const rca = page.locator('[aria-label="Root cause analysis"]');
    await rca.getByRole("button", { name: "Run RCA investigation" }).click();
    await expect(rca.getByText(/Completed · \d+ candidates/)).toBeVisible({ timeout: 180_000 });

    await expect(rca.getByRole("button", { name: "Export Markdown" })).toBeEnabled();
    await page.getByRole("button", { name: "Sign out" }).click();
    await expect(page).toHaveURL(/\/login/, { timeout: 15_000 });

    await page.goto("/projects");
    await expect(page).toHaveURL(/\/login/, { timeout: 15_000 });
  });

  test("SPA refresh on nested route", async ({ page, request }) => {
    const health = await request.get(`${baseURL}/api/v1/health/database`).catch(() => null);
    test.skip(!health?.ok(), "Stack not reachable");
    await page.goto("/login");
    await page.reload();
    await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
    await page.goto("/investigations");
    await page.reload();
    await expect(page).toHaveURL(/\/login/);
  });
});