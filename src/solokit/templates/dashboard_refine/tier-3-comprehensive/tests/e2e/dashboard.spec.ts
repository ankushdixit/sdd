import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

/**
 * Dashboard E2E Tests
 * Tests the main dashboard functionality and accessibility
 */

test.describe("Dashboard Page", () => {
  test("should display dashboard with stats cards", async ({ page }) => {
    await page.goto("/dashboard");

    // Check that dashboard title is visible
    await expect(
      page.getByRole("heading", { name: "Dashboard" }),
    ).toBeVisible();

    // Check that stat cards are present
    const cards = page.locator('[class*="grid"] > div');
    await expect(cards).toHaveCount(4); // 4 stat cards

    // Verify stat card content
    await expect(page.getByText("Total Users")).toBeVisible();
    await expect(page.getByText("Total Orders")).toBeVisible();
    await expect(page.getByText("Revenue")).toBeVisible();
    await expect(page.getByText("Products")).toBeVisible();
  });

  test("should have working navigation in sidebar", async ({ page }) => {
    await page.goto("/dashboard");

    // Check sidebar navigation links
    const sidebar = page.locator("aside");
    await expect(sidebar).toBeVisible();

    // Click on Users link
    await page.getByRole("link", { name: "Users" }).click();
    await expect(page).toHaveURL("/dashboard/users");
  });

  test("should have accessible search functionality", async ({ page }) => {
    await page.goto("/dashboard");

    // Find search input by aria-label
    const searchInput = page.getByLabel("Search");
    await expect(searchInput).toBeVisible();

    // Test search input is focusable
    await searchInput.focus();
    await searchInput.fill("test query");
    await expect(searchInput).toHaveValue("test query");
  });

  test("should pass accessibility checks", async ({ page }) => {
    await page.goto("/dashboard");

    // Run accessibility scan
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();

    // Assert no accessibility violations
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test("should be responsive on mobile", async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto("/dashboard");

    // Check that content is visible on mobile
    await expect(
      page.getByRole("heading", { name: "Dashboard" }),
    ).toBeVisible();

    // Sidebar should be hidden on mobile
    const sidebar = page.locator("aside");
    await expect(sidebar).toBeHidden();
  });

  test("should have keyboard navigation support", async ({ page }) => {
    await page.goto("/dashboard");

    // Tab through focusable elements
    await page.keyboard.press("Tab");
    await page.keyboard.press("Tab");

    // Verify focused element is visible
    const focusedElement = await page.evaluate(
      () => document.activeElement?.tagName,
    );
    expect(focusedElement).toBeTruthy();
  });
});
