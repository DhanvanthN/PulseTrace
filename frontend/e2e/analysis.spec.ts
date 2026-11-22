import { expect, test } from "./fixtures";
import { primeSession } from "./helpers/auth-browser";
import { uniqueE2eEmail } from "./helpers/constants";

test.describe("Analysis", () => {
  test("run analysis and explore anomalies and clusters", async ({ page, logReady }) => {
    await primeSession(page, logReady.token);
    await page.goto(`/projects/${logReady.projectId}/analysis`);

    await page.getByRole("button", { name: "Run analysis" }).click();
    await expect(page.getByText(/Anomalies detected:/)).toBeVisible({ timeout: 120_000 });
    await expect(page.getByText(/Status:/)).toContainText(/completed/i);

    await page.getByRole("link", { name: "View anomalies" }).click();
    await expect(page.getByRole("heading", { name: "Anomaly explorer" })).toBeVisible();
    await expect(page.getByText(/Results \(\d+\)/)).toContainText(/Results \([1-9]/);
    await page.locator("button.w-full.rounded-md.border").first().click();
    await expect(page.getByText("Method:")).toBeVisible({ timeout: 15_000 });

    await page.goto(`/projects/${logReady.projectId}/clusters`);
    await expect(page.getByRole("heading", { name: "Log clustering" })).toBeVisible();
  });

  test("empty analysis state without logs", async ({ page, api }) => {
    const email = uniqueE2eEmail("analysis-empty");
    const token = await api.registerAndLogin(email).then((r) => r.token);
    const project = await api.createProject(token, `No logs ${Date.now().toString(36)}`);
    await primeSession(page, token);

    await page.goto(`/projects/${project.id}/analysis`);
    await page.getByRole("button", { name: "Run analysis" }).click();
    await expect(page.getByText(/Status:/)).toContainText(/no_data/i, { timeout: 60_000 });
    await expect(page.getByText(/No anomalies yet/)).toBeVisible();
  });
});