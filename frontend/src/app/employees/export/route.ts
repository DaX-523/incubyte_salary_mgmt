import { exportEmployeesForMonth, getFilterOptions } from "@/lib/api";
import {
  allowedFilters,
  employeeExportFileName,
  employeeExportQuery,
  parseDashboardQuery,
} from "@/lib/dashboard-query";

/** The dashboard's employee list as a CSV download: the same filters and order, every page. */
export async function GET(request: Request) {
  const params = Object.fromEntries(new URL(request.url).searchParams);
  const options = await getFilterOptions();
  const query = parseDashboardQuery(
    params,
    allowedFilters(options, new Date()),
  );
  const csv = await exportEmployeesForMonth(employeeExportQuery(query));
  return new Response(csv, {
    headers: {
      "Content-Type": "text/csv; charset=utf-8",
      "Content-Disposition": `attachment; filename="${employeeExportFileName(query.month)}"`,
    },
  });
}
