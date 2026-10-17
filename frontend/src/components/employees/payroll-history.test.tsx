import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ADA_PAYROLL_HISTORY } from "@/test/fixtures";

import { PayrollHistory } from "./payroll-history";

describe("PayrollHistory", () => {
  it("shows each month's pay in the employee's currency", () => {
    render(<PayrollHistory payrolls={ADA_PAYROLL_HISTORY} />);

    const row = within(screen.getByRole("row", { name: /October 2026/ }));
    expect(row.getByText("£4,780.00")).toBeInTheDocument();
    expect(row.getByText("£239.00")).toBeInTheDocument();
    expect(row.getByText("£0.00")).toBeInTheDocument();
    expect(row.getByText("Bank transfer")).toBeInTheDocument();
  });

  it("keeps the API's order, newest month first", () => {
    render(<PayrollHistory payrolls={ADA_PAYROLL_HISTORY} />);

    expect(screen.getAllByRole("link").map((link) => link.textContent)).toEqual(
      ["October 2026", "September 2026"],
    );
  });

  it("links each month to its payroll, where it can be corrected", () => {
    render(<PayrollHistory payrolls={ADA_PAYROLL_HISTORY} />);

    expect(
      screen.getByRole("link", { name: "September 2026" }),
    ).toHaveAttribute("href", "/payrolls/11");
  });

  it("says so when the employee has never been paid", () => {
    render(<PayrollHistory payrolls={[]} />);

    expect(screen.getByText("No payrolls recorded yet.")).toBeInTheDocument();
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
  });
});
