"use server";

import { refresh } from "next/cache";

import { updatePayroll } from "@/lib/api";
import {
  apiErrorState,
  type FormState,
  parseForm,
  payrollUpdateSchema,
} from "@/lib/forms";

export async function updatePayrollAction(
  payrollId: number,
  _state: FormState,
  formData: FormData,
): Promise<FormState> {
  const form = parseForm(payrollUpdateSchema, formData);
  if (!form.success) {
    return form.state;
  }
  try {
    await updatePayroll(payrollId, form.data);
  } catch (error) {
    return apiErrorState(error, form.values);
  }
  refresh();
  return { status: "success", values: form.values };
}
