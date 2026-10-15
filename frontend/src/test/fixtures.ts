// Realistic API payloads shared by component and page tests.
import type {
  Employee,
  FilterOptions,
  MonthlyEmployee,
  Page,
  PayByJobTitle,
  Payroll,
  PayrollStatus,
} from "@/lib/api";

export const ADA: Employee = {
  id: 1,
  name: "Ada Lovelace",
  email: "ada@example.com",
  monthly_salary: "4780.00",
  currency: "GBP",
  country: "GB",
  department: "Engineering",
  job_title: "Software Engineer",
  is_active: true,
};

export const ALAN: Employee = {
  ...ADA,
  id: 2,
  name: "Alan Turing",
  email: "alan@example.com",
  monthly_salary: "117000.00",
  currency: "INR",
  country: "IN",
  is_active: false,
};

export const ADA_OCTOBER_PAYROLL: Payroll = {
  id: 12,
  employee_id: 1,
  month: "2026-10",
  base: "4780.00",
  bonus: "239.00",
  esops: "0.00",
  currency: "GBP",
  payment_method: "bank_transfer",
};

export const OPTIONS: FilterOptions = {
  countries: [
    { code: "DE", currency: "EUR" },
    { code: "GB", currency: "GBP" },
    { code: "IN", currency: "INR" },
  ],
  job_titles: [
    { title: "Accountant", department: "Finance" },
    { title: "Software Engineer", department: "Engineering" },
  ],
  payment_methods: ["bank_transfer", "digital_wallet"],
};

export const OCTOBER_STATUS: PayrollStatus = {
  month: "2026-10",
  total: 9168,
  paid: 7815,
  unpaid: 1353,
};

export const MONTHLY_PAGE: Page<MonthlyEmployee> = {
  items: [
    { employee: ADA, payroll: ADA_OCTOBER_PAYROLL },
    { employee: ALAN, payroll: null },
  ],
  total: 60,
  page: 1,
  page_size: 25,
};

export const GERMAN_PAY: PayByJobTitle = {
  country: "DE",
  currency: "EUR",
  job_titles: [
    {
      job_title: "Accountant",
      department: "Finance",
      headcount: 41,
      min_salary: "3060.00",
      max_salary: "4140.00",
    },
    {
      job_title: "Software Engineer",
      department: "Engineering",
      headcount: 52,
      min_salary: "4980.00",
      max_salary: "9360.00",
    },
  ],
};
