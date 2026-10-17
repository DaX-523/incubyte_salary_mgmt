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
import type { PayByJobTitle } from "@/lib/api";
import { dashboardHref } from "@/lib/dashboard-query";
import { countryName, formatCount, formatMoney } from "@/lib/format";

/** Salary range and average per job title in one country, with a link to rank its peers by pay. */
export function PayByJobTitleTable({ data }: { data: PayByJobTitle }) {
  const country = countryName(data.country);
  if (data.job_titles.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No active employees in {country}.
      </p>
    );
  }
  return (
    <Table>
      <TableCaption>
        Monthly salaries of active employees in {country}, in {data.currency}
      </TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead>Department</TableHead>
          <TableHead>Job title</TableHead>
          <TableHead className="text-right">Headcount</TableHead>
          <TableHead className="text-right">Lowest</TableHead>
          <TableHead className="text-right">Average</TableHead>
          <TableHead className="text-right">Highest</TableHead>
          <TableHead>
            <span className="sr-only">Peers</span>
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.job_titles.map((row) => (
          <TableRow key={row.job_title}>
            <TableCell>{row.department}</TableCell>
            <TableCell>{row.job_title}</TableCell>
            <TableCell className="text-right tabular-nums">
              {formatCount(row.headcount)}
            </TableCell>
            <TableCell className="text-right tabular-nums">
              {formatMoney(row.min_salary, data.currency)}
            </TableCell>
            <TableCell className="text-right tabular-nums">
              {formatMoney(row.average_salary, data.currency)}
            </TableCell>
            <TableCell className="text-right tabular-nums">
              {formatMoney(row.max_salary, data.currency)}
            </TableCell>
            <TableCell>
              <Link
                href={dashboardHref({
                  country: data.country,
                  job_title: row.job_title,
                  sort_by: "monthly_salary",
                  sort_order: "desc",
                })}
                aria-label={`Rank ${row.job_title} salaries in ${country}`}
                className="text-sm underline-offset-4 hover:underline"
              >
                Rank by salary
              </Link>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
