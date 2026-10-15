export type SearchParams = Record<string, string | string[] | undefined>;

const POSITIVE_INTEGER = /^[1-9]\d{0,15}$/;

/** The first value of a URL parameter, trimmed, or undefined when it is blank. */
export function firstParam(
  value: string | string[] | undefined,
): string | undefined {
  const text = (Array.isArray(value) ? value[0] : value)?.trim();
  return text || undefined;
}

/** `value` when it is one of `allowed`, otherwise undefined. */
export function oneOf<Value extends string>(
  value: string | undefined,
  allowed: readonly Value[],
): Value | undefined {
  return allowed.find((option) => option === value);
}

/** A positive whole number such as an id or page, or undefined. */
export function positiveInteger(value: string | undefined): number | undefined {
  return value && POSITIVE_INTEGER.test(value) ? Number(value) : undefined;
}
