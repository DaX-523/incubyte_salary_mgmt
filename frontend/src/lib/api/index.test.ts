import { beforeEach, describe, expect, it, vi } from "vitest";

import * as api from "./index";

const fetchMock = vi.fn();

beforeEach(() => {
  fetchMock.mockResolvedValue(new Response("{}", { status: 200 }));
  vi.stubGlobal("fetch", fetchMock);
});

function lastCall() {
  const [url, init] = fetchMock.mock.calls.at(-1) as [string, RequestInit];
  return {
    url: url.replace("http://localhost:8000/api/v1", ""),
    method: init.method,
  };
}

const PAYROLL = {
  month: "2026-10",
  base: "1.00",
  bonus: "0",
  esops: "0",
  payment_method: "bank_transfer",
} as const;

describe("API endpoints", () => {
  it.each([
    [
      "listEmployeesForMonth",
      () => api.listEmployeesForMonth({ month: "2026-10", page: 2 }),
      "GET",
      "/employees?month=2026-10&page=2",
    ],
    ["getEmployee", () => api.getEmployee(4), "GET", "/employees/4"],
    [
      "createEmployee",
      () =>
        api.createEmployee({
          name: "A",
          email: "a@x.co",
          monthly_salary: "1",
          country: "GB",
          job_title: "Accountant",
        }),
      "POST",
      "/employees",
    ],
    [
      "updateEmployee",
      () => api.updateEmployee(4, { name: "B" }),
      "PATCH",
      "/employees/4",
    ],
    [
      "deactivateEmployee",
      () => api.deactivateEmployee(4),
      "DELETE",
      "/employees/4",
    ],
    [
      "createPayroll",
      () => api.createPayroll(4, PAYROLL),
      "POST",
      "/employees/4/payrolls",
    ],
    ["getPayroll", () => api.getPayroll(8), "GET", "/payrolls/8"],
    [
      "updatePayroll",
      () => api.updatePayroll(8, { bonus: "5" }),
      "PATCH",
      "/payrolls/8",
    ],
    [
      "getPayrollStatus",
      () => api.getPayrollStatus({ month: "2026-10", country: "DE" }),
      "GET",
      "/insights/payroll-status?month=2026-10&country=DE",
    ],
    [
      "getPayByJobTitle",
      () => api.getPayByJobTitle("JP"),
      "GET",
      "/insights/pay-by-job-title?country=JP",
    ],
    ["getFilterOptions", () => api.getFilterOptions(), "GET", "/filters"],
  ])("%s calls %s %s", async (_, call, method, path) => {
    await call();

    expect(lastCall()).toEqual({ url: path, method });
  });
});
