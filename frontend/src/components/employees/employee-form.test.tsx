import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { FormState } from "@/lib/forms";
import { ADA, OPTIONS } from "@/test/fixtures";

import { EmployeeForm } from "./employee-form";

async function fillInNewEmployee(user: ReturnType<typeof userEvent.setup>) {
  await user.type(
    screen.getByRole("textbox", { name: "Name" }),
    "Grace Hopper",
  );
  await user.type(
    screen.getByRole("textbox", { name: "Email" }),
    "grace@example.com",
  );
  await user.selectOptions(
    screen.getByRole("combobox", { name: /Country/ }),
    "DE",
  );
  await user.selectOptions(
    screen.getByRole("combobox", { name: /Job title/ }),
    "Accountant",
  );
  await user.type(
    screen.getByRole("textbox", { name: "Monthly salary" }),
    "5200.50",
  );
}

function actionReturning(state: FormState) {
  return vi.fn<(state: FormState, formData: FormData) => Promise<FormState>>(
    async () => state,
  );
}

describe("EmployeeForm when adding an employee", () => {
  it("sends every field to the action", async () => {
    const user = userEvent.setup();
    const action = actionReturning({ status: "idle" });
    render(
      <EmployeeForm
        action={action}
        options={OPTIONS}
        submitLabel="Add employee"
      />,
    );

    await user.type(
      screen.getByRole("textbox", { name: "Name" }),
      "Grace Hopper",
    );
    await user.type(
      screen.getByRole("textbox", { name: "Email" }),
      "grace@example.com",
    );
    await user.selectOptions(
      screen.getByRole("combobox", { name: "Country" }),
      "DE",
    );
    await user.selectOptions(
      screen.getByRole("combobox", { name: "Job title" }),
      "Accountant",
    );
    await user.type(
      screen.getByRole("textbox", { name: "Monthly salary" }),
      "5200.50",
    );
    await user.click(screen.getByRole("button", { name: "Add employee" }));

    const formData = action.mock.calls[0][1];
    expect(Object.fromEntries(formData)).toEqual({
      name: "Grace Hopper",
      email: "grace@example.com",
      country: "DE",
      job_title: "Accountant",
      monthly_salary: "5200.50",
    });
  });

  it("lets the browser block submitting without the required fields", async () => {
    const user = userEvent.setup();
    const action = actionReturning({ status: "idle" });
    render(
      <EmployeeForm
        action={action}
        options={OPTIONS}
        submitLabel="Add employee"
      />,
    );

    await user.click(screen.getByRole("button", { name: "Add employee" }));

    expect(action).not.toHaveBeenCalled();
    expect(screen.getByRole("textbox", { name: "Name" })).toBeInvalid();
  });

  it("offers countries with their currency and job titles with their department", () => {
    render(
      <EmployeeForm
        action={actionReturning({ status: "idle" })}
        options={OPTIONS}
        submitLabel="Add"
      />,
    );

    expect(
      screen.getByRole("option", { name: "Germany (EUR)" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("option", { name: "Accountant (Finance)" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("combobox", { name: "Country" }),
    ).toHaveAccessibleDescription(
      "Decides the salary currency, and can't be changed later.",
    );
  });

  it("shows field errors and keeps what was typed", async () => {
    const user = userEvent.setup();
    const action = actionReturning({
      status: "error",
      fieldErrors: {
        email: "An employee with email grace@example.com already exists",
      },
      values: {
        name: "Grace Hopper",
        email: "grace@example.com",
        monthly_salary: "5200",
      },
    });
    render(
      <EmployeeForm
        action={action}
        options={OPTIONS}
        submitLabel="Add employee"
      />,
    );

    await fillInNewEmployee(user);
    await user.click(screen.getByRole("button", { name: "Add employee" }));

    const email = await screen.findByRole("textbox", { name: "Email" });
    expect(email).toHaveAttribute("aria-invalid", "true");
    expect(email).toHaveAccessibleDescription(
      "An employee with email grace@example.com already exists",
    );
    expect(screen.getByRole("textbox", { name: "Name" })).toHaveValue(
      "Grace Hopper",
    );
  });

  it("shows a problem with the whole form", async () => {
    const user = userEvent.setup();
    const action = actionReturning({
      status: "error",
      message: "Could not reach the API",
    });
    render(
      <EmployeeForm
        action={action}
        options={OPTIONS}
        submitLabel="Add employee"
      />,
    );

    await fillInNewEmployee(user);
    await user.click(screen.getByRole("button", { name: "Add employee" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Could not reach the API",
    );
  });

  it("disables the button while saving, then enables it again", async () => {
    const user = userEvent.setup();
    let finishSaving: (state: FormState) => void = () => {};
    const action = vi.fn(
      () => new Promise<FormState>((resolve) => (finishSaving = resolve)),
    );
    render(
      <EmployeeForm
        action={action}
        options={OPTIONS}
        submitLabel="Add employee"
      />,
    );

    await fillInNewEmployee(user);
    await user.click(screen.getByRole("button", { name: "Add employee" }));
    const savingButton = await screen.findByRole("button", { name: "Saving…" });
    expect(savingButton).toBeDisabled();

    finishSaving({ status: "idle" });

    expect(
      await screen.findByRole("button", { name: "Add employee" }),
    ).toBeEnabled();
  });
});

describe("EmployeeForm when editing an employee", () => {
  it("starts from the employee's details", () => {
    render(
      <EmployeeForm
        action={actionReturning({ status: "idle" })}
        options={OPTIONS}
        employee={ADA}
        submitLabel="Save changes"
      />,
    );

    expect(screen.getByRole("textbox", { name: "Name" })).toHaveValue(
      "Ada Lovelace",
    );
    expect(screen.getByRole("textbox", { name: "Monthly salary" })).toHaveValue(
      "4780.00",
    );
    expect(
      screen.getByRole("textbox", { name: "Monthly salary" }),
    ).toHaveAccessibleDescription("In GBP.");
    expect(screen.getByRole("combobox", { name: /Job title/ })).toHaveValue(
      "Software Engineer",
    );
  });

  it("shows the country without letting it change", () => {
    render(
      <EmployeeForm
        action={actionReturning({ status: "idle" })}
        options={OPTIONS}
        employee={ADA}
        submitLabel="Save changes"
      />,
    );

    expect(
      screen.queryByRole("combobox", { name: "Country" }),
    ).not.toBeInTheDocument();
    expect(screen.getByText(/United Kingdom/)).toHaveTextContent(
      "Country: United Kingdom (GBP)",
    );
  });

  it("confirms saved changes", async () => {
    const user = userEvent.setup();
    const action = actionReturning({ status: "success" });
    render(
      <EmployeeForm
        action={action}
        options={OPTIONS}
        employee={ADA}
        submitLabel="Save changes"
      />,
    );

    await user.click(screen.getByRole("button", { name: "Save changes" }));

    expect(await screen.findByRole("status")).toHaveTextContent(
      "Changes saved.",
    );
  });
});
