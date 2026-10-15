"use client";

import { useActionState } from "react";

import { SelectField, TextField } from "@/components/form-fields";
import { FormStatus } from "@/components/form-status";
import { Button } from "@/components/ui/button";
import { FieldGroup } from "@/components/ui/field";
import { NativeSelectOption } from "@/components/ui/native-select";
import type { PaymentMethod } from "@/lib/api";
import { paymentMethodLabel } from "@/lib/format";
import { type FormState, INITIAL_FORM_STATE } from "@/lib/forms";

type PayrollValues = {
  month?: string;
  base: string;
  bonus: string;
  esops: string;
  payment_method: PaymentMethod;
};

type Props = {
  action: (state: FormState, formData: FormData) => Promise<FormState>;
  currency: string;
  paymentMethods: PaymentMethod[];
  defaults: PayrollValues;
  submitLabel: string;
  /** The month can only be chosen when recording a payroll, not when correcting one. */
  withMonth: boolean;
};

export function PayrollForm({
  action,
  currency,
  paymentMethods,
  defaults,
  submitLabel,
  withMonth,
}: Props) {
  const [state, formAction, pending] = useActionState(
    action,
    INITIAL_FORM_STATE,
  );
  const errors = state.fieldErrors ?? {};
  const value = (field: keyof PayrollValues) =>
    state.values?.[field] ?? defaults[field];
  const amountHint = `In ${currency}.`;
  return (
    <form action={formAction} className="max-w-xl">
      <FieldGroup>
        {withMonth && (
          <TextField
            label="Month"
            name="month"
            type="month"
            required
            defaultValue={value("month")}
            error={errors.month}
          />
        )}
        <TextField
          label="Base pay"
          name="base"
          inputMode="decimal"
          required
          defaultValue={value("base")}
          error={errors.base}
          description={amountHint}
        />
        <TextField
          label="Bonus"
          name="bonus"
          inputMode="decimal"
          required
          defaultValue={value("bonus")}
          error={errors.bonus}
          description={amountHint}
        />
        <TextField
          label="ESOPs"
          name="esops"
          inputMode="decimal"
          required
          defaultValue={value("esops")}
          error={errors.esops}
          description={amountHint}
        />
        <SelectField
          label="Payment method"
          name="payment_method"
          required
          defaultValue={value("payment_method")}
          error={errors.payment_method}
        >
          {paymentMethods.map((method) => (
            <NativeSelectOption key={method} value={method}>
              {paymentMethodLabel(method)}
            </NativeSelectOption>
          ))}
        </SelectField>
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
