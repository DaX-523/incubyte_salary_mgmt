import type {
  EmployeeSortField,
  MonthlyEmployeeQuery,
  SortOrder,
} from "@/lib/api";
import { MONTH_PATTERN } from "@/lib/month";
import {
  firstParam,
  oneOf,
  positiveInteger,
  type SearchParams,
} from "@/lib/search-params";

export type { SearchParams };

export type DashboardQuery = MonthlyEmployeeQuery & {
  sort_by: EmployeeSortField;
  sort_order: SortOrder;
  page: number;
};

type Allowed = { month: string; countries: string[]; jobTitles: string[] };

const SORT_FIELDS: EmployeeSortField[] = ["id", "name", "monthly_salary"];
const SORT_ORDERS: SortOrder[] = ["asc", "desc"];
const MAX_NAME_LENGTH = 200;

/**
 * Reads the dashboard's filters from the URL. Anything missing or invalid falls back to the
 * default (or no filter), so a hand-edited URL never breaks the page.
 */
export function parseDashboardQuery(
  params: SearchParams,
  allowed: Allowed,
): DashboardQuery {
  const month = firstParam(params.month);
  const name = firstParam(params.name);
  const country = oneOf(firstParam(params.country), allowed.countries);
  const sortBy = oneOf(firstParam(params.sort_by), SORT_FIELDS) ?? "id";
  return {
    month: month && MONTH_PATTERN.test(month) ? month : allowed.month,
    id: positiveInteger(firstParam(params.id)),
    name: name && name.length <= MAX_NAME_LENGTH ? name : undefined,
    country,
    job_title: oneOf(firstParam(params.job_title), allowed.jobTitles),
    // Salaries are in local currencies, so they are only sorted within one country.
    sort_by: sortBy === "monthly_salary" && !country ? "id" : sortBy,
    sort_order: oneOf(firstParam(params.sort_order), SORT_ORDERS) ?? "asc",
    page: positiveInteger(firstParam(params.page)) ?? 1,
  };
}

/** A dashboard URL for `query`, leaving out defaults to keep links short. */
export function dashboardHref(query: Partial<DashboardQuery>): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && !isDefault(key, value)) {
      params.set(key, String(value));
    }
  }
  const search = params.toString();
  return search ? `/?${search}` : "/";
}

function isDefault(key: string, value: string | number): boolean {
  return (
    (key === "page" && value === 1) ||
    (key === "sort_by" && value === "id") ||
    (key === "sort_order" && value === "asc")
  );
}
