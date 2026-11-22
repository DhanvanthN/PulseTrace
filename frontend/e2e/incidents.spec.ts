import { expect, test } from "./fixtures";
import { primeSession } from "./helpers/auth-browser";
import { captureE2e } from "./helpers/screenshots";

test.describe("Incident management", () => {
  test("correlate, explore, detail, notes, resolve and reopen", async ({ page, logReady }) => {
    await primeSession(page, logReady.token);

    await page.goto(`/projects/${logReady.projectId}/analysis`);
    await page.getByRole("button", { name: "Run analysis" }).click();
    await expect(page.getByText(/completed/i)).toBeVisible({ timeout: 120_000 });

    await page.goto(`/projects/${logReady.projectId}/incidents`);
    await page.getByRole("button", { name: "Run correlation" }).click();
    await expect(page.getByText(/Last correlation/)).toBeVisible({ timeout: 120_000 });

    await page.getByRole("link", { name: "Open explorer" }).click();
    await expect(page.getByRole("heading", { name: "Incident explorer" })).toBeVisible();
    await captureE2e(page, "incident-explorer");

    await page.getByTestId("incident-table-link").first().click();
    await expect(page.locator("section[aria-label='Incident overview']")).toBeVisible({ timeout: 15_000 });
    await captureE2e(page, "incident-detail");

    await expect(page.getByRole("heading", { name: "Incident timeline" })).toBeVisible();
    await expect(page.locator("#incident-timeline ol li").first()).toBeVisible();

    await expect(page.getByRole("heading", { name: "Related anomalies" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Supporting evidence" })).toBeVisible();

    const note = `E2E note ${Date.now()}`;
    await page.getByLabel("Add note").fill(note);
    await page.getByRole("button", { name: "Add note" }).click();
    await expect(page.locator("#incident-timeline")).toContainText(note, { timeout: 15_000 });

    await page.getByRole("button", { name: "Resolve" }).click();
    await expect(
      page.locator("section[aria-label='Incident overview']").getByText("RESOLVED")
    ).toBeVisible({ timeout: 15_000 });

    await page.getByRole("button", { name: "Reopen" }).click();
    await expect(page.locator("section[aria-label='Incident overview']").getByText("OPEN")).toBeVisible({
      timeout: 15_000,
    });

    await page.reload();
    await expect(page.locator("section[aria-label='Incident overview']")).toBeVisible();
  });

  test("deployment section visible on incident", async ({ page, incidentReady }) => {
    await primeSession(page, incidentReady.token);
    await page.goto(`/projects/${incidentReady.projectId}/incidents/${incidentReady.incidentId}`);
    await expect(page.getByRole("heading", { name: "Deployment information" })).toBeVisible();
  });
});