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

export function getFilterOptions() {
  return request<FilterOptions>("GET", "/filters");
}
