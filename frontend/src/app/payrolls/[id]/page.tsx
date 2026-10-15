import Link from "next/link";
import { notFound } from "next/navigation";

import { PayrollForm } from "@/components/payrolls/payroll-form";
import { getEmployee, getFilterOptions, getPayroll } from "@/lib/api";
import { formatMoney, formatMonth, paymentMethodLabel } from "@/lib/format";
import { positiveInteger } from "@/lib/search-params";

import { loadOr404 } from "../../load-or-404";
import { updatePayrollAction } from "../actions";

export default async function PayrollPage({
  params,
}: PageProps<"/payrolls/[id]">) {
  const payrollId = positiveInteger((await params).id);
  if (payrollId === undefined) {
    notFound();
  }
  const [payroll, options] = await Promise.all([
    loadOr404(getPayroll(payrollId)),
    getFilterOptions(),
  ]);
  const employee = await getEmployee(payroll.employee_id);
  const details = [
    ["Base pay", formatMoney(payroll.base, payroll.currency)],
    ["Bonus", formatMoney(payroll.bonus, payroll.currency)],
    ["ESOPs", formatMoney(payroll.esops, payroll.currency)],
    ["Payment method", paymentMethodLabel(payroll.payment_method)],
  ] as const;
  return (
    <main className="mx-auto grid max-w-6xl gap-10 px-4 py-8 sm:px-8">
      <header>
        <h1 className="text-2xl font-semibold">
          Payroll for {formatMonth(payroll.month)}
        </h1>
        <p className="text-muted-foreground">
          Paid to{" "}
          <Link
            href={`/employees/${employee.id}`}
            className="underline underline-offset-4"
          >
            {employee.name}
          </Link>{" "}
          in {payroll.currency}
        </p>
      </header>
      <dl className="grid gap-x-8 gap-y-3 text-sm sm:grid-cols-2">
        {details.map(([label, value]) => (
          <div key={label}>
            <dt className="text-muted-foreground">{label}</dt>
            <dd className="font-medium">{value}</dd>
          </div>
        ))}
      </dl>
      <section aria-labelledby="edit-heading" className="grid gap-4">
        <h2 id="edit-heading" className="text-lg font-semibold">
          Correct this payroll
        </h2>
        <PayrollForm
          action={updatePayrollAction.bind(null, payroll.id)}
          currency={payroll.currency}
          paymentMethods={options.payment_methods}
          defaults={payroll}
          submitLabel="Save changes"
          withMonth={false}
        />
      </section>
    </main>
  );
}
