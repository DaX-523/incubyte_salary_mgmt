import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { OPTIONS } from "@/test/fixtures";

import { CountryPicker } from "./country-picker";

describe("CountryPicker", () => {
  it("submits the chosen country to the insights page", () => {
    render(<CountryPicker countries={OPTIONS.countries} />);

    expect(
      screen.getByRole("form", { name: "Choose a country" }),
    ).toHaveAttribute("action", "/insights");
    expect(screen.getByRole("combobox", { name: "Country" })).toBeRequired();
  });

  it("lists countries by name with their currency", () => {
    render(<CountryPicker countries={OPTIONS.countries} selected="IN" />);

    const select = screen.getByRole("combobox", {
      name: "Country",
    }) as HTMLSelectElement;
    expect(
      Array.from(select.options).map((option) => option.textContent),
    ).toEqual([
      "Choose a country",
      "Germany (EUR)",
      "India (INR)",
      "United Kingdom (GBP)",
    ]);
    expect(select).toHaveValue("IN");
  });
});
