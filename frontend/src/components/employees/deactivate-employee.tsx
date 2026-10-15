"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";

type Props = { name: string; action: () => Promise<void> };

/** Deactivating takes a second, deliberate click. Payroll history is always kept. */
export function DeactivateEmployee({ name, action }: Props) {
  const [confirming, setConfirming] = useState(false);
  if (!confirming) {
    return (
      <Button variant="destructive" onClick={() => setConfirming(true)}>
        Deactivate employee
      </Button>
    );
  }
  return (
    <form action={action} className="grid gap-3">
      <p className="text-sm">
        Deactivate {name}? They will no longer be paid, but their payroll
        history is kept.
      </p>
      <div className="flex gap-2">
        <Button type="submit" variant="destructive">
          Yes, deactivate
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={() => setConfirming(false)}
        >
          Cancel
        </Button>
      </div>
    </form>
  );
}
