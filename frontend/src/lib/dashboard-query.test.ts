import { describe, expect, it } from "vitest";

import {
  activeFilterLabels,
  type DashboardQuery,
  dashboardHref,
  employeeListQuery,
  parseDashboardQuery,
  salarySortNeedsCountry,
  type SearchParams,
} from "./dashboard-query";

const ALLOWED = {
  month: "2026-10",
  countries: ["DE", "GB"],
  jobTitles: ["Accountant", "Legal Counsel"],
};
const DEFAULTS: DashboardQuery = {
  month: "2026-10",
  name: undefined,
  email: undefined,
  country: undefined,
  job_title: undefined,
  sort_by: "name",
  sort_order: "asc",
  page: 1,
  page_size: 25,
};

describe("parseDashboardQuery", () => {
  it("defaults to the current month, unfiltered, first page of 25, sorted by name", () => {
    expect(parseDashboardQuery({}, ALLOWED)).toEqual(DEFAULTS);
  });

  it("reads every filter from the URL", () => {
    const params: SearchParams = {
      month: "2026-03",
      name: " ada ",
      email: " ada@example.com ",
      country: "DE",
      job_title: "Accountant",
      sort_by: "monthly_salary",
      sort_order: "desc",
      page: "3",
      page_size: "50",
    };

    expect(parseDashboardQuery(params, ALLOWED)).toEqual({
      month: "2026-03",
      name: "ada",
      email: "ada@example.com",
      country: "DE",
      job_title: "Accountant",
      sort_by: "monthly_salary",
      sort_order: "desc",
      page: 3,
      page_size: 50,
    });
  });

  it.each([
    ["25", 25],
    ["50", 50],
    ["100", 100],
  ])("offers %s rows per page", (pageSize, expected) => {
    const query = parseDashboardQuery({ page_size: pageSize }, ALLOWED);

    expect(query.page_size).toBe(expected);
  });

  it.each<[string, SearchParams]>([
    ["an invalid month", { month: "2026-13" }],
    ["a blank name", { name: "   " }],
    ["a name longer than 200 characters", { name: "x".repeat(201) }],
    ["a blank email", { email: "  " }],
    ["an email longer than 320 characters", { email: "x".repeat(321) }],
    ["an unknown country", { country: "XX" }],
    ["an unknown job title", { job_title: "Wizard" }],
    ["an unknown sort field", { sort_by: "email" }],
    ["sorting by id, which is not offered", { sort_by: "id" }],
    ["an unknown sort order", { sort_order: "sideways" }],
    ["a zero page", { page: "0" }],
    ["a negative page", { page: "-2" }],
    ["a page size that is not offered", { page_size: "30" }],
    ["a page size over the maximum", { page_size: "500" }],
  ])("ignores %s", (_, params) => {
    expect(parseDashboardQuery(params, ALLOWED)).toEqual(DEFAULTS);
  });

  it("keeps a salary sort without a country, so the form shows what was asked for", () => {
    const query = parseDashboardQuery({ sort_by: "monthly_salary" }, ALLOWED);

    expect(query.sort_by).toBe("monthly_salary");
  });

  it("takes the first value of a repeated parameter", () => {
    const query = parseDashboardQuery({ country: ["GB", "DE"] }, ALLOWED);

    expect(query.country).toBe("GB");
  });
});

describe("salarySortNeedsCountry", () => {
  it.each<[string, boolean, Partial<DashboardQuery>]>([
    ["salary without a country", true, { sort_by: "monthly_salary" }],
    [
      "salary within a country",
      false,
      { sort_by: "monthly_salary", country: "DE" },
    ],
    ["name without a country", false, { sort_by: "name" }],
  ])("%s → %s", (_, expected, sort) => {
    expect(salarySortNeedsCountry({ ...DEFAULTS, ...sort })).toBe(expected);
  });
});

describe("employeeListQuery", () => {
  it("sorts by name when salary sorting has no country", () => {
    const query: DashboardQuery = { ...DEFAULTS, sort_by: "monthly_salary" };

    expect(employeeListQuery(query)).toEqual(DEFAULTS);
  });

  it("sorts by salary within a country", () => {
    const query: DashboardQuery = {
      ...DEFAULTS,
      country: "DE",
      sort_by: "monthly_salary",
    };

    expect(employeeListQuery(query)).toEqual(query);
  });
});

describe("dashboardHref", () => {
  it("is the bare dashboard without filters", () => {
    expect(dashboardHref({})).toBe("/");
  });

  it("leaves out the default page, page size and sort", () => {
    expect(dashboardHref(DEFAULTS)).toBe("/?month=2026-10");
  });

  it("keeps filters, sort and page", () => {
    const href = dashboardHref({
      month: "2026-10",
      country: "DE",
      job_title: "Legal Counsel",
      sort_by: "monthly_salary",
      sort_order: "desc",
      page: 2,
      page_size: 100,
    });

    expect(href).toBe(
      "/?month=2026-10&country=DE&job_title=Legal+Counsel&sort_by=monthly_salary&sort_order=desc&page=2&page_size=100",
    );
  });
});

describe("activeFilterLabels", () => {
  it("is empty when nothing narrows the list", () => {
    expect(activeFilterLabels(DEFAULTS)).toEqual([]);
  });

  it("names each filter in use, with the country written out", () => {
    const query: DashboardQuery = {
      ...DEFAULTS,
      name: "ada",
      email: "ada@",
      country: "DE",
      job_title: "Accountant",
    };

    expect(activeFilterLabels(query)).toEqual([
      "Name: ada",
      "Email: ada@",
      "Germany",
      "Accountant",
    ]);
  });

  it("does not count the month, sorting or page size as filters", () => {
    const query: DashboardQuery = {
      ...DEFAULTS,
      month: "2026-03",
      sort_by: "monthly_salary",
      sort_order: "desc",
      page_size: 100,
    };

    expect(activeFilterLabels(query)).toEqual([]);
  });
});
