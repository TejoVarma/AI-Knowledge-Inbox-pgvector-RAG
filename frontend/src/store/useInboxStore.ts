import { create } from "zustand";
import { ingestItem, listItems, askQuestion, deleteItem } from "../api/client";
import type { Item, IngestPayload, SourceSnippet, ApiError } from "../types";

interface InboxState {
  items: Item[];
  isLoadingItems: boolean;
  itemsError: string | null;
  deletingIds: string[];

  isSaving: boolean;
  saveError: string | null;

  question: string;
  answer: string | null;
  sources: SourceSnippet[];
  isAsking: boolean;
  askError: string | null;

  fetchItems: () => Promise<void>;
  saveItem: (payload: IngestPayload) => Promise<{ ok: boolean; error?: string }>;
  removeItem: (id: string) => Promise<void>;
  clearSaveError: () => void;
  setQuestion: (question: string) => void;
  ask: () => Promise<void>;
}

export const useInboxStore = create<InboxState>((set, get) => ({
  items: [],
  isLoadingItems: false,
  itemsError: null,
  deletingIds: [],

  isSaving: false,
  saveError: null,

  question: "",
  answer: null,
  sources: [],
  isAsking: false,
  askError: null,

  fetchItems: async () => {
    set({ isLoadingItems: true, itemsError: null });
    try {
      const items = await listItems();
      set({ items, isLoadingItems: false });
    } catch (err) {
      set({ itemsError: (err as ApiError).message, isLoadingItems: false });
    }
  },

  saveItem: async (payload) => {
    if (get().isSaving) return { ok: false };
    set({ isSaving: true, saveError: null });
    try {
      await ingestItem(payload);
      set({ isSaving: false });
      await get().fetchItems();
      return { ok: true };
    } catch (err) {
      const message = (err as ApiError).message;
      set({ isSaving: false, saveError: message });
      return { ok: false, error: message };
    }
  },

  removeItem: async (id) => {
    set((state) => ({ deletingIds: [...state.deletingIds, id] }));
    try {
      await deleteItem(id);
      set((state) => ({
        items: state.items.filter((item) => item.id !== id),
        deletingIds: state.deletingIds.filter((d) => d !== id),
      }));
    } catch (err) {
      set((state) => ({
        itemsError: (err as ApiError).message,
        deletingIds: state.deletingIds.filter((d) => d !== id),
      }));
    }
  },

  clearSaveError: () => set({ saveError: null }),

  setQuestion: (question) => set({ question }),

  ask: async () => {
    const question = get().question.trim();
    if (!question || get().isAsking) return;
    set({ isAsking: true, askError: null, answer: null, sources: [] });
    try {
      const result = await askQuestion(question);
      set({ answer: result.answer, sources: result.sources, isAsking: false });
    } catch (err) {
      set({ askError: (err as ApiError).message, isAsking: false });
    }
  },
}));
