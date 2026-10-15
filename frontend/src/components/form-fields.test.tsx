import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SelectField, TextField } from "./form-fields";

describe("TextField", () => {
  it("labels the input and describes it with its hint", () => {
    render(
      <TextField
        label="Monthly salary"
        name="monthly_salary"
        description="In GBP."
      />,
    );

    const input = screen.getByRole("textbox", { name: "Monthly salary" });
    expect(input).toHaveAttribute("name", "monthly_salary");
    expect(input).toHaveAccessibleDescription("In GBP.");
    expect(input).not.toHaveAttribute("aria-invalid");
  });

  it("marks the input invalid and announces the error", () => {
    render(
      <TextField
        label="Name"
        name="name"
        description="Full name."
        error="Enter a name"
      />,
    );

    const input = screen.getByRole("textbox", { name: "Name" });
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(input).toHaveAccessibleDescription("Full name. Enter a name");
    expect(screen.getByRole("alert")).toHaveTextContent("Enter a name");
  });
});

describe("SelectField", () => {
  it("labels the select and shows its error", () => {
    render(
      <SelectField label="Country" name="country" error="Choose a country">
        <option value="">Choose</option>
      </SelectField>,
    );

    const select = screen.getByRole("combobox", { name: "Country" });
    expect(select).toHaveAttribute("aria-invalid", "true");
    expect(select).toHaveAccessibleDescription("Choose a country");
  });
});
