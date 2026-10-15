import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import type { DashboardQuery } from "@/lib/dashboard-query";
import { OPTIONS } from "@/test/fixtures";

import { FiltersForm } from "./filters-form";

const QUERY: DashboardQuery = {
  month: "2026-10",
  sort_by: "name",
  sort_order: "asc",
  page: 1,
  page_size: 25,
};

function optionLabels(name: string) {
  const select = screen.getByRole("combobox", { name }) as HTMLSelectElement;
  return Array.from(select.options).map((option) => option.textContent);
}

function filtersForm() {
  return screen.getByRole("form", { name: "Filters" }) as HTMLFormElement;
}

/** The bar that stays visible while the panel is collapsed. */
function summaryBar() {
  const summary = screen.getByText("Filters and sorting").closest("summary");
  if (!summary) {
    throw new Error("The filters summary bar is missing");
  }
  return within(summary);
}

describe("FiltersForm", () => {
  it("submits the filters to the dashboard URL", () => {
    render(<FiltersForm query={QUERY} options={OPTIONS} />);

    expect(filtersForm()).toHaveAttribute("action", "/");
    expect(
      screen.getByRole("button", { name: "Apply filters" }),
    ).toHaveAttribute("type", "submit");
    expect(screen.getByRole("link", { name: "Reset" })).toHaveAttribute(
      "href",
      "/",
    );
  });

  it("starts collapsed", () => {
    render(<FiltersForm query={QUERY} options={OPTIONS} />);

    expect(filtersForm()).not.toBeVisible();
    expect(screen.getByText("Filters and sorting")).toBeVisible();
  });

  it("opens when the user clicks the bar", async () => {
    const user = userEvent.setup();
    render(<FiltersForm query={QUERY} options={OPTIONS} />);

    await user.click(screen.getByText("Filters and sorting"));

    expect(filtersForm()).toBeVisible();
  });

  it("invites the user to filter when nothing is filtered yet", () => {
    render(<FiltersForm query={QUERY} options={OPTIONS} />);

    const bar = summaryBar();
    expect(
      bar.getByText(
        "Search by name or email, or narrow down to a country and job title",
      ),
    ).toBeVisible();
    expect(bar.queryByText(/active$/)).not.toBeInTheDocument();
  });

  it("lists the active filters on the collapsed bar", () => {
    const query: DashboardQuery = {
      ...QUERY,
      country: "DE",
      job_title: "Accountant",
    };

    render(<FiltersForm query={query} options={OPTIONS} />);

    const bar = summaryBar();
    expect(bar.getByText("Germany")).toBeVisible();
    expect(bar.getByText("Accountant")).toBeVisible();
    expect(bar.getByText("2 active")).toBeVisible();
  });

  it("shows the current filters", () => {
    const query: DashboardQuery = {
      ...QUERY,
      name: "ada",
      email: "ada@example.com",
      country: "IN",
      job_title: "Accountant",
      sort_by: "monthly_salary",
      sort_order: "desc",
    };

    render(<FiltersForm query={query} options={OPTIONS} />);

    expect(screen.getByLabelText("Month")).toHaveValue("2026-10");
    expect(screen.getByRole("searchbox", { name: "Name" })).toHaveValue("ada");
    expect(screen.getByRole("searchbox", { name: "Email" })).toHaveValue(
      "ada@example.com",
    );
    expect(screen.getByRole("combobox", { name: "Country" })).toHaveValue("IN");
    expect(screen.getByRole("combobox", { name: "Job title" })).toHaveValue(
      "Accountant",
    );
    expect(screen.getByRole("combobox", { name: /Sort by/ })).toHaveValue(
      "monthly_salary",
    );
    expect(screen.getByRole("combobox", { name: "Order" })).toHaveValue("desc");
  });

  it.each([
    [50, "50"],
    [100, "100"],
    [25, null],
  ] as const)(
    "keeps %s rows per page when the filters are applied",
    (pageSize, submitted) => {
      render(
        <FiltersForm
          query={{ ...QUERY, page_size: pageSize }}
          options={OPTIONS}
        />,
      );

      expect(new FormData(filtersForm()).get("page_size")).toBe(submitted);
    },
  );

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

  it("sorts by name or salary", () => {
    render(<FiltersForm query={QUERY} options={OPTIONS} />);

    expect(optionLabels("Sort by")).toEqual(["Name", "Monthly salary"]);
    expect(screen.getByRole("combobox", { name: "Sort by" })).toHaveValue(
      "name",
    );
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
