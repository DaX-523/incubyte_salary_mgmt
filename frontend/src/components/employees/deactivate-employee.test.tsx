import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { DeactivateEmployee } from "./deactivate-employee";

describe("DeactivateEmployee", () => {
  it("asks for confirmation before deactivating", async () => {
    const user = userEvent.setup();
    const action = vi.fn(async () => {});
    render(<DeactivateEmployee name="Ada Lovelace" action={action} />);

    await user.click(
      screen.getByRole("button", { name: "Deactivate employee" }),
    );

    expect(screen.getByText(/Deactivate Ada Lovelace\?/)).toHaveTextContent(
      "their payroll history is kept",
    );
    expect(action).not.toHaveBeenCalled();
  });

  it("deactivates once confirmed", async () => {
    const user = userEvent.setup();
    const action = vi.fn(async () => {});
    render(<DeactivateEmployee name="Ada Lovelace" action={action} />);

    await user.click(
      screen.getByRole("button", { name: "Deactivate employee" }),
    );
    await user.click(screen.getByRole("button", { name: "Yes, deactivate" }));

    expect(action).toHaveBeenCalledOnce();
  });

  it("can be cancelled", async () => {
    const user = userEvent.setup();
    const action = vi.fn(async () => {});
    render(<DeactivateEmployee name="Ada Lovelace" action={action} />);

    await user.click(
      screen.getByRole("button", { name: "Deactivate employee" }),
    );
    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(
      screen.getByRole("button", { name: "Deactivate employee" }),
    ).toBeInTheDocument();
    expect(action).not.toHaveBeenCalled();
  });
});
