import { describe, expect, it } from "vitest";

import { paidPercentage } from "./payroll-status";

describe("paidPercentage", () => {
  it.each([
    [7815, 9168, 85],
    [1, 3, 33],
    [2, 3, 67],
    [0, 10, 0],
    [10, 10, 100],
  ])("is the rounded share for %i paid of %i", (paid, total, expected) => {
    expect(
      paidPercentage({ month: "2026-10", paid, total, unpaid: total - paid }),
    ).toBe(expected);
  });

  it("is null when nobody is on the books", () => {
    expect(
      paidPercentage({ month: "2026-10", paid: 0, total: 0, unpaid: 0 }),
    ).toBeNull();
  });
});
