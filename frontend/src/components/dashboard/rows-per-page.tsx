"use client";

import { useRouter } from "next/navigation";

import {
  NativeSelect,
  NativeSelectOption,
} from "@/components/ui/native-select";
import {
  type DashboardQuery,
  dashboardHref,
  PAGE_SIZES,
  parsePageSize,
} from "@/lib/dashboard-query";

/** Changing the page size keeps the filters and starts again from the first page. */
export function RowsPerPage({ query }: { query: DashboardQuery }) {
  const router = useRouter();
  return (
    <label className="flex items-center gap-2 text-sm text-muted-foreground">
      Rows per page
      <NativeSelect
        key={query.page_size}
        size="sm"
        defaultValue={query.page_size}
        onChange={(event) =>
          router.push(
            dashboardHref({
              ...query,
              page: 1,
              page_size: parsePageSize(event.target.value),
            }),
          )
        }
      >
        {PAGE_SIZES.map((size) => (
          <NativeSelectOption key={size} value={size}>
            {size}
          </NativeSelectOption>
        ))}
      </NativeSelect>
    </label>
  );
}
