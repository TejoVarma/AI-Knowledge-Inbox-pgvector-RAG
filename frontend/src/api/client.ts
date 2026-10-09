import axios from "axios";
import type { IngestPayload, Item, QueryResponse, User } from "../types";
import { normalizeApiError } from "../utils/normalizeApiError";

// same origin on purpose: the vite proxy (local) and the vercel rewrite (production)
// forward /api to the backend, so the login cookie stays first-party
export const apiClient = axios.create({
  baseURL: "/api",
  timeout: 30000,
});

const UNSAFE_METHODS = ["post", "put", "patch", "delete"];

function readCookie(name: string): string | null {
  const match = document.cookie.split("; ").find((row) => row.startsWith(`${name}=`));
  return match ? decodeURIComponent(match.slice(name.length + 1)) : null;
}

// the second half of the double-submit check - read at request time, so a fresh login's
// value is always the one sent
apiClient.interceptors.request.use((config) => {
  if (UNSAFE_METHODS.includes((config.method ?? "get").toLowerCase())) {
    const csrf = readCookie("csrf_token");
    if (csrf) config.headers.set("X-CSRF-Token", csrf);
  }
  return config;
});

// a 401 from these is part of the normal flow (wrong password, not logged in yet),
// not a session that ran out
const AUTH_ROUTES = ["/auth/login", "/auth/register", "/auth/me"];

let onSessionExpired: (() => void) | null = null;

export function setSessionExpiredHandler(handler: () => void) {
  onSessionExpired = handler;
}

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const url: string = error.config?.url ?? "";
    if (error.response?.status === 401 && !AUTH_ROUTES.includes(url)) {
      onSessionExpired?.();
    }
    return Promise.reject(normalizeApiError(error));
  }
);

export const register = (name: string, email: string, password: string) =>
  apiClient.post<User>("/auth/register", { name, email, password }).then((r) => r.data);

export const login = (email: string, password: string) =>
  apiClient.post<User>("/auth/login", { email, password }).then((r) => r.data);

export const logout = () => apiClient.post("/auth/logout").then(() => undefined);

export const fetchCurrentUser = () => apiClient.get<User>("/auth/me").then((r) => r.data);

export const ingestItem = (payload: IngestPayload) =>
  apiClient.post<Item>("/ingest", payload).then((r) => r.data);

export const listItems = () => apiClient.get<Item[]>("/items").then((r) => r.data);

export const askQuestion = (question: string) =>
  apiClient.post<QueryResponse>("/query", { question }).then((r) => r.data);

export const deleteItem = (id: string) => apiClient.delete(`/items/${id}`).then(() => undefined);
