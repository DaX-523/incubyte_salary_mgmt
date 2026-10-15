import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { type DashboardQuery, dashboardHref } from "@/lib/dashboard-query";
import { formatCount } from "@/lib/format";
import { pageRange } from "@/lib/pagination";

import { RowsPerPage } from "./rows-per-page";

type Props = { query: DashboardQuery; total: number; pageSize: number };

export function Pagination({ query, total, pageSize }: Props) {
  const { first, last, totalPages } = pageRange(query.page, pageSize, total);
  const linkClass = buttonVariants({ variant: "outline", size: "sm" });
  return (
    <nav
      aria-label="Pagination"
      className="flex flex-wrap items-center justify-between gap-3"
    >
      <p className="text-sm text-muted-foreground">
        {first > 0
          ? `Showing ${formatCount(first)}–${formatCount(last)} of ${formatCount(total)}`
          : `No results on page ${query.page}`}
      </p>
      <div className="flex flex-wrap items-center gap-4">
        <RowsPerPage query={query} />
        <div className="flex gap-2">
          {query.page > 1 && (
            <Link
              href={dashboardHref({ ...query, page: query.page - 1 })}
              className={linkClass}
            >
              Previous page
            </Link>
          )}
          {query.page < totalPages && (
            <Link
              href={dashboardHref({ ...query, page: query.page + 1 })}
              className={linkClass}
            >
              Next page
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}
