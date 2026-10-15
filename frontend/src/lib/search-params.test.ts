import { describe, expect, it } from "vitest";

import { firstParam, oneOf, positiveInteger } from "./search-params";

describe("firstParam", () => {
  it.each<[string | string[] | undefined, string | undefined]>([
    ["GB", "GB"],
    [" ada ", "ada"],
    [["GB", "DE"], "GB"],
    ["   ", undefined],
    ["", undefined],
    [[], undefined],
    [undefined, undefined],
  ])("reads %j as %j", (value, expected) => {
    expect(firstParam(value)).toBe(expected);
  });
});

describe("oneOf", () => {
  it("accepts an allowed value and rejects anything else", () => {
    expect(oneOf("asc", ["asc", "desc"])).toBe("asc");
    expect(oneOf("ASC", ["asc", "desc"])).toBeUndefined();
    expect(oneOf(undefined, ["asc", "desc"])).toBeUndefined();
  });
});

describe("positiveInteger", () => {
  it.each<[string | undefined, number | undefined]>([
    ["1", 1],
    ["42", 42],
    ["9007199254740991", 9007199254740991],
    ["0", undefined],
    ["-3", undefined],
    ["007", undefined],
    ["1.5", undefined],
    ["12abc", undefined],
    ["12345678901234567", undefined],
    [undefined, undefined],
  ])("reads %j as %j", (value, expected) => {
    expect(positiveInteger(value)).toBe(expected);
  });
});
