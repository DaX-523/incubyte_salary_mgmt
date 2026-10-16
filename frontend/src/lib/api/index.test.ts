import { cacheLife } from "next/cache";
import { redirect } from "next/navigation";
import { connection } from "next/server";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { getSessionToken } from "@/lib/session";

import * as api from "./index";

vi.mock("next/cache", () => ({ cacheLife: vi.fn() }));
vi.mock("next/navigation", () => ({ redirect: vi.fn() }));
vi.mock("next/server", () => ({ connection: vi.fn() }));
vi.mock("@/lib/session", () => ({ getSessionToken: vi.fn() }));

const TOKEN = "session-token";
const PROFILE = {
  name: "ACME HR",
  email: "hr@acme.example",
  organization: "ACME",
};
const fetchMock = vi.fn();
// redirect() never returns: it throws to stop rendering.
const redirected = new Error("NEXT_REDIRECT");

beforeEach(() => {
  respondWith(200, {});
  vi.stubGlobal("fetch", fetchMock);
  vi.mocked(connection).mockResolvedValue(undefined);
  vi.mocked(getSessionToken).mockResolvedValue(TOKEN);
  vi.mocked(redirect).mockImplementation(() => {
    throw redirected;
  });
});

function respondWith(status: number, body?: unknown) {
  fetchMock.mockResolvedValue(
    new Response(body === undefined ? null : JSON.stringify(body), { status }),
  );
}

function lastCall() {
  const [url, init] = fetchMock.mock.calls.at(-1) as [string, RequestInit];
  return {
    url: url.replace("http://localhost:8000/api/v1", ""),
    method: init.method,
  };
}

function lastHeaders() {
  const [, init] = fetchMock.mock.calls.at(-1) as [string, RequestInit];
  return init.headers as Record<string, string>;
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
  ])("%s calls %s %s as the logged-in user", async (_, call, method, path) => {
    await call();

    expect(lastCall()).toEqual({ url: path, method });
    expect(lastHeaders().Authorization).toBe(`Bearer ${TOKEN}`);
  });

  it("sends a user whose session the API rejects to the login page", async () => {
    respondWith(401, { detail: "Your session has ended; log in again" });

    await expect(api.getEmployee(4)).rejects.toBe(redirected);

    expect(redirect).toHaveBeenCalledWith("/login");
  });

  it("passes other API errors on", async () => {
    respondWith(404, { detail: "Employee 4 not found" });

    await expect(api.getEmployee(4)).rejects.toThrow("Employee 4 not found");
    expect(redirect).not.toHaveBeenCalled();
  });
});

describe("login", () => {
  it("posts the credentials without a session token", async () => {
    await api.login("hr@acme.example", "secret");

    const [, init] = fetchMock.mock.calls.at(-1) as [string, RequestInit];
    expect(lastCall()).toEqual({ url: "/auth/login", method: "POST" });
    expect(init.body).toBe('{"email":"hr@acme.example","password":"secret"}');
    expect(lastHeaders().Authorization).toBeUndefined();
  });

  it("reports wrong credentials instead of redirecting", async () => {
    respondWith(401, { detail: "Email or password is incorrect" });

    await expect(api.login("hr@acme.example", "wrong")).rejects.toThrow(
      "Email or password is incorrect",
    );
    expect(redirect).not.toHaveBeenCalled();
  });
});

describe("logout", () => {
  it("ends the session with its token", async () => {
    respondWith(204);

    await api.logout();

    expect(lastCall()).toEqual({ url: "/auth/logout", method: "POST" });
    expect(lastHeaders().Authorization).toBe(`Bearer ${TOKEN}`);
  });

  it("needs nothing more when the session had already ended", async () => {
    respondWith(401, { detail: "Your session has ended; log in again" });

    await expect(api.logout()).resolves.toBeUndefined();
  });

  it("passes other API errors on", async () => {
    respondWith(500);

    await expect(api.logout()).rejects.toThrow("The API responded with 500");
  });
});

describe("getProfile", () => {
  it("returns who is logged in", async () => {
    respondWith(200, PROFILE);

    await expect(api.getProfile()).resolves.toEqual(PROFILE);
    expect(lastCall()).toEqual({ url: "/auth/me", method: "GET" });
  });

  it("is null without a session, and does not call the API", async () => {
    vi.mocked(getSessionToken).mockResolvedValue(undefined);

    await expect(api.getProfile()).resolves.toBeNull();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("is null when the API rejects the session", async () => {
    respondWith(401, { detail: "Your session has ended; log in again" });

    await expect(api.getProfile()).resolves.toBeNull();
  });

  it("passes other API errors on", async () => {
    respondWith(500);

    await expect(api.getProfile()).rejects.toThrow(
      "The API responded with 500",
    );
  });
});

describe("getFilterOptions", () => {
  it("fetches the public catalog without a session token", async () => {
    await api.getFilterOptions();

    expect(lastCall()).toEqual({ url: "/filters", method: "GET" });
    expect(lastHeaders().Authorization).toBeUndefined();
  });

  it("waits for a request before calling the API, so builds never need it", async () => {
    const incomingRequest = Promise.withResolvers<void>();
    vi.mocked(connection).mockReturnValue(incomingRequest.promise);

    const options = api.getFilterOptions();
    const calledBeforeRequest = fetchMock.mock.calls.length;
    incomingRequest.resolve();
    await options;

    expect(calledBeforeRequest).toBe(0);
    expect(fetchMock).toHaveBeenCalledOnce();
  });

  it("caches the catalog for an hour", async () => {
    await api.getFilterOptions();

    expect(cacheLife).toHaveBeenCalledWith("hours");
  });
});
