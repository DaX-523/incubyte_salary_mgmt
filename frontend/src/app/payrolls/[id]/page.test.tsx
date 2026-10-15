import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, getEmployee, getFilterOptions, getPayroll } from "@/lib/api";
import { ADA, ADA_OCTOBER_PAYROLL, OPTIONS } from "@/test/fixtures";

import PayrollPage from "./page";

vi.mock("next/navigation", () => ({
  notFound: vi.fn(() => {
    throw new Error("NEXT_NOT_FOUND");
  }),
}));
vi.mock("next/cache", () => ({ refresh: vi.fn() }));
vi.mock("@/lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/api")>()),
  getEmployee: vi.fn(),
  getFilterOptions: vi.fn(),
  getPayroll: vi.fn(),
}));

function pageFor(id: string) {
  return PayrollPage({
    params: Promise.resolve({ id }),
    searchParams: Promise.resolve({}),
  });
}

beforeEach(() => {
  vi.mocked(getFilterOptions).mockResolvedValue(OPTIONS);
  vi.mocked(getEmployee).mockResolvedValue(ADA);
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("PayrollPage", () => {
  it("shows the month, the employee and the amounts in the payroll currency", async () => {
    vi.mocked(getPayroll).mockResolvedValue(ADA_OCTOBER_PAYROLL);

    render(await pageFor("12"));

    expect(
      screen.getByRole("heading", {
        level: 1,
        name: "Payroll for October 2026",
      }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Ada Lovelace" })).toHaveAttribute(
      "href",
      "/employees/1",
    );
    expect(
      screen.getByText("Bonus", { selector: "dt" }).nextSibling,
    ).toHaveTextContent("£239.00");
    expect(
      screen.getByText("Payment method", { selector: "dt" }).nextSibling,
    ).toHaveTextContent("Bank transfer");
  });

  it("offers to correct the amounts but not the month", async () => {
    vi.mocked(getPayroll).mockResolvedValue(ADA_OCTOBER_PAYROLL);

    render(await pageFor("12"));

    expect(screen.getByRole("textbox", { name: "Base pay" })).toHaveValue(
      "4780.00",
    );
    expect(screen.queryByLabelText("Month")).not.toBeInTheDocument();
  });

  it("shows not found for an invalid id without calling the API", async () => {
    await expect(pageFor("twelve")).rejects.toThrow("NEXT_NOT_FOUND");
    expect(getPayroll).not.toHaveBeenCalled();
  });

  it("shows not found when the payroll does not exist", async () => {
    vi.mocked(getPayroll).mockRejectedValue(
      new ApiError(404, "Payroll 99 not found"),
    );

    await expect(pageFor("99")).rejects.toThrow("NEXT_NOT_FOUND");
  });
});
