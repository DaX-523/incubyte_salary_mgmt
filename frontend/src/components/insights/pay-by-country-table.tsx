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
import type { PayByCountry } from "@/lib/api";
import {
  byCountryName,
  countryName,
  formatCount,
  formatMoney,
} from "@/lib/format";

/**
 * Headcount and monthly salaries per country, each in its own currency. There is deliberately no
 * total row: it would add up different currencies.
 */
export function PayByCountryTable({ data }: { data: PayByCountry }) {
  if (data.countries.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">No active employees yet.</p>
    );
  }
  const rows = [...data.countries].sort((a, b) =>
    byCountryName(a.country, b.country),
  );
  return (
    <Table>
      <TableCaption>
        Monthly salaries of active employees, each country in its own currency
      </TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead>Country</TableHead>
          <TableHead>Currency</TableHead>
          <TableHead className="text-right">Headcount</TableHead>
          <TableHead className="text-right">Average salary</TableHead>
          <TableHead className="text-right">Total monthly salaries</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map((row) => (
          <TableRow key={row.country}>
            <TableCell>
              <Link
                href={`/insights?country=${row.country}`}
                aria-label={`Pay by job title in ${countryName(row.country)}`}
                className="underline-offset-4 hover:underline"
              >
                {countryName(row.country)}
              </Link>
            </TableCell>
            <TableCell>{row.currency}</TableCell>
            <TableCell className="text-right tabular-nums">
              {formatCount(row.headcount)}
            </TableCell>
            <TableCell className="text-right tabular-nums">
              {formatMoney(row.average_salary, row.currency)}
            </TableCell>
            <TableCell className="text-right tabular-nums">
              {formatMoney(row.total_monthly_salary, row.currency)}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
