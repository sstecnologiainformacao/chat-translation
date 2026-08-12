import type {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
} from "@/types/auth";

const DEFAULT_API_URL = "http://localhost:8000";

type RequestOptions = {
  apiBaseUrl?: string;
  fetcher?: typeof fetch;
};

export class ApiError extends Error {
  readonly status: number;
  readonly detail: string;

  constructor({ status, detail }: { status: number; detail: string }) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

export function getApiBaseUrl(
  apiUrl: string | undefined = import.meta.env.VITE_API_URL,
): string {
  const trimmed = apiUrl?.trim();

  if (!trimmed) {
    return DEFAULT_API_URL;
  }

  return trimmed.replace(/\/+$/, "");
}

export function buildApiUrl(path: string, apiBaseUrl?: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${getApiBaseUrl(apiBaseUrl)}${normalizedPath}`;
}

export function buildWebSocketUrl(
  path: string,
  token: string,
  apiBaseUrl?: string,
): string {
  const url = new URL(buildApiUrl(path, apiBaseUrl));
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.searchParams.set("token", token);
  return url.toString();
}

export async function login(
  payload: LoginRequest,
  { apiBaseUrl, fetcher = fetch }: RequestOptions = {},
): Promise<LoginResponse> {
  let response: Response;

  try {
    response = await fetcher(buildApiUrl("/auth/login", apiBaseUrl), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
  } catch {
    throw new ApiError({ status: 0, detail: "network_error" });
  }

  if (!response.ok) {
    throw new ApiError({
      status: response.status,
      detail: await readErrorDetail(response),
    });
  }

  return (await response.json()) as LoginResponse;
}

export async function register(
  payload: RegisterRequest,
  { apiBaseUrl, fetcher = fetch }: RequestOptions = {},
): Promise<RegisterResponse> {
  let response: Response;

  try {
    response = await fetcher(buildApiUrl("/auth/register", apiBaseUrl), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
  } catch {
    throw new ApiError({ status: 0, detail: "network_error" });
  }

  if (!response.ok) {
    throw new ApiError({
      status: response.status,
      detail: await readErrorDetail(response),
    });
  }

  return (await response.json()) as RegisterResponse;
}

async function readErrorDetail(response: Response): Promise<string> {
  try {
    const data: unknown = await response.json();

    if (isErrorBody(data)) {
      return data.detail;
    }
  } catch {
    return "request_failed";
  }

  return "request_failed";
}

function isErrorBody(data: unknown): data is { detail: string } {
  return (
    typeof data === "object" &&
    data !== null &&
    "detail" in data &&
    typeof data.detail === "string"
  );
}
