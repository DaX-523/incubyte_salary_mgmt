import type { ComponentProps, ReactNode } from "react";

import {
  Field,
  FieldDescription,
  FieldError,
  FieldLabel,
} from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { NativeSelect } from "@/components/ui/native-select";

type FieldProps = {
  label: string;
  name: string;
  error?: string;
  description?: ReactNode;
};

/** Label, hint and error wired to the control with ids, so screen readers announce them. */
function LabelledField({
  label,
  name,
  error,
  description,
  children,
}: FieldProps & { children: (describedBy: string | undefined) => ReactNode }) {
  const descriptionId = description ? `${name}-description` : undefined;
  const errorId = error ? `${name}-error` : undefined;
  const describedBy =
    [descriptionId, errorId].filter(Boolean).join(" ") || undefined;
  return (
    <Field data-invalid={error ? true : undefined}>
      <FieldLabel htmlFor={name}>{label}</FieldLabel>
      {children(describedBy)}
      {description && (
        <FieldDescription id={descriptionId}>{description}</FieldDescription>
      )}
      {error && <FieldError id={errorId}>{error}</FieldError>}
    </Field>
  );
}

export function TextField({
  label,
  name,
  error,
  description,
  ...inputProps
}: FieldProps & Omit<ComponentProps<"input">, "name" | "id">) {
  return (
    <LabelledField
      label={label}
      name={name}
      error={error}
      description={description}
    >
      {(describedBy) => (
        <Input
          id={name}
          name={name}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy}
          {...inputProps}
        />
      )}
    </LabelledField>
  );
}

export function SelectField({
  label,
  name,
  error,
  description,
  children,
  ...selectProps
}: FieldProps & Omit<ComponentProps<"select">, "name" | "id" | "size">) {
  return (
    <LabelledField
      label={label}
      name={name}
      error={error}
      description={description}
    >
      {(describedBy) => (
        <NativeSelect
          id={name}
          name={name}
          className="w-full"
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy}
          {...selectProps}
        >
          {children}
        </NativeSelect>
      )}
    </LabelledField>
  );
}
