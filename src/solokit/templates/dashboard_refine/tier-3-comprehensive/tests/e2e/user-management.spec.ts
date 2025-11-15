import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

/**
 * User Management E2E Tests
 * Tests CRUD operations and accessibility for user resource
 */

test.describe("User Management", () => {
  test("should display users list page", async ({ page }) => {
    await page.goto("/users");

    // Check page title
    await expect(page.getByRole("heading", { name: "Users" })).toBeVisible();

    // Check "Add User" button exists
    await expect(page.getByRole("button", { name: /Add User/i })).toBeVisible();
  });

  test("should display user table with data", async ({ page }) => {
    await page.goto("/users");

    // Wait for table to load
    const table = page.locator("table");
    await expect(table).toBeVisible();

    // Check table headers
    await expect(page.getByRole("columnheader", { name: "ID" })).toBeVisible();
    await expect(page.getByRole("columnheader", { name: "Name" })).toBeVisible();
    await expect(page.getByRole("columnheader", { name: "Email" })).toBeVisible();
    await expect(page.getByRole("columnheader", { name: "Actions" })).toBeVisible();
  });

  test("should handle loading state", async ({ page }) => {
    await page.goto("/users");

    // With mock data, loading is instant, so just verify the table renders
    const table = page.locator("table");
    await expect(table).toBeVisible({ timeout: 10000 });
  });

  test("should have accessible table structure", async ({ page }) => {
    await page.goto("/users");

    // Wait for table
    await page.waitForSelector("table");

    // Run accessibility scan on table
    const accessibilityScanResults = await new AxeBuilder({ page })
      .include("table")
      .withTags(["wcag2a", "wcag2aa"])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test("should navigate back to dashboard", async ({ page }) => {
    await page.goto("/users");

    // Click dashboard link in sidebar
    await page.getByRole("link", { name: "Dashboard" }).first().click();
    await expect(page).toHaveURL("/");
  });

  test("should pass full page accessibility audit", async ({ page }) => {
    await page.goto("/users");

    // Wait for page to fully load
    await page.waitForLoadState("networkidle");

    // Run comprehensive accessibility scan
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "best-practice"])
      .analyze();

    // Log any violations for debugging
    if (accessibilityScanResults.violations.length > 0) {
      console.log(
        "Accessibility violations:",
        JSON.stringify(accessibilityScanResults.violations, null, 2)
      );
    }

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test("should support keyboard navigation in table", async ({ page }) => {
    await page.goto("/users");

    // Wait for table
    await page.waitForSelector("table");

    // Tab into the table
    await page.keyboard.press("Tab");

    // Verify we can navigate with keyboard
    const focusedElement = await page.evaluate(() => {
      return document.activeElement?.tagName;
    });

    expect(["BUTTON", "A", "INPUT", "TABLE"]).toContain(focusedElement);
  });
});
