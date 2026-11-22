import { expect, test } from "./fixtures";
import { primeSession } from "./helpers/auth-browser";
import { captureE2e } from "./helpers/screenshots";

test.describe("Root cause analysis", () => {
  test("investigation, candidates, evidence, report and export", async ({ page, incidentReady }) => {
    await primeSession(page, incidentReady.token);
    await page.goto(`/projects/${incidentReady.projectId}/incidents/${incidentReady.incidentId}`);

    const rca = page.locator('[aria-label="Root cause analysis"]');
    await rca.getByRole("button", { name: "Run RCA investigation" }).click();

    await expect(rca.getByText(/Completed · \d+ candidates/)).toBeVisible({ timeout: 120_000 });
    await captureE2e(page, "rca-candidates");

    await expect(rca.getByRole("listbox", { name: "Root cause candidates" }).getByRole("option").first()).toBeVisible();
    await rca.getByRole("listbox", { name: "Root cause candidates" }).getByRole("option").first().click();

    await expect(rca.getByRole("meter", { name: /Evidence strength/i })).toBeVisible();
    await expect(rca.getByText(/Weighted score — not calibrated probability/i)).toBeVisible();
    await expect(rca.getByRole("heading", { name: "Supporting evidence" })).toBeVisible();
    await captureE2e(page, "rca-evidence");

    await expect(rca.getByRole("heading", { name: "Investigation report" })).toBeVisible({ timeout: 30_000 });
    await captureE2e(page, "investigation-report");

    const exportBtn = rca.getByRole("button", { name: "Export Markdown" });
    await expect(exportBtn).toBeEnabled();
    await exportBtn.click();
  });

  test("RCA shows guidance when no investigation yet", async ({ page, logReady, api }) => {
    await primeSession(page, logReady.token);
    await page.goto(`/projects/${logReady.projectId}/analysis`);
    await page.getByRole("button", { name: "Run analysis" }).click();
    await expect(page.getByText(/completed/i)).toBeVisible({ timeout: 120_000 });
    await api.correlate(logReady.token, logReady.projectId);
    const incidents = await api.listIncidents(logReady.token, logReady.projectId);
    const incidentId = incidents.items[0].id;

    await page.goto(`/projects/${logReady.projectId}/incidents/${incidentId}`);
    const rca = page.locator('[aria-label="Root cause analysis"]');
    await expect(rca.getByText(/No candidates yet/i)).toBeVisible();
    await expect(rca.getByRole("button", { name: "Export Markdown" })).toBeDisabled();
  });
});