import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PAY_BY_COUNTRY } from "@/test/fixtures";

import { PayByCountryTable } from "./pay-by-country-table";

describe("PayByCountryTable", () => {
  it("says each country is in its own currency", () => {
    render(<PayByCountryTable data={PAY_BY_COUNTRY} />);

    expect(
      screen.getByRole("table", {
        name: "Monthly salaries of active employees, each country in its own currency",
      }),
    ).toBeInTheDocument();
  });

  it("shows headcount, average and total salaries in the country's currency", () => {
    render(<PayByCountryTable data={PAY_BY_COUNTRY} />);

    const row = within(screen.getByRole("row", { name: /United Kingdom/ }));
    expect(row.getByText("GBP")).toBeInTheDocument();
    expect(row.getByText("1,004")).toBeInTheDocument();
    expect(row.getByText("£5,012.35")).toBeInTheDocument();
    expect(row.getByText("£5,032,399.40")).toBeInTheDocument();
  });

  it("lists countries by name", () => {
    render(<PayByCountryTable data={PAY_BY_COUNTRY} />);

    const [, ...rows] = screen.getAllByRole("row");
    expect(
      rows.map((row) => within(row).getByRole("link").textContent),
    ).toEqual(["Germany", "United Kingdom"]);
  });

  it("links each country to its pay by job title", () => {
    render(<PayByCountryTable data={PAY_BY_COUNTRY} />);

    expect(
      screen.getByRole("link", { name: "Pay by job title in Germany" }),
    ).toHaveAttribute("href", "/insights?country=DE");
  });

  it("says so when there are no active employees", () => {
    render(<PayByCountryTable data={{ countries: [] }} />);

    expect(screen.getByText("No active employees yet.")).toBeInTheDocument();
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
  });
});
