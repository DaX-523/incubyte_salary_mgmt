import { describe, expect, it } from "vitest";

import { currentMonth } from "./month";

describe("currentMonth", () => {
  it.each([
    ["2026-10-15T12:00:00Z", "2026-10"],
    ["2026-01-01T00:00:00Z", "2026-01"],
    ["2026-12-31T23:59:59Z", "2026-12"],
    // Already November in UTC, whatever the server's local time zone says.
    ["2026-10-31T23:30:00-02:00", "2026-11"],
  ])("is %s's UTC month: %s", (instant, expected) => {
    expect(currentMonth(new Date(instant))).toBe(expected);
  });
});
