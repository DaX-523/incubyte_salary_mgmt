import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ADA, ALAN } from "@/test/fixtures";

import { EmployeeDetails } from "./employee-details";

function detail(label: string) {
  return screen.getByText(label).nextSibling;
}

describe("EmployeeDetails", () => {
  it("shows the employee's record with the salary in their currency", () => {
    render(<EmployeeDetails employee={ADA} />);

    expect(detail("Email")).toHaveTextContent("ada@example.com");
    expect(detail("Country")).toHaveTextContent("United Kingdom (GBP)");
    expect(detail("Department")).toHaveTextContent("Engineering");
    expect(detail("Monthly salary")).toHaveTextContent("£4,780.00");
    expect(detail("Status")).toHaveTextContent("Active");
  });

  it("shows when an employee is inactive", () => {
    render(<EmployeeDetails employee={ALAN} />);

    expect(detail("Status")).toHaveTextContent("Inactive");
  });
});
