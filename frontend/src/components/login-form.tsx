"use client";

import { useActionState } from "react";

import { TextField } from "@/components/form-fields";
import { FormStatus } from "@/components/form-status";
import { Button } from "@/components/ui/button";
import { FieldGroup } from "@/components/ui/field";
import { type FormState, INITIAL_FORM_STATE } from "@/lib/forms";

type Props = {
  action: (state: FormState, formData: FormData) => Promise<FormState>;
};

export function LoginForm({ action }: Props) {
  const [state, formAction, pending] = useActionState(
    action,
    INITIAL_FORM_STATE,
  );
  const errors = state.fieldErrors ?? {};
  return (
    <form action={formAction}>
      <FieldGroup>
        <TextField
          label="Email"
          name="email"
          type="email"
          autoComplete="username"
          required
          defaultValue={state.values?.email}
          error={errors.email}
        />
        <TextField
          label="Password"
          name="password"
          type="password"
          autoComplete="current-password"
          required
          error={errors.password}
        />
        <FormStatus state={state} successMessage="Logged in." />
        <Button type="submit" disabled={pending}>
          {pending ? "Logging in…" : "Log in"}
        </Button>
      </FieldGroup>
    </form>
  );
}
