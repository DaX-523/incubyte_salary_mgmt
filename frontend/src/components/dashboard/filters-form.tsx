import { ChevronDown, SlidersHorizontal } from "lucide-react";
import Form from "next/form";
import Link from "next/link";

import { SelectField, TextField } from "@/components/form-fields";
import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { NativeSelectOption } from "@/components/ui/native-select";
import type { FilterOptions } from "@/lib/api";
import {
  activeFilterLabels,
  DEFAULT_PAGE_SIZE,
  type DashboardQuery,
  salarySortNeedsCountry,
} from "@/lib/dashboard-query";
import { countryName } from "@/lib/format";

type Props = { query: DashboardQuery; options: FilterOptions };

const SALARY_SORT_HINT =
  "Salaries are in local currency, so salary sorting needs a country.";
const SALARY_SORT_NEEDS_COUNTRY =
  "Choose a country to sort by salary. Until then, the list is sorted by name.";

/**
 * A collapsible panel around a plain GET form: filters live in the URL, so every view can be
 * bookmarked and shared. `<details>` opens and closes without any JavaScript.
 */
export function FiltersForm({ query, options }: Props) {
  const countries = [...options.countries].sort((a, b) =>
    countryName(a.code).localeCompare(countryName(b.code)),
  );
  const needsCountry = salarySortNeedsCountry(query);
  return (
    <details className="group rounded-xl border bg-card text-card-foreground shadow-xs transition-all hover:border-foreground/20 hover:shadow-md open:shadow-md motion-reduce:transition-none">
      <FiltersSummary activeFilters={activeFilterLabels(query)} />
      {/* Rebuilt whenever the applied filters change (Apply, Reset, back and forward), so the
          fields show what the list uses rather than edits that were never applied. */}
      <Form
        key={JSON.stringify(query)}
        action="/"
        aria-label="Filters"
        className="grid animate-in gap-4 border-t p-4 duration-200 fade-in slide-in-from-top-1 sm:grid-cols-2 lg:grid-cols-4"
      >
        {query.page_size !== DEFAULT_PAGE_SIZE && (
          <input type="hidden" name="page_size" value={query.page_size} />
        )}
        <TextField
          label="Month"
          name="month"
          type="month"
          defaultValue={query.month}
          required
        />
        <TextField
          label="Name"
          name="name"
          type="search"
          maxLength={200}
          defaultValue={query.name}
        />
        <TextField
          label="Email"
          name="email"
          type="search"
          inputMode="email"
          maxLength={320}
          defaultValue={query.email}
        />
        <SelectField
          label="Country"
          name="country"
          defaultValue={query.country ?? ""}
        >
          <NativeSelectOption value="">All countries</NativeSelectOption>
          {countries.map((country) => (
            <NativeSelectOption key={country.code} value={country.code}>
              {countryName(country.code)}
            </NativeSelectOption>
          ))}
        </SelectField>
        <SelectField
          label="Job title"
          name="job_title"
          defaultValue={query.job_title ?? ""}
        >
          <NativeSelectOption value="">All job titles</NativeSelectOption>
          {options.job_titles.map((job) => (
            <NativeSelectOption key={job.title} value={job.title}>
              {job.title}
            </NativeSelectOption>
          ))}
        </SelectField>
        <SelectField
          label="Sort by"
          name="sort_by"
          defaultValue={query.sort_by}
          description={needsCountry ? undefined : SALARY_SORT_HINT}
          error={needsCountry ? SALARY_SORT_NEEDS_COUNTRY : undefined}
        >
          <NativeSelectOption value="name">Name</NativeSelectOption>
          <NativeSelectOption value="monthly_salary">
            Monthly salary
          </NativeSelectOption>
        </SelectField>
        <SelectField
          label="Order"
          name="sort_order"
          defaultValue={query.sort_order}
        >
          <NativeSelectOption value="asc">Ascending</NativeSelectOption>
          <NativeSelectOption value="desc">Descending</NativeSelectOption>
        </SelectField>
        <div className="flex items-end gap-2">
          <Button type="submit">Apply filters</Button>
          <Link href="/" className={buttonVariants({ variant: "outline" })}>
            Reset
          </Link>
        </div>
      </Form>
    </details>
  );
}

/** The always-visible bar: what is filtered right now, and an inviting way to open the panel. */
function FiltersSummary({ activeFilters }: { activeFilters: string[] }) {
  return (
    <summary className="flex cursor-pointer list-none items-center gap-3 rounded-xl bg-linear-to-r from-muted/70 to-transparent p-4 transition-colors outline-none select-none hover:from-muted group-open:from-transparent focus-visible:ring-3 focus-visible:ring-ring/50 group-open:rounded-b-none sm:gap-4 [&::-webkit-details-marker]:hidden">
      <span
        aria-hidden="true"
        className="grid size-10 shrink-0 place-items-center rounded-lg bg-primary/10 text-primary transition-all duration-200 group-hover:scale-110 group-hover:bg-primary group-hover:text-primary-foreground group-open:bg-primary group-open:text-primary-foreground motion-reduce:transition-none"
      >
        <SlidersHorizontal className="size-5" />
      </span>
      <span className="grid min-w-0 flex-1 gap-1.5">
        <span className="font-medium">Filters and sorting</span>
        {activeFilters.length > 0 ? (
          <span className="flex flex-wrap gap-1.5">
            {activeFilters.map((label) => (
              <Badge key={label} variant="secondary" className="max-w-full">
                <span className="truncate">{label}</span>
              </Badge>
            ))}
          </span>
        ) : (
          <span className="text-sm text-muted-foreground">
            Search by name or email, or narrow down to a country and job title
          </span>
        )}
      </span>
      {activeFilters.length > 0 && (
        <Badge className="hidden sm:inline-flex">
          {activeFilters.length} active
        </Badge>
      )}
      <span
        aria-hidden="true"
        className="flex shrink-0 items-center gap-1 rounded-full border border-transparent bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground shadow-sm transition-all group-hover:shadow-md group-open:border-border group-open:bg-transparent group-open:text-foreground group-open:shadow-none motion-reduce:transition-none"
      >
        <span className="group-open:hidden">Show filters</span>
        <span className="hidden group-open:inline">Hide</span>
        <ChevronDown className="size-4 transition-transform duration-200 group-open:rotate-180 motion-reduce:transition-none" />
      </span>
    </summary>
  );
}
