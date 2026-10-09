interface ValidationDetail {
  msg: string;
}

interface RawApiError {
  response?: { status?: number; data?: { detail?: string | ValidationDetail[] } };
  code?: string;
}

export function normalizeApiError(error: RawApiError): { message: string; status?: number } {
  const detail = error.response?.data?.detail;
  let message = "Something went wrong. Please try again.";

  if (typeof detail === "string") {
    message = detail;
  } else if (Array.isArray(detail) && detail[0]?.msg) {
    message = detail[0].msg.replace(/^Value error, /, "");
  } else if (error.code === "ECONNABORTED") {
    message = "Request timed out — the server may be busy.";
  } else if (!error.response) {
    message = "Can't reach the server. Is the backend running?";
  }

  return { message, status: error.response?.status };
}
