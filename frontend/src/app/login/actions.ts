"use server";

import { redirect } from "next/navigation";

import { type LoginToken, login, logout } from "@/lib/api";
import {
  apiErrorState,
  type FormState,
  loginSchema,
  parseForm,
} from "@/lib/forms";
import { endSession, startSession } from "@/lib/session";

export async function loginAction(
  _state: FormState,
  formData: FormData,
): Promise<FormState> {
  // Sent back to refill the form. The password never leaves the server.
  const values = { email: String(formData.get("email") ?? "") };
  const form = parseForm(loginSchema, formData);
  if (!form.success) {
    return { ...form.state, values };
  }
  let token: LoginToken;
  try {
    token = await login(form.data.email, form.data.password);
  } catch (error) {
    return apiErrorState(error, values);
  }
  await startSession(token.access_token, new Date(token.expires_at));
  redirect("/");
}

export async function logoutAction(): Promise<void> {
  await logout();
  await endSession();
  redirect("/login");
}
