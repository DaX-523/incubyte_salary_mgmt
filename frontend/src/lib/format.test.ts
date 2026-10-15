import { describe, expect, it } from "vitest";

import {
  countryName,
  formatCount,
  formatMoney,
  formatMonth,
  paymentMethodLabel,
} from "./format";

describe("formatMoney", () => {
  it.each([
    ["4780.00", "GBP", "£4,780.00"],
    ["15730.50", "EUR", "€15,730.50"],
    ["0.00", "USD", "$0.00"],
    ["400000.00", "JPY", "¥400,000"],
    ["999999999999.99", "INR", "₹999,999,999,999.99"],
  ])("formats %s %s as %s", (amount, currency, expected) => {
    expect(formatMoney(amount, currency)).toBe(expected);
  });
});

describe("formatCount", () => {
  it("groups thousands", () => {
    expect(formatCount(9168)).toBe("9,168");
  });
});

describe("countryName", () => {
  it.each([
    ["DE", "Germany"],
    ["GB", "United Kingdom"],
    ["IN", "India"],
    ["XX", "XX"],
  ])("names %s as %s", (code, expected) => {
    expect(countryName(code)).toBe(expected);
  });
});

describe("formatMonth", () => {
  it.each([
    ["2026-10", "October 2026"],
    ["2026-01", "January 2026"],
    ["2025-12", "December 2025"],
  ])("labels %s as %s", (month, expected) => {
    expect(formatMonth(month)).toBe(expected);
  });
});

describe("paymentMethodLabel", () => {
  it.each([
    ["bank_transfer", "Bank transfer"],
    ["digital_wallet", "Digital wallet"],
    ["crypto", "crypto"],
  ])("labels %s as %s", (method, expected) => {
    expect(paymentMethodLabel(method)).toBe(expected);
  });
});
