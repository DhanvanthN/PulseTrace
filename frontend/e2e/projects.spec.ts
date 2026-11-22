import { expect, test } from "./fixtures";
import { primeSession } from "./helpers/auth-browser";
import { uniqueE2eEmail } from "./helpers/constants";
import { captureE2e } from "./helpers/screenshots";

test.describe("Projects", () => {
  test("empty project state then creation", async ({ page, api }) => {
    const email = uniqueE2eEmail("projects-empty");
    const token = await api.registerAndLogin(email).then((r) => r.token);
    await primeSession(page, token);

    await page.goto("/projects");
    await expect(page.getByTestId("projects-empty-state")).toBeVisible({ timeout: 15_000 });

    await page.getByRole("button", { name: "Create project" }).click();
    const name = `E2E UI Project ${Date.now().toString(36)}`;
    await page.getByLabel("Name").fill(name);
    await page.locator("form").getByRole("button", { name: "Create project" }).click();

    await expect(page.getByRole("heading", { level: 2, name })).toBeVisible({ timeout: 10_000 });
    await captureE2e(page, "dashboard-projects-list");
  });

  test("project listing and switching", async ({ page, logReady }) => {
    await primeSession(page, logReady.token);

    const other = await page.request.post(`${process.env.E2E_API_URL ?? "http://127.0.0.1:8000"}/api/v1/projects`, {
      headers: { Authorization: `Bearer ${logReady.token}` },
      data: { name: `Second ${Date.now().toString(36)}`, environment: "development" },
    });
    expect(other.ok()).toBeTruthy();
    const otherBody = await other.json();

    await page.goto("/projects");
    await expect(page.getByRole("heading", { level: 2, name: logReady.projectName })).toBeVisible();
    await page.getByRole("link", { name: otherBody.name, exact: true }).first().click();
    await expect(page.getByRole("heading", { level: 1, name: otherBody.name })).toBeVisible();
    await page.goBack();
    await expect(page.getByRole("heading", { name: "Projects" })).toBeVisible();
  });

  test("project detail links from hub", async ({ page, logReady }) => {
    await primeSession(page, logReady.token);
    await page.goto(`/projects/${logReady.projectId}`);
    await expect(page.getByRole("heading", { level: 1, name: logReady.projectName })).toBeVisible();
  });
});