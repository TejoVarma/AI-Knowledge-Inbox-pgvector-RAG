import { beforeEach, describe, expect, it, vi } from "vitest";
import * as api from "../api/client";
import type { User } from "../types";
import { useAuthStore } from "./useAuthStore";

vi.mock("../api/client");

const user: User = { id: "u1", name: "Tejo", email: "tejo@example.com", created_at: "2026-11-01T10:00:00Z" };

beforeEach(() => {
  vi.resetAllMocks();
  useAuthStore.setState({ status: "authenticated", user, error: null, logoutError: null });
});

describe("checkSession", () => {
  it("treats a server error as a server problem, not as being logged out", async () => {
    vi.mocked(api.fetchCurrentUser).mockRejectedValue({ message: "Something went wrong.", status: 500 });

    await useAuthStore.getState().checkSession();

    expect(useAuthStore.getState().status).toBe("unreachable");
  });

  it("treats a 401 as logged out", async () => {
    vi.mocked(api.fetchCurrentUser).mockRejectedValue({ message: "not authenticated", status: 401 });

    await useAuthStore.getState().checkSession();

    expect(useAuthStore.getState().status).toBe("anonymous");
  });
});

describe("logout", () => {
  it("clears the session when the server confirms", async () => {
    vi.mocked(api.logout).mockResolvedValue(undefined);

    await useAuthStore.getState().logout();

    expect(useAuthStore.getState().status).toBe("anonymous");
    expect(useAuthStore.getState().user).toBeNull();
  });

  it("stays logged in and says so when the request fails", async () => {
    vi.mocked(api.logout).mockRejectedValue({ message: "Can't reach the server.", unreachable: true });

    await useAuthStore.getState().logout();

    expect(useAuthStore.getState().status).toBe("authenticated");
    expect(useAuthStore.getState().logoutError).toMatch(/couldn't log out/i);
  });
});
