"use server";

import { refresh } from "next/cache";
import { redirect } from "next/navigation";

import {
  createEmployee,
  createPayroll,
  deactivateEmployee,
  type Employee,
  type Payroll,
  updateEmployee,
} from "@/lib/api";
import {
  apiErrorState,
  employeeCreateSchema,
  employeeUpdateSchema,
  type FormState,
  parseForm,
  payrollCreateSchema,
} from "@/lib/forms";

export async function createEmployeeAction(
  _state: FormState,
  formData: FormData,
): Promise<FormState> {
  const form = parseForm(employeeCreateSchema, formData);
  if (!form.success) {
    return form.state;
  }
  let employee: Employee;
  try {
    employee = await createEmployee(form.data);
  } catch (error) {
    return apiErrorState(error, form.values, "email");
  }
  redirect(`/employees/${employee.id}`);
}

export async function updateEmployeeAction(
  employeeId: number,
  _state: FormState,
  formData: FormData,
): Promise<FormState> {
  const form = parseForm(employeeUpdateSchema, formData);
  if (!form.success) {
    return form.state;
  }
  try {
    await updateEmployee(employeeId, form.data);
  } catch (error) {
    return apiErrorState(error, form.values, "email");
  }
  refresh();
  return { status: "success", values: form.values };
}

export async function deactivateEmployeeAction(
  employeeId: number,
): Promise<void> {
  await deactivateEmployee(employeeId);
  refresh();
}

export async function createPayrollAction(
  employeeId: number,
  _state: FormState,
  formData: FormData,
): Promise<FormState> {
  const form = parseForm(payrollCreateSchema, formData);
  if (!form.success) {
    return form.state;
  }
  let payroll: Payroll;
  try {
    payroll = await createPayroll(employeeId, form.data);
  } catch (error) {
    return apiErrorState(error, form.values);
  }
  redirect(`/payrolls/${payroll.id}`);
}
