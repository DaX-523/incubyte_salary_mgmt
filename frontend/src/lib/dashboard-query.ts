import type {
  EmployeeExportQuery,
  EmployeeSortField,
  FilterOptions,
  MonthlyEmployeeQuery,
  SortOrder,
} from "@/lib/api";
import { countryName } from "@/lib/format";
import { currentMonth, MONTH_PATTERN } from "@/lib/month";
import {
  firstParam,
  oneOf,
  positiveInteger,
  type SearchParams,
} from "@/lib/search-params";

export type { SearchParams };

export const PAGE_SIZES = [25, 50, 100] as const;
export type PageSize = (typeof PAGE_SIZES)[number];
/** Same as the API's default. */
export const DEFAULT_PAGE_SIZE: PageSize = 25;

export type DashboardQuery = MonthlyEmployeeQuery & {
  sort_by: EmployeeSortField;
  sort_order: SortOrder;
  page: number;
  page_size: PageSize;
};

type Allowed = { month: string; countries: string[]; jobTitles: string[] };

const SORT_FIELDS: EmployeeSortField[] = ["name", "monthly_salary"];
const EXPORT_PATH = "/employees/export";
const SORT_ORDERS: SortOrder[] = ["asc", "desc"];
const MAX_NAME_LENGTH = 200;
const MAX_EMAIL_LENGTH = 320;

/** The values the API's catalog offers, and the current month as the default month. */
export function allowedFilters(options: FilterOptions, now: Date): Allowed {
  return {
    month: currentMonth(now),
    countries: options.countries.map((country) => country.code),
    jobTitles: options.job_titles.map((job) => job.title),
  };
}

/**
 * Reads the dashboard's filters from the URL. Anything missing or invalid falls back to the
 * default (or no filter), so a hand-edited URL never breaks the page.
 */
export function parseDashboardQuery(
  params: SearchParams,
  allowed: Allowed,
): DashboardQuery {
  const month = firstParam(params.month);
  return {
    month: month && MONTH_PATTERN.test(month) ? month : allowed.month,
    name: limitedText(firstParam(params.name), MAX_NAME_LENGTH),
    email: limitedText(firstParam(params.email), MAX_EMAIL_LENGTH),
    country: oneOf(firstParam(params.country), allowed.countries),
    job_title: oneOf(firstParam(params.job_title), allowed.jobTitles),
    // Kept even without a country, so the form shows what was asked for; see employeeListQuery.
    sort_by: oneOf(firstParam(params.sort_by), SORT_FIELDS) ?? "name",
    sort_order: oneOf(firstParam(params.sort_order), SORT_ORDERS) ?? "asc",
    page: positiveInteger(firstParam(params.page)) ?? 1,
    page_size: parsePageSize(firstParam(params.page_size)),
  };
}

/** Salaries are in local currencies, so they are only sorted within one country. */
export function salarySortNeedsCountry(query: DashboardQuery): boolean {
  return query.sort_by === "monthly_salary" && !query.country;
}

/** What the employee list can show for `query`: by name until a salary sort has a country. */
export function employeeListQuery(query: DashboardQuery): DashboardQuery {
  return salarySortNeedsCountry(query) ? { ...query, sort_by: "name" } : query;
}

/** Everyone the list shows for `query`, on one sheet: the same filters and order, no pages. */
export function employeeExportQuery(
  query: DashboardQuery,
): EmployeeExportQuery {
  const { month, name, email, country, job_title, sort_by, sort_order } =
    employeeListQuery(query);
  return { month, name, email, country, job_title, sort_by, sort_order };
}

/** The "Download CSV" link for what the dashboard shows. */
export function employeeExportHref(query: DashboardQuery): string {
  return withQuery(EXPORT_PATH, employeeExportQuery(query));
}

/** "2026-10" → "employees-2026-10.csv". */
export function employeeExportFileName(month: string): string {
  return `employees-${month}.csv`;
}

/** One of the offered page sizes, or the default. */
export function parsePageSize(value: string | undefined): PageSize {
  return PAGE_SIZES.find((size) => String(size) === value) ?? DEFAULT_PAGE_SIZE;
}

/** The filters narrowing the list, as short labels for the collapsed filters panel. */
export function activeFilterLabels(query: DashboardQuery): string[] {
  const labels = [
    query.name && `Name: ${query.name}`,
    query.email && `Email: ${query.email}`,
    query.country && countryName(query.country),
    query.job_title,
  ];
  return labels.filter((label): label is string => Boolean(label));
}

/** A dashboard URL for `query`, leaving out defaults to keep links short. */
export function dashboardHref(query: Partial<DashboardQuery>): string {
  return withQuery("/", query);
}

function withQuery(path: string, query: Partial<DashboardQuery>): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && !isDefault(key, value)) {
      params.set(key, String(value));
    }
  }
  const search = params.toString();
  return search ? `${path}?${search}` : path;
}

function limitedText(value: string | undefined, maxLength: number) {
  return value && value.length <= maxLength ? value : undefined;
}

function isDefault(key: string, value: string | number): boolean {
  return (
    (key === "page" && value === 1) ||
    (key === "page_size" && value === DEFAULT_PAGE_SIZE) ||
    (key === "sort_by" && value === "name") ||
    (key === "sort_order" && value === "asc")
  );
}
