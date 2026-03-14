import { defineConfig, devices } from "@playwright/test";

const PORT = process.env.TEST_PORT || "3100";
const BASE_URL = `http://localhost:${PORT}`;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: "html",
  use: {
    baseURL: BASE_URL,
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    command: `npx next dev -p ${PORT}`,
    url: BASE_URL,
    reuseExistingServer: false,
    timeout: 120000,
    env: {
      NEXT_PUBLIC_API_URL: "http://localhost:8000",
      NEXTAUTH_SECRET: "test-secret-for-e2e",
      NEXTAUTH_URL: BASE_URL,
    },
  },
});
