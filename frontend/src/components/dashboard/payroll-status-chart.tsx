import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { PayrollStatus } from "@/lib/api";
import { formatCount, formatMonth } from "@/lib/format";
import { paidPercentage } from "@/lib/payroll-status";

/** Paid vs total employees for the month, for whatever the filters select. */
export function PayrollStatusChart({ status }: { status: PayrollStatus }) {
  const percent = paidPercentage(status);
  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <h2>Paid vs total employees</h2>
        </CardTitle>
        <CardDescription>{formatMonth(status.month)}</CardDescription>
      </CardHeader>
      <CardContent>
        {percent === null ? (
          <p className="text-sm text-muted-foreground">
            No employees on the books for this month.
          </p>
        ) : (
          <figure className="grid gap-3">
            <div
              role="img"
              aria-label={`${formatCount(status.paid)} of ${formatCount(status.total)} employees paid (${percent}%)`}
              className="flex h-4 overflow-hidden rounded-full bg-muted"
            >
              <div className="bg-primary" style={{ width: `${percent}%` }} />
            </div>
            <figcaption>
              <p className="text-2xl font-semibold">{percent}% paid</p>
              <dl className="mt-2 grid grid-cols-3 gap-2 text-sm">
                <StatusCount label="Paid" value={status.paid} />
                <StatusCount label="Unpaid" value={status.unpaid} />
                <StatusCount label="Total" value={status.total} />
              </dl>
            </figcaption>
          </figure>
        )}
      </CardContent>
    </Card>
  );
}

function StatusCount({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="font-medium">{formatCount(value)}</dd>
    </div>
  );
}
