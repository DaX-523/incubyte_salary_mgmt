import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { FormState } from "@/lib/forms";
import { ADA_OCTOBER_PAYROLL } from "@/test/fixtures";

import { PayrollForm } from "./payroll-form";

const NEW_PAYROLL = {
  month: "2026-10",
  base: "4780.00",
  bonus: "0",
  esops: "0",
  payment_method: "bank_transfer" as const,
};

function actionReturning(state: FormState) {
  return vi.fn<(state: FormState, formData: FormData) => Promise<FormState>>(
    async () => state,
  );
}

function renderForm(
  action = actionReturning({ status: "idle" }),
  withMonth = true,
) {
  render(
    <PayrollForm
      action={action}
      currency="GBP"
      paymentMethods={["bank_transfer", "digital_wallet"]}
      defaults={withMonth ? NEW_PAYROLL : ADA_OCTOBER_PAYROLL}
      submitLabel="Record payroll"
      withMonth={withMonth}
    />,
  );
  return action;
}

describe("PayrollForm", () => {
  it("prefills the month and amounts, in the employee's currency", () => {
    renderForm();

    expect(screen.getByLabelText("Month")).toHaveValue("2026-10");
    expect(screen.getByRole("textbox", { name: "Base pay" })).toHaveValue(
      "4780.00",
    );
    expect(
      screen.getByRole("textbox", { name: "Bonus" }),
    ).toHaveAccessibleDescription("In GBP.");
    expect(
      screen.getByRole("combobox", { name: "Payment method" }),
    ).toHaveValue("bank_transfer");
  });

  it("sends the payroll to the action", async () => {
    const user = userEvent.setup();
    const action = renderForm();

    await user.clear(screen.getByRole("textbox", { name: "Bonus" }));
    await user.type(screen.getByRole("textbox", { name: "Bonus" }), "250.50");
    await user.selectOptions(
      screen.getByRole("combobox", { name: "Payment method" }),
      "Digital wallet",
    );
    await user.click(screen.getByRole("button", { name: "Record payroll" }));

    expect(Object.fromEntries(action.mock.calls[0][1])).toEqual({
      month: "2026-10",
      base: "4780.00",
      bonus: "250.50",
      esops: "0",
      payment_method: "digital_wallet",
    });
  });

  it("leaves the month out when correcting an existing payroll", () => {
    renderForm(actionReturning({ status: "idle" }), false);

    expect(screen.queryByLabelText("Month")).not.toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Bonus" })).toHaveValue(
      "239.00",
    );
  });

  it("shows a conflict such as an existing payroll for the month", async () => {
    const user = userEvent.setup();
    renderForm(
      actionReturning({
        status: "error",
        message: "Employee 1 already has a payroll for 2026-10",
        values: { ...NEW_PAYROLL, bonus: "99" },
      }),
    );

    await user.click(screen.getByRole("button", { name: "Record payroll" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Employee 1 already has a payroll for 2026-10",
    );
    expect(screen.getByRole("textbox", { name: "Bonus" })).toHaveValue("99");
  });

  it("marks invalid amounts", async () => {
    const user = userEvent.setup();
    renderForm(
      actionReturning({
        status: "error",
        fieldErrors: {
          base: "Base pay must be an amount like 5000 or 5000.50",
        },
      }),
    );

    await user.click(screen.getByRole("button", { name: "Record payroll" }));

    expect(
      await screen.findByRole("textbox", { name: "Base pay" }),
    ).toHaveAccessibleDescription(
      "In GBP. Base pay must be an amount like 5000 or 5000.50",
    );
  });
});
