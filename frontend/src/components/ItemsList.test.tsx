import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import * as api from "../api/client";
import { useInboxStore } from "../store/useInboxStore";
import type { Item } from "../types";
import { ItemsList } from "./ItemsList";

vi.mock("../api/client");

const item: Item = {
  id: "i1",
  source_type: "note",
  source_ref: null,
  content: "a saved note",
  suggested_question: null,
  created_at: "2026-11-01T10:00:00Z",
  chunk_count: 1,
};

beforeEach(() => {
  vi.resetAllMocks();
  useInboxStore.getState().reset();
});
afterEach(cleanup);

it("shows a failed load instead of claiming nothing is saved, and can retry", async () => {
  vi.mocked(api.listItems)
    .mockRejectedValueOnce({ message: "Can't reach the server." })
    .mockResolvedValueOnce([item]);

  render(<ItemsList />);

  expect((await screen.findByRole("alert")).textContent).toContain("Can't reach the server.");
  expect(screen.queryByText(/nothing saved yet/i)).toBeNull();

  fireEvent.click(screen.getByRole("button", { name: /try again/i }));

  expect(await screen.findByText("a saved note")).toBeTruthy();
  expect(screen.queryByRole("alert")).toBeNull();
});

it("shows a failed delete and keeps the item", async () => {
  vi.mocked(api.listItems).mockResolvedValue([item]);
  vi.mocked(api.deleteItem).mockRejectedValue({ message: "item not found" });
  render(<ItemsList />);
  await screen.findByText("a saved note");

  await act(() => useInboxStore.getState().removeItem(item.id));

  expect(screen.getByRole("alert").textContent).toContain("item not found");
  expect(screen.getByText("a saved note")).toBeTruthy();
});
