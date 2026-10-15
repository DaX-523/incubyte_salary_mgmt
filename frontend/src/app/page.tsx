import { EmployeeTable } from "@/components/dashboard/employee-table";
import { FiltersForm } from "@/components/dashboard/filters-form";
import { Pagination } from "@/components/dashboard/pagination";
import { PayrollStatusChart } from "@/components/dashboard/payroll-status-chart";
import {
  getFilterOptions,
  getPayrollStatus,
  listEmployeesForMonth,
} from "@/lib/api";
import { parseDashboardQuery } from "@/lib/dashboard-query";
import { formatMonth } from "@/lib/format";
import { currentMonth } from "@/lib/month";

export default async function DashboardPage({ searchParams }: PageProps<"/">) {
  const [params, options] = await Promise.all([
    searchParams,
    getFilterOptions(),
  ]);
  const query = parseDashboardQuery(params, {
    month: currentMonth(new Date()),
    countries: options.countries.map((country) => country.code),
    jobTitles: options.job_titles.map((job) => job.title),
  });
  const [status, employees] = await Promise.all([
    getPayrollStatus({
      month: query.month,
      country: query.country,
      job_title: query.job_title,
    }),
    listEmployeesForMonth(query),
  ]);
  return (
    <main className="mx-auto grid max-w-6xl gap-8 px-4 py-8 sm:px-8">
      <header>
        <h1 className="text-2xl font-semibold">Payroll dashboard</h1>
        <p className="text-muted-foreground">{formatMonth(query.month)}</p>
      </header>
      <PayrollStatusChart status={status} />
      <FiltersForm query={query} options={options} />
      <section aria-labelledby="employees-heading" className="grid gap-4">
        <h2 id="employees-heading" className="text-lg font-semibold">
          Employees
        </h2>
        <EmployeeTable rows={employees.items} month={query.month} />
        <Pagination
          query={query}
          total={employees.total}
          pageSize={employees.page_size}
        />
      </section>
    </main>
  );
}
