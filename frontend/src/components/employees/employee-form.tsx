"use client";

import { useActionState } from "react";

import { SelectField, TextField } from "@/components/form-fields";
import { FormStatus } from "@/components/form-status";
import { Button } from "@/components/ui/button";
import { FieldGroup } from "@/components/ui/field";
import { NativeSelectOption } from "@/components/ui/native-select";
import type { Employee, FilterOptions } from "@/lib/api";
import { countryName } from "@/lib/format";
import { type FormState, INITIAL_FORM_STATE } from "@/lib/forms";

type Props = {
  action: (state: FormState, formData: FormData) => Promise<FormState>;
  options: FilterOptions;
  submitLabel: string;
  /** Present when editing. The country can't change: the salary is in its currency. */
  employee?: Employee;
};

export function EmployeeForm({
  action,
  options,
  submitLabel,
  employee,
}: Props) {
  const [state, formAction, pending] = useActionState(
    action,
    INITIAL_FORM_STATE,
  );
  const errors = state.fieldErrors ?? {};
  const value = (field: keyof Employee) =>
    state.values?.[field] ?? employee?.[field]?.toString();
  return (
    <form action={formAction} className="max-w-xl">
      <FieldGroup>
        <TextField
          label="Name"
          name="name"
          required
          maxLength={200}
          autoComplete="off"
          defaultValue={value("name")}
          error={errors.name}
        />
        <TextField
          label="Email"
          name="email"
          type="email"
          required
          autoComplete="off"
          defaultValue={value("email")}
          error={errors.email}
        />
        {employee ? (
          <p className="text-sm">
            <span className="font-medium">Country:</span>{" "}
            {countryName(employee.country)} ({employee.currency})
          </p>
        ) : (
          <SelectField
            label="Country"
            name="country"
            required
            defaultValue={value("country") ?? ""}
            error={errors.country}
            description="Decides the salary currency, and can't be changed later."
          >
            <NativeSelectOption value="" disabled>
              Choose a country
            </NativeSelectOption>
            {options.countries.map((country) => (
              <NativeSelectOption key={country.code} value={country.code}>
                {countryName(country.code)} ({country.currency})
              </NativeSelectOption>
            ))}
          </SelectField>
        )}
        <SelectField
          label="Job title"
          name="job_title"
          required
          defaultValue={value("job_title") ?? ""}
          error={errors.job_title}
          description="The department follows from the job title."
        >
          <NativeSelectOption value="" disabled>
            Choose a job title
          </NativeSelectOption>
          {options.job_titles.map((job) => (
            <NativeSelectOption key={job.title} value={job.title}>
              {job.title} ({job.department})
            </NativeSelectOption>
          ))}
        </SelectField>
        <TextField
          label="Monthly salary"
          name="monthly_salary"
          inputMode="decimal"
          required
          defaultValue={value("monthly_salary")}
          error={errors.monthly_salary}
          description={
            employee
              ? `In ${employee.currency}.`
              : "In the local currency of the employee's country."
          }
        />
        <FormStatus state={state} successMessage="Changes saved." />
        <div>
          <Button type="submit" disabled={pending}>
            {pending ? "Saving…" : submitLabel}
          </Button>
        </div>
      </FieldGroup>
    </form>
  );
}
