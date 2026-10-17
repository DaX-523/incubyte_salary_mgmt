import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { GERMAN_PAY } from "@/test/fixtures";

import { PayByJobTitleTable } from "./pay-by-job-title-table";

describe("PayByJobTitleTable", () => {
  it("names the country and currency it compares", () => {
    render(<PayByJobTitleTable data={GERMAN_PAY} />);

    expect(
      screen.getByRole("table", {
        name: "Monthly salaries of active employees in Germany, in EUR",
      }),
    ).toBeInTheDocument();
  });

  it("shows headcount, salary range and average per job title", () => {
    render(<PayByJobTitleTable data={GERMAN_PAY} />);

    const row = within(screen.getByRole("row", { name: /Accountant/ }));
    expect(row.getByText("Finance")).toBeInTheDocument();
    expect(row.getByText("41")).toBeInTheDocument();
    expect(row.getByText("€3,060.00")).toBeInTheDocument();
    expect(row.getByText("€3,612.20")).toBeInTheDocument();
    expect(row.getByText("€4,140.00")).toBeInTheDocument();
  });

  it("labels the average column", () => {
    render(<PayByJobTitleTable data={GERMAN_PAY} />);

    expect(
      screen.getByRole("columnheader", { name: "Average" }),
    ).toBeInTheDocument();
  });

  it("links each job title to its peers ranked by salary", () => {
    render(<PayByJobTitleTable data={GERMAN_PAY} />);

    expect(
      screen.getByRole("link", {
        name: "Rank Software Engineer salaries in Germany",
      }),
    ).toHaveAttribute(
      "href",
      "/?country=DE&job_title=Software+Engineer&sort_by=monthly_salary&sort_order=desc",
    );
  });

  it("says so when the country has no active employees", () => {
    render(<PayByJobTitleTable data={{ ...GERMAN_PAY, job_titles: [] }} />);

    expect(
      screen.getByText("No active employees in Germany."),
    ).toBeInTheDocument();
  });
});
