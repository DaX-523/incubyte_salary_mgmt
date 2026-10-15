// Display formatting. The locale is fixed so the UI (and its tests) look the same everywhere.
const LOCALE = "en-US";

const countryNames = new Intl.DisplayNames([LOCALE], {
  type: "region",
  fallback: "none",
});
const monthLabels = new Intl.DateTimeFormat(LOCALE, {
  month: "long",
  year: "numeric",
  timeZone: "UTC",
});
const counts = new Intl.NumberFormat(LOCALE);

const PAYMENT_METHOD_LABELS: Record<string, string> = {
  bank_transfer: "Bank transfer",
  digital_wallet: "Digital wallet",
};

/** "4780.00" + "GBP" → "£4,780.00". The amount stays a decimal string: no float rounding. */
export function formatMoney(amount: string, currency: string): string {
  return new Intl.NumberFormat(LOCALE, { style: "currency", currency }).format(
    amount as Intl.StringNumericLiteral,
  );
}

export function formatCount(value: number): string {
  return counts.format(value);
}

/** "DE" → "Germany"; unknown codes come back unchanged. */
export function countryName(code: string): string {
  return countryNames.of(code) ?? code;
}

/** "2026-10" → "October 2026". */
export function formatMonth(month: string): string {
  const [year, monthNumber] = month.split("-").map(Number);
  return monthLabels.format(Date.UTC(year, monthNumber - 1, 1));
}

export function paymentMethodLabel(method: string): string {
  return PAYMENT_METHOD_LABELS[method] ?? method;
}
