import { refresh } from "next/cache";
import { redirect } from "next/navigation";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  ApiError,
  createEmployee,
  createPayroll,
  deactivateEmployee,
  updateEmployee,
} from "@/lib/api";
import { ADA, ADA_OCTOBER_PAYROLL } from "@/test/fixtures";

import {
  createEmployeeAction,
  createPayrollAction,
  deactivateEmployeeAction,
  updateEmployeeAction,
} from "./actions";

vi.mock("next/cache", () => ({ refresh: vi.fn() }));
vi.mock("next/navigation", async (importOriginal) => ({
  ...(await importOriginal<typeof import("next/navigation")>()),
  redirect: vi.fn(),
}));
vi.mock("@/lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/api")>()),
  createEmployee: vi.fn(),
  updateEmployee: vi.fn(),
  deactivateEmployee: vi.fn(),
  createPayroll: vi.fn(),
}));

const IDLE = { status: "idle" } as const;
const NEW_EMPLOYEE = {
  name: "Grace Hopper",
  email: "Grace@Example.com",
  monthly_salary: "7000",
  country: "US",
  job_title: "Legal Counsel",
};
const NEW_PAYROLL = {
  month: "2026-10",
  base: "4780.00",
  bonus: "0",
  esops: "0",
  payment_method: "bank_transfer",
};

function formData(values: Record<string, string>): FormData {
  const data = new FormData();
  for (const [key, value] of Object.entries(values)) {
    data.set(key, value);
  }
  return data;
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("createEmployeeAction", () => {
  it("creates the employee and opens their page", async () => {
    vi.mocked(createEmployee).mockResolvedValue({ ...ADA, id: 7 });

    await createEmployeeAction(IDLE, formData(NEW_EMPLOYEE));

    expect(createEmployee).toHaveBeenCalledWith({
      ...NEW_EMPLOYEE,
      email: "grace@example.com",
    });
    expect(redirect).toHaveBeenCalledWith("/employees/7");
  });

  it("returns field errors without calling the API when the form is invalid", async () => {
    const state = await createEmployeeAction(
      IDLE,
      formData({ ...NEW_EMPLOYEE, name: " " }),
    );

    expect(state).toMatchObject({
      status: "error",
      fieldErrors: { name: "Enter a name" },
    });
    expect(createEmployee).not.toHaveBeenCalled();
  });

  it("shows a taken email on the email field", async () => {
    vi.mocked(createEmployee).mockRejectedValue(
      new ApiError(
        409,
        "An employee with email grace@example.com already exists",
      ),
    );

    const state = await createEmployeeAction(IDLE, formData(NEW_EMPLOYEE));

    expect(state.fieldErrors).toEqual({
      email: "An employee with email grace@example.com already exists",
    });
    expect(state.values).toEqual(NEW_EMPLOYEE);
    expect(redirect).not.toHaveBeenCalled();
  });
});

describe("updateEmployeeAction", () => {
  it("saves the changes without the country and refreshes the page", async () => {
    vi.mocked(updateEmployee).mockResolvedValue(ADA);

    const state = await updateEmployeeAction(1, IDLE, formData(NEW_EMPLOYEE));

    expect(updateEmployee).toHaveBeenCalledWith(1, {
      name: "Grace Hopper",
      email: "grace@example.com",
      monthly_salary: "7000",
      job_title: "Legal Counsel",
    });
    expect(refresh).toHaveBeenCalledOnce();
    expect(state.status).toBe("success");
  });

  it("returns field errors without calling the API when the form is invalid", async () => {
    const state = await updateEmployeeAction(
      1,
      IDLE,
      formData({ ...NEW_EMPLOYEE, email: "x" }),
    );

    expect(state.fieldErrors).toEqual({ email: "Enter a valid email address" });
    expect(updateEmployee).not.toHaveBeenCalled();
  });

  it("reports API failures and does not refresh", async () => {
    vi.mocked(updateEmployee).mockRejectedValue(
      new ApiError(404, "Employee 1 not found"),
    );

    const state = await updateEmployeeAction(1, IDLE, formData(NEW_EMPLOYEE));

    expect(state).toMatchObject({
      status: "error",
      message: "Employee 1 not found",
    });
    expect(refresh).not.toHaveBeenCalled();
  });
});

describe("deactivateEmployeeAction", () => {
  it("deactivates the employee and refreshes the page", async () => {
    vi.mocked(deactivateEmployee).mockResolvedValue(undefined);

    await deactivateEmployeeAction(1);

    expect(deactivateEmployee).toHaveBeenCalledWith(1);
    expect(refresh).toHaveBeenCalledOnce();
  });
});

describe("createPayrollAction", () => {
  it("records the payroll and opens it", async () => {
    vi.mocked(createPayroll).mockResolvedValue(ADA_OCTOBER_PAYROLL);

    await createPayrollAction(1, IDLE, formData(NEW_PAYROLL));

    expect(createPayroll).toHaveBeenCalledWith(1, NEW_PAYROLL);
    expect(redirect).toHaveBeenCalledWith("/payrolls/12");
  });

  it("returns field errors without calling the API when the form is invalid", async () => {
    const state = await createPayrollAction(
      1,
      IDLE,
      formData({ ...NEW_PAYROLL, month: "10/2026" }),
    );

    expect(state.fieldErrors).toEqual({ month: "Enter a month like 2026-10" });
    expect(createPayroll).not.toHaveBeenCalled();
  });

  it("shows a duplicate month as a message for the whole form", async () => {
    vi.mocked(createPayroll).mockRejectedValue(
      new ApiError(409, "Employee 1 already has a payroll for 2026-10"),
    );

    const state = await createPayrollAction(1, IDLE, formData(NEW_PAYROLL));

    expect(state).toMatchObject({
      status: "error",
      message: "Employee 1 already has a payroll for 2026-10",
    });
    expect(redirect).not.toHaveBeenCalled();
  });
});
