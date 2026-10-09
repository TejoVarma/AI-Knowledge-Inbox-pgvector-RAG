import { create } from "zustand";
import * as api from "../api/client";
import type { ApiError, User } from "../types";
import { useInboxStore } from "./useInboxStore";

type AuthStatus = "checking" | "anonymous" | "authenticated";

interface AuthState {
  status: AuthStatus;
  user: User | null;
  error: string | null;
  sessionExpired: boolean;
  isSubmitting: boolean;

  checkSession: () => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  expireSession: () => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  status: "checking",
  user: null,
  error: null,
  sessionExpired: false,
  isSubmitting: false,

  // the cookie is invisible to us, so the only way to know is to ask the backend
  checkSession: async () => {
    try {
      const user = await api.fetchCurrentUser();
      set({ status: "authenticated", user });
    } catch {
      set({ status: "anonymous", user: null });
    }
  },

  login: async (email, password) => {
    if (get().isSubmitting) return;
    set({ isSubmitting: true, error: null, sessionExpired: false });
    try {
      const user = await api.login(email, password);
      set({ status: "authenticated", user, isSubmitting: false });
    } catch (err) {
      set({ error: (err as ApiError).message, isSubmitting: false });
    }
  },

  register: async (name, email, password) => {
    if (get().isSubmitting) return;
    set({ isSubmitting: true, error: null, sessionExpired: false });
    try {
      await api.register(name, email, password);
      // straight in - nobody wants to type the same details twice
      const user = await api.login(email, password);
      set({ status: "authenticated", user, isSubmitting: false });
    } catch (err) {
      set({ error: (err as ApiError).message, isSubmitting: false });
    }
  },

  logout: async () => {
    try {
      await api.logout();
    } finally {
      useInboxStore.getState().reset();
      set({ status: "anonymous", user: null, error: null, sessionExpired: false });
    }
  },

  expireSession: () => {
    if (get().status !== "authenticated") return;
    useInboxStore.getState().reset();
    set({ status: "anonymous", user: null, sessionExpired: true });
  },

  clearError: () => set({ error: null }),
}));

api.setSessionExpiredHandler(() => useAuthStore.getState().expireSession());
