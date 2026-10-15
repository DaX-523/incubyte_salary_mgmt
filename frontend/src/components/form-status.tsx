import { Alert, AlertDescription } from "@/components/ui/alert";
import type { FormState } from "@/lib/forms";

/** The outcome of the last submission: a confirmation, or a problem with the whole form. */
export function FormStatus({
  state,
  successMessage,
}: {
  state: FormState;
  successMessage: string;
}) {
  if (state.status === "success") {
    return (
      <p role="status" className="text-sm text-muted-foreground">
        {successMessage}
      </p>
    );
  }
  if (state.message) {
    return (
      <Alert variant="destructive">
        <AlertDescription>{state.message}</AlertDescription>
      </Alert>
    );
  }
  return null;
}
