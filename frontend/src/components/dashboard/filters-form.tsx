import Form from "next/form";
import Link from "next/link";

import { SelectField, TextField } from "@/components/form-fields";
import { Button, buttonVariants } from "@/components/ui/button";
import { NativeSelectOption } from "@/components/ui/native-select";
import type { FilterOptions } from "@/lib/api";
import type { DashboardQuery } from "@/lib/dashboard-query";
import { countryName } from "@/lib/format";

type Props = { query: DashboardQuery; options: FilterOptions };

/** A plain GET form: filters live in the URL, so every view can be bookmarked and shared. */
export function FiltersForm({ query, options }: Props) {
  const countries = [...options.countries].sort((a, b) =>
    countryName(a.code).localeCompare(countryName(b.code)),
  );
  return (
    <Form
      action="/"
      aria-label="Filters"
      className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"
    >
      <TextField
        label="Month"
        name="month"
        type="month"
        defaultValue={query.month}
        required
      />
      <TextField
        label="Employee ID"
        name="id"
        type="number"
        min={1}
        defaultValue={query.id}
      />
      <TextField
        label="Name"
        name="name"
        type="search"
        maxLength={200}
        defaultValue={query.name}
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
        description="Salaries are in local currency, so salary sorting needs a country."
      >
        <NativeSelectOption value="id">Employee ID</NativeSelectOption>
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
  );
}
