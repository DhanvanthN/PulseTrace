import { expect, type Page } from "@playwright/test";

const IGNORED_CONSOLE = [
  /Download the React DevTools/,
  /favicon\.ico/,
  /Failed to load resource.*favicon/,
  /Failed to load resource: the server responded with a status of 401/,
];

export function trackConsoleErrors(page: Page): string[] {
  const errors: string[] = [];
  page.on("pageerror", (err) => errors.push(`pageerror: ${err.message}`));
  page.on("console", (msg) => {
    if (msg.type() === "error") {
      const text = msg.text();
      if (IGNORED_CONSOLE.some((re) => re.test(text))) {
        return;
      }
      errors.push(`console.error: ${text}`);
    }
  });
  return errors;
}

export function assertNoConsoleErrors(errors: string[]): void {
  expect(errors, `Unexpected browser errors:\n${errors.join("\n")}`).toEqual([]);
}

export async function assertNoHorizontalOverflow(page: Page): Promise<void> {
  const overflow = await page.evaluate(() => {
    const doc = document.documentElement;
    return doc.scrollWidth > doc.clientWidth + 2;
  });
  expect(overflow, "page should not scroll horizontally").toBeFalsy();
}