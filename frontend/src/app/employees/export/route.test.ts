import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { exportEmployeesForMonth, getFilterOptions } from "@/lib/api";
import { OPTIONS } from "@/test/fixtures";

import { GET } from "./route";

vi.mock("@/lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/api")>()),
  exportEmployeesForMonth: vi.fn(),
  getFilterOptions: vi.fn(),
}));

const CSV = 'Employee ID,Name\r\n1,Ada Lovelace\r\n2,"Lovelace, Ada"\r\n';

function download(search: string) {
  return GET(new Request(`http://localhost:3000/employees/export${search}`));
}

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date("2026-10-15T12:00:00Z"));
  vi.mocked(getFilterOptions).mockResolvedValue(OPTIONS);
  vi.mocked(exportEmployeesForMonth).mockResolvedValue(CSV);
});

afterEach(() => {
  vi.useRealTimers();
  vi.clearAllMocks();
});

describe("GET /employees/export", () => {
  it("sends the API's CSV as a download named after the month", async () => {
    const response = await download("?month=2026-09");

    expect(response.headers.get("Content-Type")).toBe(
      "text/csv; charset=utf-8",
    );
    expect(response.headers.get("Content-Disposition")).toBe(
      'attachment; filename="employees-2026-09.csv"',
    );
    await expect(response.text()).resolves.toBe(CSV);
  });

  it("exports the dashboard's filters and order, without pages", async () => {
    await download(
      "?month=2026-09&country=DE&job_title=Accountant&sort_by=monthly_salary&sort_order=desc&page=3&page_size=100",
    );

    expect(exportEmployeesForMonth).toHaveBeenCalledWith({
      month: "2026-09",
      name: undefined,
      email: undefined,
      country: "DE",
      job_title: "Accountant",
      sort_by: "monthly_salary",
      sort_order: "desc",
    });
  });

  it("defaults to this month and drops values the API does not offer", async () => {
    await download("?country=XX&sort_by=monthly_salary");

    expect(exportEmployeesForMonth).toHaveBeenCalledWith({
      month: "2026-10",
      name: undefined,
      email: undefined,
      country: undefined,
      job_title: undefined,
      sort_by: "name",
      sort_order: "asc",
    });
  });
});
