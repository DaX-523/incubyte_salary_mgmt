import { cacheLife } from "next/cache";
import { connection } from "next/server";

import { request } from "./client";
import type {
  Employee,
  EmployeeCreate,
  EmployeeUpdate,
  FilterOptions,
  MonthlyEmployee,
  MonthlyEmployeeQuery,
  Page,
  PayByJobTitle,
  Payroll,
  PayrollCreate,
  PayrollStatus,
  PayrollStatusQuery,
  PayrollUpdate,
} from "./types";

export { ApiError } from "./client";
export type * from "./types";

export function listEmployeesForMonth(query: MonthlyEmployeeQuery) {
  return request<Page<MonthlyEmployee>>("GET", "/employees", { query });
}

export function getEmployee(id: number) {
  return request<Employee>("GET", `/employees/${id}`);
}

export function createEmployee(body: EmployeeCreate) {
  return request<Employee>("POST", "/employees", { body });
}

export function updateEmployee(id: number, body: EmployeeUpdate) {
  return request<Employee>("PATCH", `/employees/${id}`, { body });
}

export function deactivateEmployee(id: number) {
  return request<void>("DELETE", `/employees/${id}`);
}

export function createPayroll(employeeId: number, body: PayrollCreate) {
  return request<Payroll>("POST", `/employees/${employeeId}/payrolls`, {
    body,
  });
}

export function getPayroll(id: number) {
  return request<Payroll>("GET", `/payrolls/${id}`);
}

export function updatePayroll(id: number, body: PayrollUpdate) {
  return request<Payroll>("PATCH", `/payrolls/${id}`, { body });
}

export function getPayrollStatus(query: PayrollStatusQuery) {
  return request<PayrollStatus>("GET", "/insights/payroll-status", { query });
}

export function getPayByJobTitle(country: string) {
  return request<PayByJobTitle>("GET", "/insights/pay-by-job-title", {
    query: { country },
  });
}

/**
 * The catalog only changes when the backend is redeployed, so it is cached for an hour instead of
 * fetched on every page render. Waiting for a request first keeps `next build` from calling the
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
