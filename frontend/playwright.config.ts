import { defineConfig, devices } from "@playwright/test";

// e2e tests drive a real browser against a production build of the app (vite preview),
// which proxies /api to the backend just like the dev server does. a production build
// rather than the dev server because the dev server's hot-reload websocket changes browser
// behaviour - pages with an open websocket never enter the back/forward cache
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: "http://localhost:4173",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        // full chromium, and without playwright's default --disable-back-forward-cache:
        // real browsers keep pages in that cache, and one of the logout tests needs it
        channel: "chromium",
        launchOptions: { ignoreDefaultArgs: ["--disable-back-forward-cache"] },
      },
    },
  ],
  webServer: {
    command: "pnpm run build && pnpm exec vite preview --port 4173 --strictPort",
    url: "http://localhost:4173",
    reuseExistingServer: !process.env.CI,
  },
});
