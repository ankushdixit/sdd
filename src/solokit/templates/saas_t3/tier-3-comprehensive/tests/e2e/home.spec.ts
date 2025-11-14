import { test, expect } from "@playwright/test";
import { injectAxe, checkA11y } from "axe-playwright";

test.describe("Home Page", () => {
  test("should load the home page", async ({ page }) => {
    await page.goto("/");

    // Check for the main heading
    await expect(
      page.getByRole("heading", { name: /create.*t3.*app/i }),
    ).toBeVisible();
  });

  test("should display tRPC query result", async ({ page }) => {
    await page.goto("/");

    // Wait for the tRPC query to load
    await expect(page.getByText(/hello from trpc/i)).toBeVisible();
  });

  test("should have no accessibility violations", async ({ page }) => {
    await page.goto("/");

    // Inject axe-core
    await injectAxe(page);

    // Check for accessibility violations
    await checkA11y(page, undefined, {
      detailedReport: true,
      detailedReportOptions: {
        html: true,
      },
    });
  });

  test("should navigate between sections", async ({ page }) => {
    await page.goto("/");

    // Check that both cards are visible
    await expect(page.getByText(/first steps/i)).toBeVisible();
    await expect(page.getByText(/documentation/i)).toBeVisible();
  });
});
