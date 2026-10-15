import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  getFilterOptions,
  getPayrollStatus,
  listEmployeesForMonth,
} from "@/lib/api";
import { MONTHLY_PAGE, OCTOBER_STATUS, OPTIONS } from "@/test/fixtures";

import DashboardPage from "./page";

vi.mock("@/lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/api")>()),
  getFilterOptions: vi.fn(),
  getPayrollStatus: vi.fn(),
  listEmployeesForMonth: vi.fn(),
}));

async function renderDashboard(searchParams: Record<string, string> = {}) {
  render(
    await DashboardPage({
      params: Promise.resolve({}),
      searchParams: Promise.resolve(searchParams),
    }),
  );
}

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date("2026-10-15T12:00:00Z"));
  vi.mocked(getFilterOptions).mockResolvedValue(OPTIONS);
  vi.mocked(getPayrollStatus).mockResolvedValue(OCTOBER_STATUS);
  vi.mocked(listEmployeesForMonth).mockResolvedValue(MONTHLY_PAGE);
});

afterEach(() => {
  vi.useRealTimers();
  vi.clearAllMocks();
});

describe("DashboardPage", () => {
  it("shows the current month's payroll by default", async () => {
    await renderDashboard();

    expect(
      screen.getByRole("heading", { level: 1, name: "Payroll dashboard" }),
    ).toBeInTheDocument();
    expect(listEmployeesForMonth).toHaveBeenCalledWith({
      month: "2026-10",
      id: undefined,
      name: undefined,
      country: undefined,
      job_title: undefined,
      sort_by: "id",
      sort_order: "asc",
      page: 1,
    });
    expect(getPayrollStatus).toHaveBeenCalledWith({
      month: "2026-10",
      country: undefined,
      job_title: undefined,
    });
  });

  it("applies the filters from the URL to the chart and the list", async () => {
    await renderDashboard({
      month: "2026-09",
      country: "DE",
      job_title: "Accountant",
      sort_by: "monthly_salary",
      sort_order: "desc",
      page: "2",
    });

    expect(getPayrollStatus).toHaveBeenCalledWith({
      month: "2026-09",
      country: "DE",
      job_title: "Accountant",
    });
    expect(listEmployeesForMonth).toHaveBeenCalledWith(
      expect.objectContaining({
        country: "DE",
        sort_by: "monthly_salary",
        page: 2,
      }),
    );
  });

  it("ignores filter values the API does not offer", async () => {
    await renderDashboard({ country: "XX", job_title: "Wizard" });

    expect(listEmployeesForMonth).toHaveBeenCalledWith(
      expect.objectContaining({ country: undefined, job_title: undefined }),
    );
  });

  it("shows the paid vs total chart, the employees and pagination", async () => {
    await renderDashboard();

    expect(
      screen.getByRole("img", { name: "7,815 of 9,168 employees paid (85%)" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Ada Lovelace" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Showing 1–25 of 60")).toBeInTheDocument();
  });
});
