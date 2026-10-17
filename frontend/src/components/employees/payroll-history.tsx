import Link from "next/link";

import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { Payroll } from "@/lib/api";
import { formatMoney, formatMonth, paymentMethodLabel } from "@/lib/format";

/** What an employee was paid each month, newest first; each month opens its payroll to correct. */
export function PayrollHistory({ payrolls }: { payrolls: Payroll[] }) {
  if (payrolls.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">No payrolls recorded yet.</p>
    );
  }
  return (
    <Table>
      <TableCaption>Payrolls, newest month first</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead>Month</TableHead>
          <TableHead className="text-right">Base pay</TableHead>
          <TableHead className="text-right">Bonus</TableHead>
          <TableHead className="text-right">ESOPs</TableHead>
          <TableHead>Payment method</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {payrolls.map((payroll) => (
          <TableRow key={payroll.id}>
            <TableCell>
              <Link
                href={`/payrolls/${payroll.id}`}
                className="font-medium underline-offset-4 hover:underline"
              >
                {formatMonth(payroll.month)}
              </Link>
            </TableCell>
            <TableCell className="text-right tabular-nums">
              {formatMoney(payroll.base, payroll.currency)}
            </TableCell>
            <TableCell className="text-right tabular-nums">
              {formatMoney(payroll.bonus, payroll.currency)}
            </TableCell>
            <TableCell className="text-right tabular-nums">
              {formatMoney(payroll.esops, payroll.currency)}
            </TableCell>
            <TableCell>{paymentMethodLabel(payroll.payment_method)}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
