import { describe, expect, it } from "vitest";

import { ApiError } from "@/lib/api/client";

import {
  apiErrorState,
  employeeCreateSchema,
  employeeUpdateSchema,
  parseForm,
  payrollCreateSchema,
  payrollUpdateSchema,
} from "./forms";

function formData(values: Record<string, string>): FormData {
  const data = new FormData();
  for (const [key, value] of Object.entries(values)) {
    data.set(key, value);
  }
  return data;
}

const EMPLOYEE = {
  name: "Grace Hopper",
  email: "grace@example.com",
  monthly_salary: "7000",
  country: "US",
  job_title: "Legal Counsel",
};
const PAYROLL = {
  month: "2026-10",
  base: "7000.00",
  bonus: "0",
  esops: "0",
  payment_method: "bank_transfer",
};

describe("parseForm", () => {
  it("returns the cleaned data and the submitted values", () => {
    const submitted = {
      ...EMPLOYEE,
      name: "  Grace Hopper ",
      email: " Grace@Example.com",
    };

    const result = parseForm(employeeCreateSchema, formData(submitted));

    expect(result).toEqual({
      success: true,
      data: { ...EMPLOYEE, email: "grace@example.com" },
      values: submitted,
    });
  });

  it("ignores the fields React adds to server action submissions", () => {
    const data = formData(EMPLOYEE);
    data.set("$ACTION_ID_abc", "");

    const result = parseForm(employeeCreateSchema, data);

    expect(result).toMatchObject({ success: true, values: EMPLOYEE });
  });

  it("reports the first problem with each field and keeps the values", () => {
    const submitted = { ...EMPLOYEE, name: "", email: "nope" };

    const result = parseForm(employeeCreateSchema, formData(submitted));

    expect(result).toEqual({
      success: false,
      state: {
        status: "error",
        fieldErrors: {
          name: "Enter a name",
          email: "Enter a valid email address",
        },
        values: submitted,
      },
    });
  });
});

describe("employee schemas", () => {
  it.each([
    ["name", { name: "x".repeat(201) }, "Name must be 200 characters or fewer"],
    [
      "monthly_salary",
      { monthly_salary: "-5" },
      "Monthly salary must be an amount like 5000 or 5000.50",
    ],
    [
      "monthly_salary",
      { monthly_salary: "5000.123" },
      "Monthly salary must be an amount like 5000 or 5000.50",
    ],
    [
      "monthly_salary",
      { monthly_salary: "1e5" },
      "Monthly salary must be an amount like 5000 or 5000.50",
    ],
    [
      "monthly_salary",
      { monthly_salary: "1000000000000" },
      "Monthly salary must be an amount like 5000 or 5000.50",
    ],
    ["country", { country: "" }, "Choose a country"],
    ["job_title", { job_title: "" }, "Choose a job title"],
  ])("rejects an invalid %s", (field, overrides, message) => {
    const result = parseForm(
      employeeCreateSchema,
      formData({ ...EMPLOYEE, ...overrides }),
    );

    expect(result).toMatchObject({
      success: false,
      state: { fieldErrors: { [field]: message } },
    });
  });

  it.each(["0", "5000", "5000.5", "999999999999.99"])(
    "accepts the salary %s",
    (salary) => {
      const result = parseForm(
        employeeCreateSchema,
        formData({ ...EMPLOYEE, monthly_salary: salary }),
      );

      expect(result.success).toBe(true);
    },
  );

  it("does not send a country when editing", () => {
    const result = parseForm(employeeUpdateSchema, formData(EMPLOYEE));

    expect(result).toMatchObject({ success: true });
    expect(result.success && "country" in result.data).toBe(false);
  });
});

describe("payroll schemas", () => {
  it("accepts a complete payroll", () => {
    expect(parseForm(payrollCreateSchema, formData(PAYROLL))).toMatchObject({
      success: true,
    });
  });

  it.each([
    ["month", { month: "2026-13" }, "Enter a month like 2026-10"],
    ["base", { base: "" }, "Base pay must be an amount like 5000 or 5000.50"],
    [
      "bonus",
      { bonus: "1.234" },
      "Bonus must be an amount like 5000 or 5000.50",
    ],
    ["esops", { esops: "abc" }, "ESOPs must be an amount like 5000 or 5000.50"],
    ["payment_method", { payment_method: "cash" }, "Choose a payment method"],
  ])("rejects an invalid %s", (field, overrides, message) => {
    const result = parseForm(
      payrollCreateSchema,
      formData({ ...PAYROLL, ...overrides }),
    );

    expect(result).toMatchObject({
      success: false,
      state: { fieldErrors: { [field]: message } },
    });
  });

  it("does not send a month when editing", () => {
    const result = parseForm(payrollUpdateSchema, formData(PAYROLL));

    expect(result.success && "month" in result.data).toBe(false);
  });
});

describe("apiErrorState", () => {
  const values = { email: "grace@example.com" };

  it("shows a conflict on the field it concerns", () => {
    const error = new ApiError(
      409,
      "An employee with email grace@example.com already exists",
    );

    expect(apiErrorState(error, values, "email")).toEqual({
      status: "error",
      fieldErrors: {
        email: "An employee with email grace@example.com already exists",
      },
      values,
    });
  });

  it("shows other API errors as a form message with any field errors", () => {
    const error = new ApiError(422, "unknown job title", {
      job_title: "unknown job title",
    });

    expect(apiErrorState(error, values, "email")).toEqual({
      status: "error",
      message: "unknown job title",
      fieldErrors: { job_title: "unknown job title" },
      values,
    });
  });

  it("shows a conflict as a form message when no field is given", () => {
    const error = new ApiError(
      409,
      "Employee 1 already has a payroll for 2026-10",
    );

    expect(apiErrorState(error, values)).toMatchObject({
      message: "Employee 1 already has a payroll for 2026-10",
    });
  });

  it("shows unexpected errors such as an unreachable API as a message", () => {
    const error = new Error("Could not reach the API at http://localhost:8000");

    expect(apiErrorState(error, values)).toEqual({
      status: "error",
      message: "Could not reach the API at http://localhost:8000",
      values,
    });
  });

  it("rethrows things that are not errors", () => {
    expect(() => apiErrorState("boom", values)).toThrow("boom");
  });
});
