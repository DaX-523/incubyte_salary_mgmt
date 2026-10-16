import { cacheLife } from "next/cache";
import { redirect } from "next/navigation";
import { connection } from "next/server";

import { getSessionToken } from "@/lib/session";

import { ApiError, request, type RequestOptions } from "./client";
import type {
  Employee,
  EmployeeCreate,
  EmployeeUpdate,
  FilterOptions,
  LoginToken,
  MonthlyEmployee,
  MonthlyEmployeeQuery,
  Page,
  PayByJobTitle,
  Payroll,
  PayrollCreate,
  PayrollStatus,
  PayrollStatusQuery,
  PayrollUpdate,
  Profile,
} from "./types";

export { ApiError } from "./client";
export type * from "./types";

const LOGIN_PATH = "/login";

/**
 * Calls the API as the logged-in user. When the API rejects the session (expired, or logged out
 * elsewhere), the user is sent to log in again.
 */
async function authorized<Result>(
  method: "GET" | "POST" | "PATCH" | "DELETE",
  path: string,
  options: Omit<RequestOptions, "token"> = {},
): Promise<Result> {
  const token = await getSessionToken();
  try {
    return await request<Result>(method, path, { ...options, token });
  } catch (error) {
    if (isUnauthorized(error)) {
      redirect(LOGIN_PATH);
    }
    throw error;
  }
}

function isUnauthorized(error: unknown) {
  return error instanceof ApiError && error.status === 401;
}

/** Exchanges an email and password for a token. Wrong credentials throw an ApiError (401). */
export function login(email: string, password: string) {
  return request<LoginToken>("POST", "/auth/login", {
    body: { email, password },
  });
}

/** Ends every session of the logged-in user. A session that already ended needs nothing more. */
export async function logout() {
  try {
    await request<void>("POST", "/auth/logout", {
      token: await getSessionToken(),
    });
  } catch (error) {
    if (!isUnauthorized(error)) {
      throw error;
    }
  }
}

/** Who is logged in, or null when nobody is (no session, or the API rejected it). */
export async function getProfile(): Promise<Profile | null> {
  const token = await getSessionToken();
  if (token === undefined) {
    return null;
  }
  try {
    return await request<Profile>("GET", "/auth/me", { token });
  } catch (error) {
    if (isUnauthorized(error)) {
      return null;
    }
    throw error;
  }
}

export function listEmployeesForMonth(query: MonthlyEmployeeQuery) {
  return authorized<Page<MonthlyEmployee>>("GET", "/employees", { query });
}

export function getEmployee(id: number) {
  return authorized<Employee>("GET", `/employees/${id}`);
}

export function createEmployee(body: EmployeeCreate) {
  return authorized<Employee>("POST", "/employees", { body });
}

export function updateEmployee(id: number, body: EmployeeUpdate) {
  return authorized<Employee>("PATCH", `/employees/${id}`, { body });
}

export function deactivateEmployee(id: number) {
  return authorized<void>("DELETE", `/employees/${id}`);
}

export function createPayroll(employeeId: number, body: PayrollCreate) {
  return authorized<Payroll>("POST", `/employees/${employeeId}/payrolls`, {
    body,
  });
}

export function getPayroll(id: number) {
  return authorized<Payroll>("GET", `/payrolls/${id}`);
}

export function updatePayroll(id: number, body: PayrollUpdate) {
  return authorized<Payroll>("PATCH", `/payrolls/${id}`, { body });
}

export function getPayrollStatus(query: PayrollStatusQuery) {
  return authorized<PayrollStatus>("GET", "/insights/payroll-status", {
    query,
  });
}

export function getPayByJobTitle(country: string) {
  return authorized<PayByJobTitle>("GET", "/insights/pay-by-job-title", {
    query: { country },
  });
}

/**
 * The catalog is public reference data (the same for every organization, so no token) that only
 * changes when the backend is redeployed, so it is cached for an hour instead of fetched on every
 * page render. Waiting for a request first keeps `next build` from calling the
 * API, so the build does not need the backend running.
 */
export async function getFilterOptions() {
  await connection();
  return cachedFilterOptions();
}

async function cachedFilterOptions() {
  "use cache";
  cacheLife("hours");
  return request<FilterOptions>("GET", "/filters");
}
