import { describe, expect, it } from "vitest";

import {
  dashboardHref,
  parseDashboardQuery,
  type SearchParams,
} from "./dashboard-query";

const ALLOWED = {
  month: "2026-10",
  countries: ["DE", "GB"],
  jobTitles: ["Accountant", "Legal Counsel"],
};
const DEFAULTS = {
  month: "2026-10",
  id: undefined,
  name: undefined,
  country: undefined,
  job_title: undefined,
  sort_by: "id",
  sort_order: "asc",
  page: 1,
};

describe("parseDashboardQuery", () => {
  it("defaults to the current month, unfiltered, first page, sorted by id", () => {
    expect(parseDashboardQuery({}, ALLOWED)).toEqual(DEFAULTS);
  });

  it("reads every filter from the URL", () => {
    const params: SearchParams = {
      month: "2026-03",
      id: "42",
      name: " ada ",
      country: "DE",
      job_title: "Accountant",
      sort_by: "monthly_salary",
      sort_order: "desc",
      page: "3",
    };

    expect(parseDashboardQuery(params, ALLOWED)).toEqual({
      month: "2026-03",
      id: 42,
      name: "ada",
      country: "DE",
      job_title: "Accountant",
      sort_by: "monthly_salary",
      sort_order: "desc",
      page: 3,
    });
  });

  it.each<[string, SearchParams]>([
    ["an invalid month", { month: "2026-13" }],
    ["a blank name", { name: "   " }],
    ["a name longer than 200 characters", { name: "x".repeat(201) }],
    ["a zero id", { id: "0" }],
    ["a non-numeric id", { id: "12abc" }],
    ["an unknown country", { country: "XX" }],
    ["an unknown job title", { job_title: "Wizard" }],
    ["an unknown sort field", { sort_by: "email" }],
    ["an unknown sort order", { sort_order: "sideways" }],
    ["a zero page", { page: "0" }],
    ["a negative page", { page: "-2" }],
  ])("ignores %s", (_, params) => {
    expect(parseDashboardQuery(params, ALLOWED)).toEqual(DEFAULTS);
  });

  it("only sorts by salary within a country", () => {
    const query = parseDashboardQuery({ sort_by: "monthly_salary" }, ALLOWED);

    expect(query.sort_by).toBe("id");
  });

  it("takes the first value of a repeated parameter", () => {
    const query = parseDashboardQuery({ country: ["GB", "DE"] }, ALLOWED);

    expect(query.country).toBe("GB");
  });
});

describe("dashboardHref", () => {
  it("is the bare dashboard without filters", () => {
    expect(dashboardHref({})).toBe("/");
  });

  it("leaves out the default page and sort", () => {
    expect(
      dashboardHref({ ...DEFAULTS, sort_by: "id", sort_order: "asc" }),
    ).toBe("/?month=2026-10");
  });

  it("keeps filters, sort and page", () => {
    const href = dashboardHref({
      month: "2026-10",
      country: "DE",
      job_title: "Legal Counsel",
      sort_by: "monthly_salary",
      sort_order: "desc",
      page: 2,
    });

    expect(href).toBe(
      "/?month=2026-10&country=DE&job_title=Legal+Counsel&sort_by=monthly_salary&sort_order=desc&page=2",
    );
  });
});
