import { E2E_API_URL, expect, test } from "./fixtures";

/** Minimal gate — detailed checks live in feature specs. */
test.describe("PulseTrace smoke", () => {
  test("API health and login page", async ({ page, api }) => {
    await api.assertReachable();
    await page.goto("/login");
    await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
    void E2E_API_URL;
  });
});