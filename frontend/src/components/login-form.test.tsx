import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { FormState } from "@/lib/forms";

import { LoginForm } from "./login-form";

function actionReturning(state: FormState) {
  return vi.fn<(state: FormState, formData: FormData) => Promise<FormState>>(
    async () => state,
  );
}

describe("LoginForm", () => {
  it("sends the email and password to the action", async () => {
    const user = userEvent.setup();
    const action = actionReturning({ status: "idle" });
    render(<LoginForm action={action} />);

    await user.type(
      screen.getByRole("textbox", { name: "Email" }),
      "hr@acme.example",
    );
    await user.type(screen.getByLabelText("Password"), "secret");
    await user.click(screen.getByRole("button", { name: "Log in" }));

    const [, submitted] = action.mock.calls[0];
    expect(submitted.get("email")).toBe("hr@acme.example");
    expect(submitted.get("password")).toBe("secret");
  });

  it("hides the password and lets password managers fill both fields", () => {
    render(<LoginForm action={actionReturning({ status: "idle" })} />);

    expect(screen.getByLabelText("Password")).toHaveAttribute(
      "type",
      "password",
    );
    expect(screen.getByLabelText("Password")).toHaveAttribute(
      "autocomplete",
      "current-password",
    );
    expect(screen.getByRole("textbox", { name: "Email" })).toHaveAttribute(
      "autocomplete",
      "username",
    );
  });

  it("shows why logging in failed and keeps the email", async () => {
    const user = userEvent.setup();
    const action = actionReturning({
      status: "error",
      message: "Email or password is incorrect",
      values: { email: "hr@acme.example" },
    });
    render(<LoginForm action={action} />);

    await user.type(
      screen.getByRole("textbox", { name: "Email" }),
      "hr@acme.example",
    );
    await user.type(screen.getByLabelText("Password"), "wrong");
    await user.click(screen.getByRole("button", { name: "Log in" }));

    expect(
      await screen.findByText("Email or password is incorrect"),
    ).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Email" })).toHaveValue(
      "hr@acme.example",
    );
    expect(screen.getByLabelText("Password")).toHaveValue("");
  });
});
