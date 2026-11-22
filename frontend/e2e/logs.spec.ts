import path from "node:path";
import { fileURLToPath } from "node:url";

import { expect, test } from "./fixtures";
import { buildRecentJsonlSpike } from "./helpers/data";
import { primeSession } from "./helpers/auth-browser";
import { uniqueE2eEmail } from "./helpers/constants";

const sampleJsonl = path.resolve(fileURLToPath(new URL(".", import.meta.url)), "fixtures/sample.jsonl");

test.describe("Log management", () => {
  test("upload validation rejects unsupported extension", async ({ page, logReady }) => {
    await primeSession(page, logReady.token);
    await page.goto(`/projects/${logReady.projectId}/logs/upload`);

    await page.locator('input[type="file"]').setInputFiles({
      name: "malware.exe",
      mimeType: "application/octet-stream",
      buffer: Buffer.from("bad"),
    });
    await expect(page.getByRole("alert")).toContainText(/Unsupported format/i);
    await expect(page.getByRole("button", { name: "Upload and process" })).toBeDisabled();
  });

  test("upload via UI processes JSONL", async ({ page, api }) => {
    const email = uniqueE2eEmail("upload-ui");
    const token = await api.registerAndLogin(email).then((r) => r.token);
    const project = await api.createProject(token, `Upload UI ${Date.now().toString(36)}`);
    await primeSession(page, token);

    await page.goto(`/projects/${project.id}/logs/upload`);
    await page.locator('input[type="file"]').setInputFiles({
      name: "ui-spike.jsonl",
      mimeType: "application/json",
      buffer: buildRecentJsonlSpike(),
    });
    await page.getByRole("button", { name: "Upload and process" }).click();
    await expect(page.getByText(/Processed \d+/)).toBeVisible({ timeout: 60_000 });
    await page.getByRole("link", { name: "Open log explorer" }).click();
    await expect(page.getByRole("heading", { name: "Search logs" })).toBeVisible();
  });

  test("log explorer search filter and pagination", async ({ page, logReady }) => {
    await primeSession(page, logReady.token);
    await page.goto(`/projects/${logReady.projectId}/logs`);

    await page.getByLabel("Keyword").fill("database");
    await expect(page.locator("table tbody tr").first()).toBeVisible({ timeout: 15_000 });

    await page.getByLabel("Level").selectOption("ERROR");
    await page.getByRole("button", { name: "Clear filters" }).click();
    await page.getByLabel("Keyword").fill("database");
    await expect(page.locator("table tbody tr").first()).toBeVisible({ timeout: 15_000 });

    const next = page.getByRole("button", { name: "Next" });
    if (await next.isEnabled()) {
      await next.click();
      await expect(page.getByRole("button", { name: "Previous" })).toBeEnabled();
    }

    await page.getByTestId("log-row-view").first().click();
    await expect(page.getByRole("heading", { name: "Log details" })).toBeVisible({ timeout: 20_000 });
    await expect(page.getByTestId("log-detail-panel")).toBeVisible();
  });

  test("fixture sample upload shows partial completion", async ({ page, api }) => {
    const email = uniqueE2eEmail("sample-upload");
    const token = await api.registerAndLogin(email).then((r) => r.token);
    const project = await api.createProject(token, `Fixture ${Date.now().toString(36)}`);
    await primeSession(page, token);

    await page.goto(`/projects/${project.id}/logs/upload`);
    await page.locator('input[type="file"]').setInputFiles(sampleJsonl);
    await page.getByRole("button", { name: "Upload and process" }).click();
    await expect(page.getByText(/Failed \d+/)).toBeVisible({ timeout: 60_000 });
  });
});