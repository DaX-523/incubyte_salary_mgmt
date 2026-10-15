import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { OCTOBER_STATUS } from "@/test/fixtures";

import { PayrollStatusChart } from "./payroll-status-chart";

describe("PayrollStatusChart", () => {
  it("shows how many employees were paid out of the total for the month", () => {
    render(<PayrollStatusChart status={OCTOBER_STATUS} />);

    expect(
      screen.getByRole("heading", { name: "Paid vs total employees" }),
    ).toBeInTheDocument();
    expect(screen.getByText("October 2026")).toBeInTheDocument();
    expect(
      screen.getByRole("img", { name: "7,815 of 9,168 employees paid (85%)" }),
    ).toBeInTheDocument();
    expect(screen.getByText("85% paid")).toBeInTheDocument();
  });

  it("lists the paid, unpaid and total counts", () => {
    render(<PayrollStatusChart status={OCTOBER_STATUS} />);

    expect(screen.getByText("Paid").nextSibling).toHaveTextContent("7,815");
    expect(screen.getByText("Unpaid").nextSibling).toHaveTextContent("1,353");
    expect(screen.getByText("Total").nextSibling).toHaveTextContent("9,168");
  });

  it("says so when nobody is on the books", () => {
    render(
      <PayrollStatusChart
        status={{ month: "2026-10", total: 0, paid: 0, unpaid: 0 }}
      />,
    );

    expect(
      screen.getByText("No employees on the books for this month."),
    ).toBeInTheDocument();
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });
});
