export type SourceType = "note" | "url";

export interface Item {
  id: string;
  source_type: SourceType;
  source_ref: string | null;
  content: string;
  suggested_question: string | null;
  created_at: string;
  chunk_count: number;
}

export type IngestPayload =
  | { source_type: "note"; content: string }
  | { source_type: "url"; url: string };

export interface SourceSnippet {
  item_id: string;
  source_type: string;
  source_ref: string | null;
  chunk_text: string;
  similarity: number;
}

export interface QueryResponse {
  answer: string;
  sources: SourceSnippet[];
}

export interface ApiError {
  message: string;
  status?: number;
  unreachable?: boolean;
}

export interface User {
  id: string;
  name: string | null;
  email: string;
  created_at: string;
}
