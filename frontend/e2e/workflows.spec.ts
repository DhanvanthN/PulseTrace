import { expect, test } from "./fixtures";
import { primeSession } from "./helpers/auth-browser";
import { captureE2e } from "./helpers/screenshots";

/** End-to-end happy path across hubs (browser-driven analysis steps). */
test.describe("Core workflow", () => {
  test("register project upload analyze correlate investigate", async ({ page, api }) => {
    const workspace = await api.createLogReadyWorkspace("workflow-full");
    await primeSession(page, workspace.token);

    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Overview" })).toBeVisible();
    await captureE2e(page, "dashboard");

    await page.goto(`/projects/${workspace.projectId}/logs`);
    await expect(page.getByRole("heading", { name: "Search logs" })).toBeVisible();

    await page.goto(`/projects/${workspace.projectId}/analysis`);
    await page.getByRole("button", { name: "Run analysis" }).click();
    await expect(page.getByText(/completed/i)).toBeVisible({ timeout: 120_000 });

    await page.goto(`/projects/${workspace.projectId}/incidents`);
    await page.getByRole("button", { name: "Run correlation" }).click();
    await expect(page.getByText(/Last correlation/)).toBeVisible({ timeout: 120_000 });

    const incidents = await api.listIncidents(workspace.token, workspace.projectId);
    await page.goto(`/projects/${workspace.projectId}/incidents/${incidents.items[0].id}`);
    await page.locator('[aria-label="Root cause analysis"]').getByRole("button", {
      name: "Run RCA investigation",
    }).click();
    await expect(page.getByText(/Completed · \d+ candidates/)).toBeVisible({ timeout: 120_000 });
  });
});