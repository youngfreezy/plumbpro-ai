import { test, expect } from "@playwright/test";

test.describe("Navigation & Page Load", () => {
  test("landing page loads without errors", async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (err) => errors.push(err.message));
    await page.goto("/");
    await expect(page.locator("body")).toBeVisible();
    expect(errors).toHaveLength(0);
  });

  test("login page loads without errors", async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (err) => errors.push(err.message));
    await page.goto("/auth/login");
    await expect(page.locator("body")).toBeVisible();
    expect(errors).toHaveLength(0);
  });

  test("register page loads without errors", async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (err) => errors.push(err.message));
    await page.goto("/auth/register");
    await expect(page.locator("body")).toBeVisible();
    expect(errors).toHaveLength(0);
  });

  test("should have proper meta tags", async ({ page }) => {
    await page.goto("/");
    const description = await page
      .locator('meta[name="description"]')
      .getAttribute("content");
    expect(description).toBeTruthy();
  });

  test("should have responsive viewport", async ({ page }) => {
    await page.goto("/");
    // Check that content is visible on mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.locator("body")).toBeVisible();
    const h1 = page.getByRole("heading", { level: 1 }).first();
    await expect(h1).toBeVisible();
  });
});
