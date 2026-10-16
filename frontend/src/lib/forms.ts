import { unstable_rethrow } from "next/navigation";
import { z } from "zod";

import { ApiError } from "@/lib/api/client";
import { MONTH_PATTERN } from "@/lib/month";

/** What a form's server action reports back: field errors, a message, and the values to keep. */
export type FormState = {
  status: "idle" | "error" | "success";
  message?: string;
  fieldErrors?: Record<string, string>;
  values?: Record<string, string>;
};

export const INITIAL_FORM_STATE: FormState = { status: "idle" };

// Up to 999,999,999,999.99: the most the database stores. Never parsed into a float.
const MONEY_PATTERN = /^\d{1,12}(\.\d{1,2})?$/;

function money(label: string) {
  return z
    .string()
    .trim()
    .regex(MONEY_PATTERN, `${label} must be an amount like 5000 or 5000.50`);
}

const name = z
  .string()
  .trim()
  .min(1, "Enter a name")
  .max(200, "Name must be 200 characters or fewer");
const email = z
  .string()
  .trim()
  .toLowerCase()
  .pipe(z.email({ error: "Enter a valid email address" }));
const jobTitle = z.string().min(1, "Choose a job title");
const paymentMethod = z.enum(["bank_transfer", "digital_wallet"], {
  error: "Choose a payment method",
});

export const employeeCreateSchema = z.object({
  name,
  email,
  monthly_salary: money("Monthly salary"),
  country: z.string().min(1, "Choose a country"),
  job_title: jobTitle,
});

// The country is fixed once an employee exists: their salary is in its currency.
export const employeeUpdateSchema = employeeCreateSchema.omit({
  country: true,
});

// Only checked for presence: the API decides whether the credentials are right.
export const loginSchema = z.object({
  email: z
    .string({ error: "Enter your email" })
    .trim()
    .min(1, "Enter your email"),
  password: z
    .string({ error: "Enter your password" })
    .min(1, "Enter your password"),
});

export const payrollUpdateSchema = z.object({
  base: money("Base pay"),
  bonus: money("Bonus"),
  esops: money("ESOPs"),
  payment_method: paymentMethod,
});

export const payrollCreateSchema = payrollUpdateSchema.extend({
  month: z.string().regex(MONTH_PATTERN, "Enter a month like 2026-10"),
});

export type ParsedForm<Data> =
  | { success: true; data: Data; values: Record<string, string> }
  | { success: false; state: FormState };

export function parseForm<Data>(
  schema: z.ZodType<Data>,
  formData: FormData,
): ParsedForm<Data> {
  const values = formValues(formData);
  const result = schema.safeParse(values);
  if (result.success) {
    return { success: true, data: result.data, values };
  }
  const fieldErrors: Record<string, string> = {};
  for (const [field, messages] of Object.entries(
    z.flattenError(result.error).fieldErrors,
  )) {
    const [message] = messages as string[];
    fieldErrors[field] = message;
  }
  return { success: false, state: { status: "error", fieldErrors, values } };
}

/**
 * Turns a failed API call into form feedback. A 409 Conflict is shown on `conflictField` when
 * given (for example "email"), otherwise as a message for the whole form.
 */
export function apiErrorState(
  error: unknown,
  values: Record<string, string>,
  conflictField?: string,
): FormState {
  // Next.js redirects (for example to the login page) are thrown errors that must pass through.
  unstable_rethrow(error);
  if (error instanceof ApiError) {
    if (error.status === 409 && conflictField) {
      return {
        status: "error",
        fieldErrors: { [conflictField]: error.message },
        values,
      };
    }
    return {
      status: "error",
      message: error.message,
      fieldErrors: error.fieldErrors,
      values,
    };
  }
  if (error instanceof Error) {
    return { status: "error", message: error.message, values };
  }
  throw error;
}

function formValues(formData: FormData): Record<string, string> {
  const values: Record<string, string> = {};
  formData.forEach((value, key) => {
    // React adds $ACTION_* entries to server action form data.
    if (typeof value === "string" && !key.startsWith("$ACTION")) {
      values[key] = value;
    }
  });
  return values;
}
