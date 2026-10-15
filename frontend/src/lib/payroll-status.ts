import type { PayrollStatus } from "@/lib/api";

/** Whole-number share of employees paid, or null when nobody is on the books. */
export function paidPercentage(status: PayrollStatus): number | null {
  return status.total > 0
    ? Math.round((status.paid / status.total) * 100)
    : null;
}
