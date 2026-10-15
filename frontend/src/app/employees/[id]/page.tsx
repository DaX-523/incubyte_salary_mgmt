import { notFound } from "next/navigation";

import { DeactivateEmployee } from "@/components/employees/deactivate-employee";
import { EmployeeDetails } from "@/components/employees/employee-details";
import { EmployeeForm } from "@/components/employees/employee-form";
import { PayrollForm } from "@/components/payrolls/payroll-form";
import { Badge } from "@/components/ui/badge";
import { getEmployee, getFilterOptions } from "@/lib/api";
import { currentMonth } from "@/lib/month";
import { positiveInteger } from "@/lib/search-params";

import { loadOr404 } from "../../load-or-404";
import {
  createPayrollAction,
  deactivateEmployeeAction,
  updateEmployeeAction,
} from "../actions";

export default async function EmployeePage({
  params,
}: PageProps<"/employees/[id]">) {
  const employeeId = positiveInteger((await params).id);
  if (employeeId === undefined) {
    notFound();
  }
  const [employee, options] = await Promise.all([
    loadOr404(getEmployee(employeeId)),
    getFilterOptions(),
  ]);
  return (
    <main className="mx-auto grid max-w-6xl gap-10 px-4 py-8 sm:px-8">
      <header className="flex items-center gap-3">
        <h1 className="text-2xl font-semibold">{employee.name}</h1>
        {!employee.is_active && <Badge variant="outline">Inactive</Badge>}
      </header>
      <EmployeeDetails employee={employee} />
      <section aria-labelledby="edit-heading" className="grid gap-4">
        <h2 id="edit-heading" className="text-lg font-semibold">
          Edit details
        </h2>
        <EmployeeForm
          action={updateEmployeeAction.bind(null, employee.id)}
          options={options}
          employee={employee}
          submitLabel="Save changes"
        />
      </section>
      {employee.is_active ? (
        <>
          <section aria-labelledby="payroll-heading" className="grid gap-4">
            <h2 id="payroll-heading" className="text-lg font-semibold">
              Record a payroll
            </h2>
            <PayrollForm
              action={createPayrollAction.bind(null, employee.id)}
              currency={employee.currency}
              paymentMethods={options.payment_methods}
              defaults={{
                month: currentMonth(new Date()),
                base: employee.monthly_salary,
                bonus: "0",
                esops: "0",
                payment_method: "bank_transfer",
              }}
              submitLabel="Record payroll"
              withMonth
            />
          </section>
          <section aria-labelledby="deactivate-heading" className="grid gap-4">
            <h2 id="deactivate-heading" className="text-lg font-semibold">
              Deactivate
            </h2>
            <DeactivateEmployee
              name={employee.name}
              action={deactivateEmployeeAction.bind(null, employee.id)}
            />
          </section>
        </>
      ) : (
        <p className="text-sm text-muted-foreground">
          This employee is inactive: their payroll history is kept, but no new
          payrolls can be recorded.
        </p>
      )}
    </main>
  );
}
