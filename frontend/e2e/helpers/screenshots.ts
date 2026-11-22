import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Page } from "@playwright/test";

const E2E_SCREENSHOT_DIR = path.resolve(
  fileURLToPath(new URL(".", import.meta.url)),
  "../../../docs/screenshots/e2e"
);

export async function captureE2e(page: Page, name: string): Promise<void> {
  await page.screenshot({
    path: path.join(E2E_SCREENSHOT_DIR, `${name}.png`),
    fullPage: true,
  });
}