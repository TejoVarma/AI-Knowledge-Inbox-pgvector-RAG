import { defineConfig, devices } from "@playwright/test";

// set E2E_BASE_URL to run the same tests against a deployed site instead of a local build,
// e.g. E2E_BASE_URL=https://ai-knowledge-inbox-pgvector-rag.vercel.app pnpm test:e2e
const deployedUrl = process.env.E2E_BASE_URL;

// e2e tests drive a real browser against a production build of the app (vite preview),
// which proxies /api to the backend just like the dev server does. a production build
// rather than the dev server because the dev server's hot-reload websocket changes browser
// behaviour - pages with an open websocket never enter the back/forward cache
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  // a free-tier backend has a fraction of a cpu; 16 parallel sign-ups (argon2 is slow on
  // purpose) can push a step past the default timeout, so go easier on deployed sites
  workers: deployedUrl ? 4 : undefined,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: deployedUrl ?? "http://localhost:4173",
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
  webServer: deployedUrl
    ? undefined
    : {
        command: "pnpm run build && pnpm exec vite preview --port 4173 --strictPort",
        url: "http://localhost:4173",
        reuseExistingServer: !process.env.CI,
      },
});
