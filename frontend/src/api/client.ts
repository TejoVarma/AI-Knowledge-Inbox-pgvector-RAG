import axios from "axios";
import type { IngestPayload, Item, QueryResponse } from "../types";
import { normalizeApiError } from "../utils/normalizeApiError";

// same origin on purpose: the vite proxy (local) and the vercel rewrite (production)
// forward /api to the backend, so the login cookie stays first-party
export const apiClient = axios.create({
  baseURL: "/api",
  timeout: 30000,
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(normalizeApiError(error))
);

export const ingestItem = (payload: IngestPayload) =>
  apiClient.post<Item>("/ingest", payload).then((r) => r.data);

export const listItems = () => apiClient.get<Item[]>("/items").then((r) => r.data);

export const askQuestion = (question: string) =>
  apiClient.post<QueryResponse>("/query", { question }).then((r) => r.data);

export const deleteItem = (id: string) => apiClient.delete(`/items/${id}`).then(() => undefined);
