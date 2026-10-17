const DEFAULT_API_BASE_URL = "http://localhost:8000";
const API_PREFIX = "/api/v1";

type QueryValue = string | number | undefined;
type ValidationIssue = { loc: (string | number)[]; msg: string };

/** A non-2xx response. `fieldErrors` maps request fields to the API's validation messages. */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
    readonly fieldErrors: Record<string, string> = {},
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export function apiBaseUrl(): string {
  return process.env.API_BASE_URL || DEFAULT_API_BASE_URL;
}

export function buildUrl(
  path: string,
  query: Record<string, QueryValue> = {},
): string {
  const url = new URL(`${API_PREFIX}${path}`, apiBaseUrl());
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== "") {
      url.searchParams.set(key, String(value));
    }
  }
  return url.toString();
}

export type RequestOptions = {
  query?: Record<string, QueryValue>;
  body?: unknown;
  /** The logged-in user's token, sent as `Authorization: Bearer <token>`. */
  token?: string;
  /** "text" returns the body as it came, for downloads such as CSV; the default parses JSON. */
  responseType?: "json" | "text";
};

export async function request<Result>(
  method: "GET" | "POST" | "PATCH" | "DELETE",
  path: string,
  options: RequestOptions = {},
): Promise<Result> {
  let response: Response;
  try {
    response = await fetch(buildUrl(path, options.query), {
      method,
      headers: requestHeaders(options),
      body:
        options.body === undefined ? undefined : JSON.stringify(options.body),
    });
  } catch (cause) {
    throw new Error(`Could not reach the API at ${apiBaseUrl()}`, { cause });
  }
  if (!response.ok) {
    throw await toApiError(response);
  }
  if (response.status === 204) {
    return undefined as Result;
  }
  if (options.responseType === "text") {
    return (await response.text()) as Result;
  }
  return (await response.json()) as Result;
}

function requestHeaders({ body, token }: RequestOptions) {
  const headers: Record<string, string> = {};
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  if (token !== undefined) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

async function toApiError(response: Response): Promise<ApiError> {
  const body: unknown = await response.json().catch(() => null);
  const detail = isRecord(body) ? body.detail : undefined;
  if (typeof detail === "string") {
    return new ApiError(response.status, detail);
  }
  if (Array.isArray(detail)) {
    return validationError(response.status, detail as ValidationIssue[]);
  }
  return new ApiError(
    response.status,
    `The API responded with ${response.status}`,
  );
}

function validationError(status: number, issues: ValidationIssue[]): ApiError {
  const fieldErrors: Record<string, string> = {};
  for (const issue of issues) {
    // loc is ["body", "<field>"] for field errors and ["body"] for whole-request errors.
    const field =
      issue.loc.length > 1
        ? String(issue.loc[issue.loc.length - 1])
        : undefined;
    if (field && !(field in fieldErrors)) {
      fieldErrors[field] = issue.msg;
    }
  }
  return new ApiError(
    status,
    issues.map((issue) => issue.msg).join("; "),
    fieldErrors,
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
