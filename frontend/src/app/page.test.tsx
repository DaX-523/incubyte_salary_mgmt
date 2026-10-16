import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  getFilterOptions,
  getPayrollStatus,
  listEmployeesForMonth,
} from "@/lib/api";
import { MONTHLY_PAGE, OCTOBER_STATUS, OPTIONS } from "@/test/fixtures";

import DashboardPage from "./page";

vi.mock("next/navigation", () => ({ useRouter: vi.fn() }));
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
      name: undefined,
      email: undefined,
      country: undefined,
      job_title: undefined,
      sort_by: "name",
      sort_order: "asc",
      page: 1,
      page_size: 25,
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
      page_size: "50",
      email: "ada@",
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
        page_size: 50,
        email: "ada@",
      }),
    );
  });

  it("lists by name, but keeps the requested salary sort, when no country is chosen", async () => {
    await renderDashboard({ sort_by: "monthly_salary" });

    expect(listEmployeesForMonth).toHaveBeenCalledWith(
      expect.objectContaining({ sort_by: "name" }),
    );
    expect(screen.getByRole("combobox", { name: "Sort by" })).toHaveValue(
      "monthly_salary",
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

  it("shows the paid vs total chart above the filters", async () => {
    await renderDashboard();

    const chart = screen.getByRole("heading", {
      name: "Paid vs total employees",
    });
    const filters = screen.getByText("Filters and sorting");
    expect(chart.compareDocumentPosition(filters)).toBe(
      Node.DOCUMENT_POSITION_FOLLOWING,
    );
  });
});
