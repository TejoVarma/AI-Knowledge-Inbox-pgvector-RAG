interface ValidationDetail {
  msg: string;
}

interface RawApiError {
  response?: { status?: number; data?: { detail?: string | ValidationDetail[] } };
  code?: string;
}

const UNREACHABLE_MESSAGE = "Can't reach the server. Please try again in a moment.";

export function normalizeApiError(error: RawApiError): { message: string; status?: number; unreachable: boolean } {
  const status = error.response?.status;
  const detail = error.response?.data?.detail;

  // no response at all, or a gateway error with no body - that's the proxy (vite locally,
  // vercel in production) saying the backend didn't answer. our own 502s always carry a detail
  const unreachable = !error.response || (!detail && (status === 502 || status === 503 || status === 504));

  let message = "Something went wrong. Please try again.";
  if (typeof detail === "string") {
    message = detail;
  } else if (Array.isArray(detail) && detail[0]?.msg) {
    message = detail[0].msg.replace(/^Value error, /, "");
  } else if (error.code === "ECONNABORTED") {
    message = "Request timed out — the server may be busy.";
  } else if (unreachable) {
    message = UNREACHABLE_MESSAGE;
  }

  return { message, status, unreachable };
}
