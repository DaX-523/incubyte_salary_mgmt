import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MONTHLY_PAGE } from "@/test/fixtures";

import { EmployeeTable } from "./employee-table";

function rowFor(name: string) {
  return within(
    screen.getByRole("link", { name }).closest("tr") as HTMLElement,
  );
}

describe("EmployeeTable", () => {
  it("describes which month it lists", () => {
    render(<EmployeeTable rows={MONTHLY_PAGE.items} month="2026-10" />);

    expect(
      screen.getByRole("table", {
        name: "Employees on the books in October 2026",
      }),
    );
  });

  it("shows each employee's salary in their own currency", () => {
    render(<EmployeeTable rows={MONTHLY_PAGE.items} month="2026-10" />);

    expect(rowFor("Ada Lovelace").getByText("£4,780.00")).toBeInTheDocument();
    expect(
      rowFor("Ada Lovelace").getByText("United Kingdom"),
    ).toBeInTheDocument();
    expect(rowFor("Alan Turing").getByText("₹117,000.00")).toBeInTheDocument();
  });

  it("links the whole row to the employee page", () => {
    render(<EmployeeTable rows={MONTHLY_PAGE.items} month="2026-10" />);

    const employeeLink = screen.getByRole("link", { name: "Ada Lovelace" });

    expect(employeeLink).toHaveAttribute("href", "/employees/1");
    expect(employeeLink.closest("tr")).toHaveClass("relative");
    expect(employeeLink).toHaveClass("after:absolute", "after:inset-0");
  });

  it("links a paid employee to the month's payroll and marks the unpaid", () => {
    render(<EmployeeTable rows={MONTHLY_PAGE.items} month="2026-10" />);

    const paidLink = rowFor("Ada Lovelace").getByRole("link", { name: "Paid" });

    expect(paidLink).toHaveAttribute("href", "/payrolls/12");
    expect(paidLink).toHaveClass("relative", "z-20");
    expect(rowFor("Alan Turing").getByText("Unpaid")).toBeInTheDocument();
  });

  it("flags employees who are no longer active", () => {
    render(<EmployeeTable rows={MONTHLY_PAGE.items} month="2026-10" />);

    expect(rowFor("Alan Turing").getByText("Inactive")).toBeInTheDocument();
    expect(
      rowFor("Ada Lovelace").queryByText("Inactive"),
    ).not.toBeInTheDocument();
  });

  it("says so when no employee matches", () => {
    render(<EmployeeTable rows={[]} month="2026-10" />);

    expect(
      screen.getByText("No employees match these filters."),
    ).toBeInTheDocument();
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
  });
});
