import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { DashboardQuery } from "@/lib/dashboard-query";
import { OPTIONS } from "@/test/fixtures";

import { FiltersForm } from "./filters-form";

const QUERY: DashboardQuery = {
  month: "2026-10",
  sort_by: "id",
  sort_order: "asc",
  page: 1,
};

function optionLabels(name: string) {
  const select = screen.getByRole("combobox", { name }) as HTMLSelectElement;
  return Array.from(select.options).map((option) => option.textContent);
}

describe("FiltersForm", () => {
  it("submits the filters to the dashboard URL", () => {
    render(<FiltersForm query={QUERY} options={OPTIONS} />);

    expect(screen.getByRole("form", { name: "Filters" })).toHaveAttribute(
      "action",
      "/",
    );
    expect(
      screen.getByRole("button", { name: "Apply filters" }),
    ).toHaveAttribute("type", "submit");
    expect(screen.getByRole("link", { name: "Reset" })).toHaveAttribute(
      "href",
      "/",
    );
  });

  it("shows the current filters", () => {
    const query: DashboardQuery = {
      ...QUERY,
      id: 7,
      name: "ada",
      country: "IN",
      job_title: "Accountant",
      sort_by: "monthly_salary",
      sort_order: "desc",
    };

    render(<FiltersForm query={query} options={OPTIONS} />);

    expect(screen.getByLabelText("Month")).toHaveValue("2026-10");
    expect(screen.getByRole("spinbutton", { name: "Employee ID" })).toHaveValue(
      7,
    );
    expect(screen.getByRole("searchbox", { name: "Name" })).toHaveValue("ada");
    expect(screen.getByRole("combobox", { name: "Country" })).toHaveValue("IN");
    expect(screen.getByRole("combobox", { name: "Job title" })).toHaveValue(
      "Accountant",
    );
    expect(screen.getByRole("combobox", { name: /Sort by/ })).toHaveValue(
      "monthly_salary",
    );
    expect(screen.getByRole("combobox", { name: "Order" })).toHaveValue("desc");
  });

  it("offers every country by name, alphabetically, plus all countries", () => {
    render(<FiltersForm query={QUERY} options={OPTIONS} />);

    expect(optionLabels("Country")).toEqual([
      "All countries",
      "Germany",
      "India",
      "United Kingdom",
    ]);
    expect(screen.getByRole("combobox", { name: "Country" })).toHaveValue("");
  });

  it("explains that salary sorting needs a country", () => {
    render(<FiltersForm query={QUERY} options={OPTIONS} />);

    expect(
      screen.getByRole("combobox", { name: "Sort by" }),
    ).toHaveAccessibleDescription(
      "Salaries are in local currency, so salary sorting needs a country.",
    );
  });
});
