import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test.describe("Home Page", () => {
  test("should load the home page", async ({ page }) => {
    await page.goto("/");

    // Check for the main heading
    await expect(page.getByRole("heading", { name: /create.*t3.*app/i })).toBeVisible();
  });

  test("should display tRPC query result", async ({ page }) => {
    await page.goto("/");

    // Wait for the tRPC query to load
    await expect(page.getByText(/hello from trpc/i)).toBeVisible();
  });

  test("should have no accessibility violations", async ({ page }) => {
    await page.goto("/");

    // Run accessibility scan
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();

    // Assert no accessibility violations
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test("should navigate between sections", async ({ page }) => {
    await page.goto("/");

    // Check that both cards are visible using more reliable selectors
    await expect(page.getByRole("heading", { name: /first steps/i })).toBeVisible();
    await expect(page.getByRole("heading", { name: /documentation/i })).toBeVisible();
  });
});
