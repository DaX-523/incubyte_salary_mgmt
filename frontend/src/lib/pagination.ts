export type PageRange = { first: number; last: number; totalPages: number };

/** Which items (1-based) a page shows, e.g. page 2 of 25 per page shows items 26–50. */
export function pageRange(
  page: number,
  pageSize: number,
  total: number,
): PageRange {
  const totalPages = Math.ceil(total / pageSize);
  const first = (page - 1) * pageSize + 1;
  if (first > total) {
    return { first: 0, last: 0, totalPages };
  }
  return { first, last: Math.min(page * pageSize, total), totalPages };
}
