import { expect, test } from "./fixtures";
import { assertNoHorizontalOverflow } from "./helpers/assertions";
import { primeSession } from "./helpers/auth-browser";
import { captureE2e } from "./helpers/screenshots";

const VIEWPORTS = [
  { width: 360, height: 800 },
  { width: 390, height: 844 },
  { width: 768, height: 1024 },
  { width: 1366, height: 768 },
  { width: 1920, height: 1080 },
];

test.describe("Responsive layout", () => {
  for (const viewport of VIEWPORTS) {
    test(`incident detail at ${viewport.width}×${viewport.height}`, async ({ page, incidentReady }) => {
      await page.setViewportSize(viewport);
      await primeSession(page, incidentReady.token);
      await page.goto(`/projects/${incidentReady.projectId}/incidents/${incidentReady.incidentId}`);

      await expect(page.locator("section[aria-label='Incident overview']")).toBeVisible();
      await expect(page.locator('[aria-label="Root cause analysis"]')).toBeVisible();
      await assertNoHorizontalOverflow(page);

      if (viewport.width === 1920) {
        await captureE2e(page, "dashboard-overview-responsive");
      }
    });
  }

  test("RCA panel at narrow and wide widths", async ({ page, incidentReady }) => {
    for (const width of [360, 1920]) {
      await page.setViewportSize({ width, height: 800 });
      await primeSession(page, incidentReady.token);
      await page.goto(`/projects/${incidentReady.projectId}/incidents/${incidentReady.incidentId}`);
      const rca = page.locator('[aria-label="Root cause analysis"]');
      await rca.getByRole("button", { name: "Run RCA investigation" }).click();
      await expect(rca.getByRole("listbox", { name: "Root cause candidates" })).toBeVisible({
        timeout: 120_000,
      });
      await assertNoHorizontalOverflow(page);
    }
  });
});