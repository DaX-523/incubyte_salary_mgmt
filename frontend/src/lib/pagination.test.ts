import { describe, expect, it } from "vitest";

import { pageRange } from "./pagination";

describe("pageRange", () => {
  it.each([
    [1, 25, 9168, { first: 1, last: 25, totalPages: 367 }],
    [2, 25, 9168, { first: 26, last: 50, totalPages: 367 }],
    [367, 25, 9168, { first: 9151, last: 9168, totalPages: 367 }],
    [1, 25, 25, { first: 1, last: 25, totalPages: 1 }],
    [1, 25, 0, { first: 0, last: 0, totalPages: 0 }],
    [5, 25, 30, { first: 0, last: 0, totalPages: 2 }],
  ])(
    "page %i of %i per page over %i items",
    (page, pageSize, total, expected) => {
      expect(pageRange(page, pageSize, total)).toEqual(expected);
    },
  );
});
