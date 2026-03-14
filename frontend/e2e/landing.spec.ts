import { test, expect } from "@playwright/test";

test.describe("Landing Page", () => {
  test("should display the landing page with hero section", async ({
    page,
  }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/PlumbPro/);
    await expect(
      page.getByRole("heading", { level: 1 }).first()
    ).toBeVisible();
  });

  test("should have CTA buttons in header", async ({ page }) => {
    await page.goto("/");
    // Header has "Sign In" and "Get Started" buttons
    const header = page.locator("header");
    await expect(header.getByText(/sign in/i).first()).toBeVisible();
    await expect(header.getByText(/get started/i).first()).toBeVisible();
  });

  test("should navigate to register page", async ({ page }) => {
    await page.goto("/");
    await page.locator("header").getByText(/get started/i).first().click();
    await expect(page).toHaveURL(/\/register/);
  });

  test("should navigate to login page", async ({ page }) => {
    await page.goto("/");
    await page.locator("header").getByText(/sign in/i).first().click();
    await expect(page).toHaveURL(/\/login/);
  });

  test("should display feature modules", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("Smart Scheduling")).toBeVisible();
    await expect(page.getByText("AI Diagnostics")).toBeVisible();
    await expect(page.getByText("Instant Estimates")).toBeVisible();
  });
});
