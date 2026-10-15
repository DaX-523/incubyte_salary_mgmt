import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, getEmployee, getFilterOptions } from "@/lib/api";
import { ADA, ALAN, OPTIONS } from "@/test/fixtures";

import EmployeePage from "./page";

vi.mock("next/navigation", () => ({
  notFound: vi.fn(() => {
    throw new Error("NEXT_NOT_FOUND");
  }),
  redirect: vi.fn(),
}));
vi.mock("next/cache", () => ({ refresh: vi.fn() }));
vi.mock("@/lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/api")>()),
  getEmployee: vi.fn(),
  getFilterOptions: vi.fn(),
}));

function pageFor(id: string) {
  return EmployeePage({
    params: Promise.resolve({ id }),
    searchParams: Promise.resolve({}),
  });
}

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date("2026-10-15T12:00:00Z"));
  vi.mocked(getFilterOptions).mockResolvedValue(OPTIONS);
});

afterEach(() => {
  vi.useRealTimers();
  vi.clearAllMocks();
});

describe("EmployeePage", () => {
  it("shows the employee with forms to edit, pay and deactivate them", async () => {
    vi.mocked(getEmployee).mockResolvedValue(ADA);

    render(await pageFor("1"));

    expect(getEmployee).toHaveBeenCalledWith(1);
    expect(
      screen.getByRole("heading", { level: 1, name: "Ada Lovelace" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Save changes" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Record payroll" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Deactivate employee" }),
    ).toBeInTheDocument();
  });

  it("prefills a payroll for this month at the employee's salary", async () => {
    vi.mocked(getEmployee).mockResolvedValue(ADA);

    render(await pageFor("1"));

    expect(screen.getByLabelText("Month")).toHaveValue("2026-10");
    expect(screen.getByRole("textbox", { name: "Base pay" })).toHaveValue(
      "4780.00",
    );
  });

  it("does not offer payroll or deactivation for an inactive employee", async () => {
    vi.mocked(getEmployee).mockResolvedValue(ALAN);

    render(await pageFor("2"));

    expect(screen.getAllByText("Inactive").length).toBeGreaterThan(0);
    expect(
      screen.queryByRole("button", { name: "Record payroll" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Deactivate employee" }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByText(/no new payrolls can be recorded/),
    ).toBeInTheDocument();
  });

  it.each(["abc", "0", "-1"])(
    "shows not found for the id %j without calling the API",
    async (id) => {
      await expect(pageFor(id)).rejects.toThrow("NEXT_NOT_FOUND");
      expect(getEmployee).not.toHaveBeenCalled();
    },
  );

  it("shows not found when the employee does not exist", async () => {
    vi.mocked(getEmployee).mockRejectedValue(
      new ApiError(404, "Employee 9 not found"),
    );

    await expect(pageFor("9")).rejects.toThrow("NEXT_NOT_FOUND");
  });
});
