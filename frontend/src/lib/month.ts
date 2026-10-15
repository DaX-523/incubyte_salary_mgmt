export const MONTH_PATTERN = /^\d{4}-(0[1-9]|1[0-2])$/;

/** The calendar month of `now` in UTC, as "YYYY-MM". */
export function currentMonth(now: Date): string {
  return `${now.getUTCFullYear()}-${String(now.getUTCMonth() + 1).padStart(2, "0")}`;
}
