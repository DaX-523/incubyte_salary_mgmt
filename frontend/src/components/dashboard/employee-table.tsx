import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { MonthlyEmployee } from "@/lib/api";
import { countryName, formatMoney, formatMonth } from "@/lib/format";

type Props = { rows: MonthlyEmployee[]; month: string };

export function EmployeeTable({ rows, month }: Props) {
  if (rows.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No employees match these filters.
      </p>
    );
  }
  return (
    <Table>
      <TableCaption>
        Employees on the books in {formatMonth(month)}
      </TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead>ID</TableHead>
          <TableHead>Name</TableHead>
          <TableHead>Country</TableHead>
          <TableHead>Job title</TableHead>
          <TableHead className="text-right">Monthly salary</TableHead>
          <TableHead>Payroll</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map(({ employee, payroll }) => (
          <TableRow key={employee.id} className="relative">
            <TableCell>{employee.id}</TableCell>
            <TableCell>
              <Link
                href={`/employees/${employee.id}`}
                className="font-medium after:absolute after:inset-0 after:z-10 after:content-[''] hover:underline"
              >
                {employee.name}
              </Link>
              {!employee.is_active && (
                <Badge variant="outline" className="ml-2">
                  Inactive
                </Badge>
              )}
            </TableCell>
            <TableCell>{countryName(employee.country)}</TableCell>
            <TableCell>{employee.job_title}</TableCell>
            <TableCell className="text-right tabular-nums">
              {formatMoney(employee.monthly_salary, employee.currency)}
            </TableCell>
            <TableCell>
              {payroll ? (
                <Badge
                  className="relative z-20"
                  render={<Link href={`/payrolls/${payroll.id}`} />}
                >
                  Paid
                </Badge>
              ) : (
                <Badge variant="secondary">Unpaid</Badge>
              )}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
