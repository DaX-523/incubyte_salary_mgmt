// Mirrors the backend's /api/v1 contract. Money is a decimal string ("4780.00"), never a number,
// and months are "YYYY-MM".

export type PaymentMethod = "bank_transfer" | "digital_wallet";
export type EmployeeSortField = "name" | "monthly_salary";
export type SortOrder = "asc" | "desc";

export type Employee = {
  id: number;
  name: string;
  email: string;
  monthly_salary: string;
  currency: string;
  country: string;
  department: string;
  job_title: string;
  is_active: boolean;
};

export type Payroll = {
  id: number;
  employee_id: number;
  month: string;
  base: string;
  bonus: string;
  esops: string;
  currency: string;
  payment_method: PaymentMethod;
};

export type MonthlyEmployee = {
  employee: Employee;
  payroll: Payroll | null;
};

export type Page<Item> = {
  items: Item[];
  total: number;
  page: number;
  page_size: number;
};

export type MonthlyEmployeeQuery = {
  month: string;
  name?: string;
  email?: string;
  country?: string;
  job_title?: string;
  sort_by?: EmployeeSortField;
  sort_order?: SortOrder;
  page?: number;
  page_size?: number;
};

/** The monthly list's filters and order, without pages: what the CSV export takes. */
export type EmployeeExportQuery = Omit<
  MonthlyEmployeeQuery,
  "page" | "page_size"
>;

export type EmployeeCreate = {
  name: string;
  email: string;
  monthly_salary: string;
  country: string;
  job_title: string;
};

export type EmployeeUpdate = Partial<Omit<EmployeeCreate, "country">>;

export type PayrollCreate = {
  month: string;
  base: string;
  bonus: string;
  esops: string;
  payment_method: PaymentMethod;
};

export type PayrollUpdate = Partial<Omit<PayrollCreate, "month">>;

export type PayrollStatusQuery = {
  month: string;
  country?: string;
  job_title?: string;
};

export type PayrollStatus = {
  month: string;
  total: number;
  paid: number;
  unpaid: number;
};

export type JobTitlePay = {
  job_title: string;
  department: string;
  headcount: number;
  min_salary: string;
  max_salary: string;
  average_salary: string;
};

export type PayByJobTitle = {
  country: string;
  currency: string;
  job_titles: JobTitlePay[];
};

export type CountryPay = {
  country: string;
  currency: string;
  headcount: number;
  average_salary: string;
  total_monthly_salary: string;
};

/** One row per country, each in its own currency: there is no organization-wide total. */
export type PayByCountry = { countries: CountryPay[] };

export type CountryOption = { code: string; currency: string };
export type JobTitleOption = { title: string; department: string };

export type FilterOptions = {
  countries: CountryOption[];
  job_titles: JobTitleOption[];
  payment_methods: PaymentMethod[];
};

export type LoginToken = {
  access_token: string;
  token_type: "bearer";
  /** ISO 8601 date-time, for example "2026-10-16T17:00:00Z". */
  expires_at: string;
};

export type Profile = { name: string; email: string; organization: string };
