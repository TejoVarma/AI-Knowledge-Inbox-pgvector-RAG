import { expect, test, type Page } from "@playwright/test";

const PASSWORD = "e2e-password-1";

function uniqueEmail(label: string) {
  return `e2e-${label}-${Date.now()}-${Math.floor(Math.random() * 1e6)}@example.com`;
}

async function register(page: Page, name: string, email: string) {
  await page.goto("/register");
  await page.getByLabel("Name").fill(name);
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(PASSWORD);
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page).toHaveURL(/\/inbox$/);
}

async function login(page: Page, email: string) {
  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(PASSWORD);
  await page.getByRole("button", { name: "Log in" }).click();
  await expect(page).toHaveURL(/\/inbox$/);
}

test.describe("routes when logged out", () => {
  for (const path of ["/", "/inbox", "/some-page-that-does-not-exist"]) {
    test(`${path} redirects to /login`, async ({ page }) => {
      await page.goto(path);
      await expect(page).toHaveURL(/\/login$/);
      await expect(page.getByRole("heading", { name: "Welcome back" })).toBeVisible();
    });
  }

  test("login and register link to each other", async ({ page }) => {
    await page.goto("/login");
    await page.getByRole("link", { name: "Create an account" }).click();
    await expect(page).toHaveURL(/\/register$/);
    await page.getByRole("link", { name: "Log in" }).click();
    await expect(page).toHaveURL(/\/login$/);
  });
});

test.describe("register and login", () => {
  test("register lands in the inbox with a greeting", async ({ page }) => {
    await register(page, "Asha Rao", uniqueEmail("register"));
    await expect(page.getByText("Hi,")).toBeVisible();
    await expect(page.getByTitle("Asha Rao")).toBeVisible();
  });

  test("short password keeps the button disabled", async ({ page }) => {
    await page.goto("/register");
    await page.getByLabel("Name").fill("Short");
    await page.getByLabel("Email").fill(uniqueEmail("short"));
    await page.getByLabel("Password").fill("seven77");
    await expect(page.getByRole("button", { name: "Create account" })).toBeDisabled();
    await page.getByLabel("Password").fill("exactly8");
    await expect(page.getByRole("button", { name: "Create account" })).toBeEnabled();
  });

  test("wrong password and unknown email show the same message", async ({ page }) => {
    const email = uniqueEmail("wrongpw");
    await register(page, "Wrong Pw", email);
    await page.getByRole("button", { name: "Log out" }).click();

    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill("not-the-password");
    await page.getByRole("button", { name: "Log in" }).click();
    await expect(page.getByRole("alert")).toHaveText("invalid email or password");

    await page.getByLabel("Email").fill(uniqueEmail("nobody"));
    await page.getByRole("button", { name: "Log in" }).click();
    await expect(page.getByRole("alert")).toHaveText("invalid email or password");
  });

  test("logged-in visits to /login and /register go to /inbox", async ({ page }) => {
    await register(page, "Already In", uniqueEmail("guestonly"));
    for (const path of ["/login", "/register", "/"]) {
      await page.goto(path);
      await expect(page).toHaveURL(/\/inbox$/);
    }
  });

  test("refresh keeps you logged in", async ({ page }) => {
    await register(page, "Refresher", uniqueEmail("refresh"));
    await page.reload();
    await expect(page).toHaveURL(/\/inbox$/);
    await expect(page.getByRole("button", { name: "Log out" })).toBeVisible();
  });
});

test.describe("logout and sessions", () => {
  test("logout goes to /login and back doesn't reopen the inbox", async ({ page }) => {
    await register(page, "Leaver", uniqueEmail("logout"));
    await page.getByRole("button", { name: "Log out" }).click();
    await expect(page).toHaveURL(/\/login$/);

    // redirects replace history entries, so Back may leave the app entirely - what matters
    // is that it never shows the inbox again
    await page.goBack();
    await expect(page.getByRole("button", { name: "Log out" })).toHaveCount(0);
    await expect(page).not.toHaveURL(/\/inbox$/);
  });

  test("a page frozen in the back/forward cache re-checks the session when restored", async ({ page }) => {
    // record whether the browser really restored a frozen page, so this test can't pass
    // by accident in a browser that reloads instead
    await page.addInitScript(() => {
      window.addEventListener("pageshow", (e) => {
        if (e.persisted) sessionStorage.setItem("restored-from-bfcache", "yes");
      });
    });

    const email = uniqueEmail("bfcache");
    await register(page, "Frozen Page", email); // page load A, logged in
    await page.goto("/inbox?again"); // page load B - like typing the address again
    await page.getByRole("button", { name: "Log out" }).click();
    await expect(page).toHaveURL(/\/login$/);

    // a page restored from the cache never fires "load" (it was never reloaded), so only
    // wait for the navigation itself
    await page.goBack({ waitUntil: "commit" }); // restores page load A, frozen while logged in
    await expect(page).toHaveURL(/\/login$/);
    await expect(page.getByRole("button", { name: "Log out" })).toHaveCount(0);
    expect(await page.evaluate(() => sessionStorage.getItem("restored-from-bfcache"))).toBe("yes");
  });

  test("logging out in one tab expires the session in another", async ({ page, context }) => {
    const email = uniqueEmail("tabs");
    await register(page, "Two Tabs", email);
    const second = await context.newPage();
    await second.goto("/inbox");
    await expect(second.getByRole("button", { name: "Log out" })).toBeVisible();

    await page.getByRole("button", { name: "Log out" }).click();
    // wait until the logout has really finished - otherwise the save below can beat it to
    // the server and succeed (a real saved note, and a real openai call)
    await expect(page).toHaveURL(/\/login$/);

    // the second tab still shows the inbox until it next talks to the backend
    await second.getByPlaceholder("Paste a note…").fill("typed after logging out elsewhere");
    await second.getByRole("button", { name: "Save" }).click();
    await expect(second).toHaveURL(/\/login$/);
    await expect(second.getByText("Your session expired. Please log in again.")).toBeVisible();

    // and nothing was saved: log back in and the inbox is still empty
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill(PASSWORD);
    await page.getByRole("button", { name: "Log in" }).click();
    await expect(page.getByText("Nothing saved yet")).toBeVisible();
  });

  test("a second user in the same browser sees only their own inbox", async ({ page }) => {
    const first = uniqueEmail("usera");
    await register(page, "User A", first);
    await page.getByRole("button", { name: "Log out" }).click();
    await expect(page).toHaveURL(/\/login$/);

    await register(page, "User B", uniqueEmail("userb"));
    await expect(page.getByTitle("User B")).toBeVisible();
    await expect(page.getByTitle("User A")).toHaveCount(0);
    await expect(page.getByText("Nothing saved yet")).toBeVisible();

    await page.getByRole("button", { name: "Log out" }).click();
    await expect(page).toHaveURL(/\/login$/);
    await login(page, first);
    await expect(page.getByTitle("User A")).toBeVisible();
  });
});

test.describe("server problems", () => {
  test("an unreachable server shows a retry screen instead of the login page", async ({ page }) => {
    await page.route("**/api/auth/me", (route) => route.fulfill({ status: 502, body: "" }));
    await page.goto("/inbox");
    await expect(page.getByRole("heading", { name: "Can't reach the server" })).toBeVisible();

    await page.unroute("**/api/auth/me");
    await page.getByRole("button", { name: "Try again" }).click();
    await expect(page).toHaveURL(/\/login$/);
  });

  test("login while the server is unreachable explains it", async ({ page }) => {
    await page.goto("/login");
    await page.route("**/api/auth/login", (route) => route.fulfill({ status: 502, body: "" }));
    await page.getByLabel("Email").fill(uniqueEmail("down"));
    await page.getByLabel("Password").fill(PASSWORD);
    await page.getByRole("button", { name: "Log in" }).click();
    await expect(page.getByRole("alert")).toHaveText("Can't reach the server. Please try again in a moment.");
  });
});

test.describe("layout", () => {
  test("a long name doesn't break the header on a phone", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    const longName = "Bartholomew Alexander Fitzgerald-Montgomery of Kensington";
    await register(page, longName, uniqueEmail("longname"));

    const header = page.locator("header");
    const headerBox = await header.boundingBox();
    expect(headerBox!.height).toBeLessThan(100);
    await expect(page.getByTitle(longName)).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  });
});
